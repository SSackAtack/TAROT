import cv2
import numpy as np
import glob
import os
import asyncio
import threading
import json
import copy
import websockets
import math
import time
import logging

from tarotvision.metrics import RuntimeMetrics
from tarotvision.matching_schedule import choose_cards_to_match, get_schedule_mode
from tarotvision.motion import MotionDetector
from tarotvision.audit_policy import should_reverify
from tarotvision.table_state import TableState, PHASE_LOCKED, PHASE_NEEDS_REVERIFY
from tarotvision.roi_map import filter_boxes_outside_occupied
from tarotvision.contour_tracking import assign_boxes_to_cards
from tarotvision.runtime_config import RuntimeConfigSession, ParameterValidationError
from tarotvision.tuning_protocol import parse_control_message, ControlMessageError
from tarotvision.profile_store import ProfileStore
from tarotvision.camera_controls import read_camera_control
from tarotvision.calibration_session import choose_best_candidate
from tarotvision.table_calibration import TableCalibration
from tarotvision.card_detection import find_card_quads
from tarotvision.card_recognition import recognize_card_crop
from tarotvision.snapshot_gate import SnapshotGate, SnapshotGateConfig
from tarotvision.snapshot_quality import choose_best_snapshot
from tarotvision.snapshot_analyzer import SnapshotAnalyzer
from tarotvision.camera import CameraSession
from tarotvision.preview import OpenCvPreview
from tarotvision.pipelines import SnapshotFirstPipeline, StateFirstLegacyPipeline

# Konfiguracja
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.environ.get("TAROTVISION_LOG_DIR", os.path.join(PROJECT_ROOT, "logs"))
CV_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", "rider-waite-smith", "produkcja", "wzorce_cv"))
MIN_MATCH_COUNT = 18   # Obnizony do 18 — filtry geometryczne (homografia + validate_quad + aspect ratio + inlier ratio) skutecznie eliminuja szum
RATIO_THRESH = 0.75    # Zaostrzone z 0.79 do 0.75 dla wyeliminowania dopasowan krzyzowych i poprawy homografii podobnych kart (np. Star i Moon)
MIN_INLIER_RATIO = 0.3 # Minimalna proporcja inlierow w homografii RANSAC (odrzuca niestabilne dopasowania)
CARD_ASPECT_RATIO = 1.72  # Standardowy stosunek wysokosc/szerokosc kart tarota RWS (~1.72)
CARD_ASPECT_TOLERANCE = 0.65  # Tolerancja odchylenia aspect ratio (poluzowana — perspektywa kamery silnie znieksztalca proporcje)
EMA_ALPHA = 0.4        # Wspolczynnik wygladzania Exponential Moving Average dla pozycji (0 = pelne wygladzanie, 1 = brak)
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
DETECTION_IOU_THRESHOLD = 0.35  # Maksymalne dopuszczalne nalozenie dwoch kandydatow kart
RUNTIME_PROFILE = "cpu_baseline"
CAMERA_FOCUS_LOCKED = True      # Ustawienie operatorskie: AnkerWork C310 ma pracowac z blokada AF
CAMERA_EXPOSURE_LOCKED = True   # Ustawienie operatorskie: blokada ekspozycji zmniejsza flicker i false positives
LOCKED_REFRESH_INTERVAL = 10    # Karty LOCKED sprawdzamy okresowo, nie w kazdej klatce
INACTIVE_PER_FRAME_EMPTY = 4     # Gdy nie ma aktywnych kart, szybciej skanujemy talie
INACTIVE_PER_FRAME_ACTIVE = 2    # Gdy sa aktywne karty, skanujemy 2 nieaktywne/klatke (ArUco cache daje budzet)
INACTIVE_PER_FRAME_BOOST = 3     # Po zmianie ukladu chwilowo skanujemy szybciej, ale bez powrotu do pelnego kosztu
BOOST_AFTER_LAYOUT_CHANGE_FRAMES = 12
REVERIFY_INTERVAL_FRAMES = 180
TRACKING_IOU_THRESHOLD = 0.35
TRACKING_REVERIFY_GAP_FRAMES = 24
USE_TABLE_CARD_DETECTION = False  # Feature flag: True = uruchom detekcje prostokatow kart (Task 3 roadmapy CV)
USE_SNAPSHOT_FIRST_CV = os.environ.get("TAROTVISION_SNAPSHOT_FIRST", "0") == "1"
SNAPSHOT_SETTLE_SECONDS = 0.5
SNAPSHOT_SAMPLE_COUNT = 1
SNAPSHOT_SAMPLE_INTERVAL_MS = 250

# System dwufazowy "Zlap i Zamroz" — eliminuje mikro-jitter statycznych kart
LOCK_AFTER_FRAMES = 8      # Klatki stabilnej detekcji zanim pozycja zostanie zamrozona
LOCK_DEAD_ZONE_POS = 3.0   # Minimalny ruch pozycji (w jednostkach sceny) zeby odblokowac karte (zwiekszony pod katem szumow centroidu)
LOCK_DEAD_ZONE_ANGLE = 0.5 # Minimalny ruch kata (w radianach, ~28 stopni) zeby odblokowac karte

from tarotvision.status import StatusStore, DiagnosticsWriter

# Stan wspoldzielony i zapis diagnostyczny zarządzany przez wydzielone moduly
status_store = StatusStore()
status_lock = status_store.lock

# Zestaw polaczonych klientow
connected_clients = set()
control_messages = []
config_session = RuntimeConfigSession()
runtime_config = config_session.config
operator_warnings = []
calibration_state = {"state": "idle", "last_score": None}
profile_store = ProfileStore(os.path.join(LOG_DIR, "calibration_profiles"))
active_tuning_profile = "default"

# Inicjalizacja DiagnosticsWriter, CameraSession i OpenCvPreview
reset_logs = os.environ.get("TAROTVISION_RESET_LOGS") == "1"
diagnostics_writer = DiagnosticsWriter(LOG_DIR, filename="cv_metrics.jsonl", reset_on_start=reset_logs)
camera_session = CameraSession(LOG_DIR, camera_width=1280, camera_height=720)
opencv_preview = OpenCvPreview("TarotVision - AI Detection (Wcisnij Q by wyjsc)")


logging.basicConfig(
    filename=os.path.join(LOG_DIR, "cv_runtime.log"),
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

def log_event(message):
    logging.info(message)
    print(message)


def build_operator_snapshot():
    return {
        "enabled": True,
        "active_profile": active_tuning_profile,
        "parameters": copy.deepcopy(runtime_config.values),
        "parameter_metadata": runtime_config.metadata(),
        "pending_changes": copy.deepcopy(config_session.pending_changes),
        "supported_camera_controls": copy.deepcopy(camera_session.supported_camera_controls),
        "calibration": copy.deepcopy(calibration_state),
        "warnings": list(operator_warnings[-8:]),
    }


def add_operator_warning(message):
    operator_warnings.append(message)
    log_event(f"[OPERATOR] {message}")


def handle_control_message(message, camera_session):
    global calibration_state
    global active_tuning_profile

    if message.type == "tuning_update":
        try:
            live_safe = config_session.update(message.param, message.value)
        except ParameterValidationError as exc:
            add_operator_warning(str(exc))
            return

        if live_safe:
            log_event(f"[OPERATOR] Zastosowano {message.param}={runtime_config.values[message.param]}")
        else:
            add_operator_warning(f"{message.param} wymaga kroku kalibracji/apply")
        return

    if message.type == "tuning_rollback":
        config_session.rollback()
        add_operator_warning("Przywrocono ostatni stabilny snapshot parametrów")
        return

    if message.type == "profile_save":
        profile_store.save(message.name, runtime_config.values)
        active_tuning_profile = message.name
        add_operator_warning(f"Zapisano profil {message.name}")
        return

    if message.type == "profile_apply":
        values = profile_store.load(message.name)
        for param_name, value in values.items():
            runtime_config.update(param_name, value)
        config_session.commit_stable()
        active_tuning_profile = message.name
        add_operator_warning(f"Wczytano profil {message.name}")
        return

    if message.type == "camera_probe":
        camera_session.probe_controls()
        add_operator_warning("Odczytano parametry kamery bez zmiany focus/exposure")
        return

    if message.type == "camera_set":
        if camera_session.set_control(message.param, message.value):
            add_operator_warning(f"Ustawiono {message.param} = {message.value}")
        else:
            add_operator_warning(f"Nieznany lub nieobsługiwany parametr kamery: {message.param}")
        return

    if message.type == "calibration_start":
        candidates = [
            {"name": "current", "score": 0.0},
            {"name": "stable_tracking_bias", "score": 1.0},
        ]
        best = choose_best_candidate(candidates)
        calibration_state = {
            "state": "recommendation_ready",
            "last_score": best["score"] if best else None,
            "recommended_profile": best["name"] if best else None,
            "score_before": 0.0,
            "score_after": best["score"] if best else None,
        }
        add_operator_warning("Przygotowano wstepna rekomendacje profilu bez auto-apply")
        return

    if message.type == "calibration_cancel":
        calibration_state = {"state": "idle", "last_score": None}
        add_operator_warning("Anulowano kalibracje")


def drain_control_messages(camera_session):
    with status_lock:
        queued_messages = list(control_messages)
        control_messages.clear()
    for message in queued_messages:
        try:
            handle_control_message(message, camera_session)
        except Exception as exc:
            add_operator_warning(f"Blad obslugi {message.type}: {exc}")


def append_diagnostics(metrics_snapshot, runtime_snapshot, active_cards):
    diagnostics_writer.append(metrics_snapshot, runtime_snapshot, active_cards)

async def handler(websocket):
    log_event(f"[WEBSOCKET] Polaczono klienta: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        # Wyslij natychmiast obecny stan (bezpieczna gleboka kopia)
        state = status_store.get_status()
        await websocket.send(json.dumps(state))
        
        async for message in websocket:
            try:
                control_message = parse_control_message(message)
            except ControlMessageError as exc:
                log_event(f"[WEBSOCKET] Odrzucono control message: {exc}")
                continue
            with status_lock:
                control_messages.append(control_message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        log_event(f"[WEBSOCKET] Rozlaczono klienta: {websocket.remote_address}")

async def broadcast_status():
    last_sent_json = None
    while True:
        if connected_clients:
            # Bezpieczna gleboka kopia pod lockiem — eliminuje race condition z shallow copy
            state_to_send = status_store.get_status()
            
            # Serializujemy do JSON raz i porownujemy stringi (unika problemow z float comparison)
            current_json = json.dumps(state_to_send)
            if current_json != last_sent_json:
                websockets_tasks = [client.send(current_json) for client in connected_clients]
                if websockets_tasks:
                    await asyncio.gather(*websockets_tasks, return_exceptions=True)
                last_sent_json = current_json
        await asyncio.sleep(0.05) # Odpytywanie co 50ms (20 FPS)

async def main_ws():
    async with websockets.serve(handler, "localhost", 8765):
        log_event("[WEBSOCKET] Serwer WebSocket dziala pod adresem ws://localhost:8765")
        await broadcast_status()

def start_websocket_server():
    asyncio.run(main_ws())

# Uruchomienie serwera WebSocket w tle
ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
ws_thread.start()



log_event("========================================")
log_event("[TAROT VISION] Computer Vision Module v2.0 (Audited)")
log_event("========================================")
log_event(f"[LOG] Katalog logow: {LOG_DIR}")

# 1. Inicjalizacja detektora ORB (szybki i darmowy detektor cech)
# 2000 features przy 720p — zoptymalizowane pod kątem wydajności (3x szybsze dopasowanie!)
orb = cv2.ORB_create(nfeatures=2000)

# FLANN-LSH Matcher — 2-5x szybszy niz BruteForce dla binarnych deskryptorow ORB
# Uzywa Locality Sensitive Hashing zamiast pelnego porownania N*M
FLANN_INDEX_LSH = 6
index_params = dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12, multi_probe_level=1)
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params, search_params)

# CLAHE — tworzony RAZ (nie w kazdej klatce!) dla unikniecia zbednych alokacji pamieci
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# 2. Ladowanie szablonow (naszych wygenerowanych kart JPG)
log_event(f"[INFO] Ladowanie cyfrowych wzorcow z {CV_ASSETS_DIR}")
reference_cards = {}
file_paths = glob.glob(os.path.join(CV_ASSETS_DIR, "*.jpg"))

if not file_paths:
    log_event("[BLAD] Nie znaleziono zadnych plikow wzorcow .jpg w katalogu!")
    exit(1)

for file_path in file_paths:
    card_name = os.path.basename(file_path).replace(".jpg", "")
    
    # Wczytywanie w odcieniach szarosci
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        continue
    
    # Stosujemy CLAHE takze na wzorcach — zapewnia spojnosc z klatkami kamery
    img = clahe.apply(img)
        
    kp, des = orb.detectAndCompute(img, None)
    if des is not None:
        kp = kp[:500]
        des = des[:500]

    # Obrocona o 180 stopni — karta postawiona do gory nogami (reversed)
    img_reversed = cv2.rotate(img, cv2.ROTATE_180)
    kp_rev, des_rev = orb.detectAndCompute(img_reversed, None)
    
    # Pre-trenowany BF Matcher dla upright wariantu karty (50x szybszy i dokładniejszy niż FLANN)
    card_matcher = None
    if des is not None and len(des) > 0:
        try:
            card_matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
            card_matcher.add([des])
            card_matcher.train()
        except cv2.error:
            card_matcher = None

    # Zapisujemy do pamieci referencyjnej
    reference_cards[card_name] = {
        "image": img,
        "keypoints": kp,
        "descriptors": des,
        "reversed_image": img_reversed,
        "reversed_keypoints": kp_rev,
        "reversed_descriptors": des_rev,
        "matcher": card_matcher,
    }

log_event(f"[OK] Zaladowano {len(reference_cards)} wzorcow do pamieci (upright + reversed)!")
table_state = TableState(reference_cards.keys())
table_calibration = TableCalibration(table_width=CAMERA_WIDTH, table_height=CAMERA_HEIGHT)
log_event("[ARUCO] Modul kalibracji stolu zainicjalizowany (markery ID 10-13, DICT_4X4_50)")


def recognize_snapshot_crop(gray_crop):
    crop_for_matching = clahe.apply(gray_crop)
    config_values = runtime_config.values
    min_match_count = int(config_values.get("MIN_MATCH_COUNT", 12.0))
    ratio_thresh = config_values.get("RATIO_THRESH", 0.79)
    min_inlier_ratio = config_values.get("MIN_INLIER_RATIO", 0.25)
    
    result = recognize_card_crop(
        crop_for_matching, reference_cards, orb, flann,
        min_good_matches=min_match_count,
        lowe_ratio=ratio_thresh,
        min_inlier_ratio=min_inlier_ratio
    )
    if result is None:
        return None
    
    angle_deg = result.get("homography_angle_deg", 0.0)
    log_event(
        f"[DIAGNOSTYKA ORIENTACJI] Karta: {result['name']} | "
        f"Kąt z homografii: {angle_deg}° | "
        f"Ustalona orientacja: {result['orientation']} | "
        f"Pewność (inliers): {result.get('inlier_ratio', 0.0)}"
    )
    
    return {
        "name": result["name"],
        "confidence": result.get("confidence", 0.0),
        "orientation": result.get("orientation", "unknown"),
        "homography_angle_deg": angle_deg,
    }


runtime_metrics = RuntimeMetrics(maxlen=60)

snapshot_gate = SnapshotGate(SnapshotGateConfig(
    settle_seconds=SNAPSHOT_SETTLE_SECONDS,
    sample_count=SNAPSHOT_SAMPLE_COUNT,
    sample_interval_ms=SNAPSHOT_SAMPLE_INTERVAL_MS,
))
snapshot_pipeline = SnapshotFirstPipeline(
    camera_session=camera_session,
    opencv_preview=opencv_preview,
    status_store=status_store,
    diagnostics_writer=diagnostics_writer,
    snapshot_gate=snapshot_gate,
    snapshot_analyzer=snapshot_analyzer,
    table_calibration=table_calibration,
    runtime_metrics=runtime_metrics,
    runtime_config=runtime_config,
    build_operator_snapshot_fn=build_operator_snapshot,
    operator_warnings=operator_warnings,
    log_dir=LOG_DIR,
    runtime_profile=RUNTIME_PROFILE
)
snapshot_pipeline.snapshot_sample_count = SNAPSHOT_SAMPLE_COUNT
snapshot_pipeline.snapshot_sample_interval_ms = SNAPSHOT_SAMPLE_INTERVAL_MS

legacy_pipeline = StateFirstLegacyPipeline(
    camera_session=camera_session,
    opencv_preview=opencv_preview,
    status_store=status_store,
    diagnostics_writer=diagnostics_writer,
    table_calibration=table_calibration,
    table_state=table_state,
    runtime_metrics=runtime_metrics,
    runtime_config=runtime_config,
    build_operator_snapshot_fn=build_operator_snapshot,
    operator_warnings=operator_warnings,
    log_dir=LOG_DIR,
    reference_cards=reference_cards,
    orb=orb,
    flann=flann,
    clahe=clahe,
    runtime_profile=RUNTIME_PROFILE
)

# 3. Inicjalizacja Kamery — jawnie ustawiamy 720p (1280x720) dla wiecej cech ORB z wiekszej odleglosci
log_event("[KAMERA] Uruchamianie kamery... (Wcisnij 'q' by zamknac, cyfry '0'-'9' by przelaczac kamery w locie!)")
if not camera_session.open(0):
    log_event("[OSTRZEZENIE] Brak kamery pod indeksem 0. Wcisnij np. 1 lub 2 by zmienic.")

frame_width, frame_height = camera_session.frame_width, camera_session.frame_height
log_event(f"[KAMERA] Rozdzielczosc: {frame_width}x{frame_height}")

motion_detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)

# Petla glowna (Live feed)
while True:
    frame_loop_start = time.perf_counter()
    drain_control_messages(camera_session)
    config_values = runtime_config.values
    
    # Dynamiczna aktualizacja parametrów detektora ruchu i bramki snapshotu
    motion_detector.min_changed_ratio = config_values.get("MOTION_CHANGED_RATIO", 0.02)
    
    settle_seconds = config_values.get("SNAPSHOT_SETTLE_SECONDS", 0.5)
    if snapshot_gate.config.settle_seconds != settle_seconds:
        snapshot_gate.config = SnapshotGateConfig(
            settle_seconds=settle_seconds,
            sample_count=snapshot_gate.config.sample_count,
            sample_interval_ms=snapshot_gate.config.sample_interval_ms
        )
    camera_read_start = time.perf_counter()
    ret, frame = camera_session.read()
    runtime_metrics.add("camera_read_ms", (time.perf_counter() - camera_read_start) * 1000.0)

    preprocess_start = time.perf_counter()
    if not ret:
        # Zastepcze okno ostrzegawcze
        display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(display_frame, f"Brak wideo pod portem: {camera_session.camera_index}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(display_frame, f"Wcisnij inna cyfre (0-5) by szukac.", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        gray_frame = None
    else:
        # Aktualizujemy rozdzielczosc dynamicznie (na wypadek zmiany kamery)
        frame_height, frame_width = frame.shape[:2]
        
        display_frame = frame.copy()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Zastosowanie CLAHE — obiekt tworzony RAZ na poczatku, nie w kazdej klatce
        gray_frame = clahe.apply(gray_frame)
    runtime_metrics.add("preprocess_ms", (time.perf_counter() - preprocess_start) * 1000.0)

    # Kalibracja stolu ArUco — szukamy 4 markerow co klatke
    aruco_start = time.perf_counter()
    if gray_frame is not None:
        workspace_inflate_percent = config_values.get("WORKSPACE_INFLATE_PERCENT", 0.0)
        table_calibration.update(gray_frame, workspace_inflate_percent=workspace_inflate_percent)
    runtime_metrics.add("aruco_ms", (time.perf_counter() - aruco_start) * 1000.0)

    # Detekcja prostokatow kart (Task 3) — uruchamiana za feature flag
    detected_card_quads = []
    if USE_TABLE_CARD_DETECTION and gray_frame is not None:
        card_detect_start = time.perf_counter()
        # Preferujemy sprostowany obraz ArUco, fallback na surowa klatke
        if table_calibration.calibrated:
            detection_input = table_calibration.warp_frame(frame)
        else:
            detection_input = frame
        if detection_input is not None:
            detected_card_quads = find_card_quads(detection_input)
        runtime_metrics.add("card_detect_ms", (time.perf_counter() - card_detect_start) * 1000.0)
        runtime_metrics.add("card_quads_found", len(detected_card_quads))
    
    # 4. Wykrywamy punkty kluczowe w obecnej klatce
    feature_start = time.perf_counter()
    if gray_frame is not None:
        kp_frame, des_frame = orb.detectAndCompute(gray_frame, None)
    else:
        des_frame = None
    runtime_metrics.add("feature_detect_ms", (time.perf_counter() - feature_start) * 1000.0)

    if gray_frame is not None:
        motion_result = motion_detector.update(gray_frame)
    else:
        motion_result = motion_detector.update(np.zeros((8, 8), dtype=np.uint8))
    runtime_metrics.add("motion_changed_ratio", motion_result.changed_ratio)
    if motion_result.scene_settled:
        boost_frames_remaining = max(boost_frames_remaining, boost_after_layout_change_frames)

    if USE_SNAPSHOT_FIRST_CV:
        pipeline_result = snapshot_pipeline.process_frame(
            frame=frame,
            motion_result=motion_result,
            frame_width=frame_width,
            frame_height=frame_height,
            frame_loop_start=frame_loop_start
        )
        if pipeline_result["action"] == "quit":
            break
        elif pipeline_result["action"] == "switch":
            frame_width = pipeline_result["frame_width"]
            frame_height = pipeline_result["frame_height"]
            log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")
        continue
    
    # ==========================================================================
    # STATE-FIRST OPTIMIZATION (Task 10, Opus 2026-05-29) -> Hermetyzowane w legacy_pipeline
    # ==========================================================================
    pipeline_result = legacy_pipeline.process_frame(
        frame=frame,
        gray_frame=gray_frame,
        motion_result=motion_result,
        des_frame=des_frame,
        kp_frame=kp_frame,
        frame_width=frame_width,
        frame_height=frame_height,
        frame_loop_start=frame_loop_start
    )
    if pipeline_result["action"] == "quit":
        break
    elif pipeline_result["action"] == "switch":
        frame_width = pipeline_result["frame_width"]
        frame_height = pipeline_result["frame_height"]
        log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")
    continue

camera_session.close()
opencv_preview.close()
