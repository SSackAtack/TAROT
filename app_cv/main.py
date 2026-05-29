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
from tarotvision.camera_controls import probe_camera_control
from tarotvision.calibration_session import choose_best_candidate

# Konfiguracja
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.environ.get("TAROTVISION_LOG_DIR", os.path.join(PROJECT_ROOT, "logs"))
CV_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", "rider-waite-smith", "produkcja", "wzorce_cv"))
MIN_MATCH_COUNT = 18   # Obnizony do 18 — filtry geometryczne (homografia + validate_quad + aspect ratio + inlier ratio) skutecznie eliminuja szum
RATIO_THRESH = 0.79    # Zaostrzone z 0.83 do 0.79 dla czystosci dopasowan cech ORB
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
INACTIVE_PER_FRAME_ACTIVE = 1    # Gdy sa aktywne karty, chronimy FPS i szukamy nowych wolniej
INACTIVE_PER_FRAME_BOOST = 3     # Po zmianie ukladu chwilowo skanujemy szybciej, ale bez powrotu do pelnego kosztu
BOOST_AFTER_LAYOUT_CHANGE_FRAMES = 12
REVERIFY_INTERVAL_FRAMES = 180
TRACKING_IOU_THRESHOLD = 0.35
TRACKING_REVERIFY_GAP_FRAMES = 24

# System dwufazowy "Zlap i Zamroz" — eliminuje mikro-jitter statycznych kart
LOCK_AFTER_FRAMES = 8      # Klatki stabilnej detekcji zanim pozycja zostanie zamrozona
LOCK_DEAD_ZONE_POS = 3.0   # Minimalny ruch pozycji (w jednostkach sceny) zeby odblokowac karte (zwiekszony pod katem szumow centroidu)
LOCK_DEAD_ZONE_ANGLE = 0.5 # Minimalny ruch kata (w radianach, ~28 stopni) zeby odblokowac karte

# Stan wspoldzielony miedzy watkiem wizyjnym (CV) a watkiem serwera WebSocket
status_lock = threading.Lock()
current_status = {
    "detected": False,
    "cards": [],
    "metrics": {},
    "runtime": {},
    "operator": {
        "enabled": True,
        "active_profile": "default",
        "parameters": {},
        "parameter_metadata": {},
        "pending_changes": {},
        "supported_camera_controls": {},
        "calibration": {"state": "idle", "last_score": None},
        "warnings": [],
    },
}

# Zestaw polaczonych klientow
connected_clients = set()
control_messages = []
config_session = RuntimeConfigSession()
runtime_config = config_session.config
operator_warnings = []
supported_camera_controls = {}
calibration_state = {"state": "idle", "last_score": None}
profile_store = ProfileStore(os.path.join(LOG_DIR, "calibration_profiles"))
active_tuning_profile = "default"

os.makedirs(LOG_DIR, exist_ok=True)
diagnostics_path = os.path.join(LOG_DIR, "cv_metrics.jsonl")
if os.environ.get("TAROTVISION_RESET_LOGS") == "1" and os.path.exists(diagnostics_path):
    os.remove(diagnostics_path)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "cv_runtime.log"),
    filemode="w",
    level=logging.INFO,
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
        "supported_camera_controls": copy.deepcopy(supported_camera_controls),
        "calibration": copy.deepcopy(calibration_state),
        "warnings": list(operator_warnings[-8:]),
    }


def add_operator_warning(message):
    operator_warnings.append(message)
    log_event(f"[OPERATOR] {message}")


def probe_camera_controls(capture):
    probes = {
        "CAP_PROP_FOCUS": (cv2.CAP_PROP_FOCUS, 120.0),
        "CAP_PROP_EXPOSURE": (cv2.CAP_PROP_EXPOSURE, -6.0),
        "CAP_PROP_CONTRAST": (cv2.CAP_PROP_CONTRAST, 120.0),
        "CAP_PROP_AUTOFOCUS": (cv2.CAP_PROP_AUTOFOCUS, 0.0),
    }
    results = {}
    for name, (prop_id, test_value) in probes.items():
        probe = probe_camera_control(capture, prop_id, test_value)
        results[name] = {
            "supported": probe.supported,
            "requested_value": probe.requested_value,
            "readback_value": probe.readback_value,
        }
    return results


def handle_control_message(message, capture):
    global supported_camera_controls
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
        supported_camera_controls = probe_camera_controls(capture)
        add_operator_warning("Zakonczono probe obslugi parametrów kamery")
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


def drain_control_messages(capture):
    with status_lock:
        queued_messages = list(control_messages)
        control_messages.clear()
    for message in queued_messages:
        try:
            handle_control_message(message, capture)
        except Exception as exc:
            add_operator_warning(f"Blad obslugi {message.type}: {exc}")


def append_diagnostics(metrics_snapshot, runtime_snapshot, active_cards):
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "detected": len(active_cards) > 0,
        "card_count": len(active_cards),
        "cards": active_cards,
        "metrics": metrics_snapshot,
        "runtime": runtime_snapshot
    }
    with open(diagnostics_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

async def handler(websocket):
    log_event(f"[WEBSOCKET] Polaczono klienta: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        # Wyslij natychmiast obecny stan (bezpieczna gleboka kopia)
        with status_lock:
            state = copy.deepcopy(current_status)
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
            with status_lock:
                state_to_send = copy.deepcopy(current_status)
            
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

def validate_quadrilateral(dst):
    """Walidacja geometryczna czworokata: proporcje bokow, katy wewnetrzne i aspect ratio karty."""
    # dst ma ksztalt (4, 1, 2)
    p0 = dst[0][0] # Gorny-lewy (TL)
    p1 = dst[1][0] # Dolny-lewy (BL)
    p2 = dst[2][0] # Dolny-prawy (BR)
    p3 = dst[3][0] # Gorny-prawy (TR)
    
    # 1. Obliczamy dlugosci czterech bokow
    side_left = np.linalg.norm(p1 - p0)
    side_bottom = np.linalg.norm(p2 - p1)
    side_right = np.linalg.norm(p3 - p2)
    side_top = np.linalg.norm(p0 - p3)
    
    # Zabezpieczenie przed mikroskopijnymi szumami
    if min(side_left, side_bottom, side_right, side_top) < 25.0:
        return False
        
    # 2. Sprawdzamy stosunek dlugosci naprzeciwleglych bokow (lewy vs prawy, gora vs dol)
    # W rzucie perspektywicznym dopuszczamy drobne zwezenia, ale nie drastyczne kliny/trojkaty
    ratio_lr = side_left / side_right if side_left > side_right else side_right / side_left
    ratio_tb = side_top / side_bottom if side_top > side_bottom else side_bottom / side_top
    
    if ratio_lr > 1.95 or ratio_tb > 1.95:
        return False
        
    # 3. Sprawdzamy katy wewnetrzne przy uzyciu cosinusow (szukamy zblizonych do 90 stopni)
    def get_cos_angle(a, b, c):
        ba = a - b
        bc = c - b
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba == 0 or norm_bc == 0:
            return 1.0
        return np.dot(ba, bc) / (norm_ba * norm_bc)
        
    cos_0 = abs(get_cos_angle(p3, p0, p1))
    cos_1 = abs(get_cos_angle(p0, p1, p2))
    cos_2 = abs(get_cos_angle(p1, p2, p3))
    cos_3 = abs(get_cos_angle(p2, p3, p0))
    
    # Prog 0.82 odrzuca katy ostrzejsze niz ~35 i rozwarte powyzej ~145 stopni
    MAX_COS = 0.82
    if cos_0 > MAX_COS or cos_1 > MAX_COS or cos_2 > MAX_COS or cos_3 > MAX_COS:
        return False
    
    # 4. Sprawdzamy aspect ratio czworokata (karty tarota maja proporcje ~1.72)
    avg_height = (side_left + side_right) / 2.0
    avg_width = (side_top + side_bottom) / 2.0
    if avg_width > 0:
        detected_ratio = avg_height / avg_width
        if abs(detected_ratio - CARD_ASPECT_RATIO) > CARD_ASPECT_TOLERANCE:
            return False
        
    return True

def configure_camera_capture(capture):
    """Wymusza docelowa rozdzielczosc kamery i zwraca faktycznie ustawiony rozmiar."""
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or CAMERA_WIDTH
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or CAMERA_HEIGHT
    return width, height

def polygon_iou(poly_a, poly_b):
    """Liczy IoU dwoch wypuklych czworokatow OpenCV w formacie (4, 1, 2)."""
    area_a = cv2.contourArea(poly_a)
    area_b = cv2.contourArea(poly_b)
    if area_a <= 0 or area_b <= 0:
        return 0.0
    
    try:
        intersection_area, _ = cv2.intersectConvexConvex(
            np.float32(poly_a).reshape(-1, 2),
            np.float32(poly_b).reshape(-1, 2)
        )
    except cv2.error:
        return 0.0
    
    union_area = area_a + area_b - intersection_area
    if union_area <= 0:
        return 0.0
    return float(intersection_area / union_area)

def deduplicate_detections(candidates):
    """Zostawia najlepsze dopasowanie dla nakladajacych sie detekcji tej samej fizycznej karty."""
    selected = []
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (item["count"], item["inlier_ratio"], item["area"]),
        reverse=True
    )
    
    for candidate in sorted_candidates:
        overlaps_existing = any(
            polygon_iou(candidate["dst"], accepted["dst"]) > DETECTION_IOU_THRESHOLD
            for accepted in selected
        )
        if not overlaps_existing:
            selected.append(candidate)
    
    return {candidate["name"]: candidate for candidate in selected}


def quad_to_box(quad):
    xs = quad[:, 0, 0]
    ys = quad[:, 0, 1]
    x_min = int(np.min(xs))
    y_min = int(np.min(ys))
    x_max = int(np.max(xs))
    y_max = int(np.max(ys))
    return (x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min))

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
        
    # Wyliczamy od razu kluczowe cechy dla karty
    kp, des = orb.detectAndCompute(img, None)
    
    # Zapisujemy do pamieci referencyjnej
    reference_cards[card_name] = {
        "image": img,
        "keypoints": kp,
        "descriptors": des
    }

log_event(f"[OK] Zaladowano {len(reference_cards)} wzorcow do pamieci!")
table_state = TableState(reference_cards.keys())

# 3. Inicjalizacja Kamery — jawnie ustawiamy 720p (1280x720) dla wiecej cech ORB z wiekszej odleglosci
log_event("[KAMERA] Uruchamianie kamery... (Wcisnij 'q' by zamknac, cyfry '0'-'9' by przelaczac kamery w locie!)")
camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    log_event("[OSTRZEZENIE] Brak kamery pod indeksem 0. Wcisnij np. 1 lub 2 by zmienic.")

frame_width, frame_height = configure_camera_capture(cap)
log_event(f"[KAMERA] Rozdzielczosc: {frame_width}x{frame_height}")

# Parametry stabilizacji detekcji (debouncing) dla wielu kart
debounce_state = {}
DEBOUNCE_FRAMES = 3  # Karta musi byc stabilnie wykryta przez 3 klatki z rzedu
LOSS_FRAMES = 8      # Karta musi zniknac na 8 klatek z rzedu, aby zostala schowana

# Zoptymalizowana kolejka round-robin do sprawdzania nieaktywnych kart
inactive_index = 0
prev_time = time.time()  # Do pomiaru FPS
runtime_metrics = RuntimeMetrics(maxlen=60)
last_diagnostics_time = 0.0
frame_counter = 0
boost_frames_remaining = 0
previous_active_card_names = set()
schedule_mode_name = "empty_scan"
motion_detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
tracked_boxes_by_name = {}

# Petla glowna (Live feed)
while True:
    frame_counter += 1
    drain_control_messages(cap)
    config_values = runtime_config.values
    min_match_count = int(config_values["MIN_MATCH_COUNT"])
    ratio_thresh = config_values["RATIO_THRESH"]
    min_inlier_ratio = config_values["MIN_INLIER_RATIO"]
    ema_alpha = config_values["EMA_ALPHA"]
    boost_after_layout_change_frames = int(config_values["BOOST_AFTER_LAYOUT_CHANGE_FRAMES"])
    reverify_interval_frames = int(config_values["REVERIFY_INTERVAL_FRAMES"])
    tracking_iou_threshold = config_values["TRACKING_IOU_THRESHOLD"]
    lock_dead_zone_pos = config_values["LOCK_DEAD_ZONE_POS"]
    lock_dead_zone_angle = config_values["LOCK_DEAD_ZONE_ANGLE"]
    frame_loop_start = time.perf_counter()
    camera_read_start = time.perf_counter()
    ret, frame = cap.read()
    runtime_metrics.add("camera_read_ms", (time.perf_counter() - camera_read_start) * 1000.0)

    preprocess_start = time.perf_counter()
    if not ret:
        # Zastepcze okno ostrzegawcze
        display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(display_frame, f"Brak wideo pod portem: {camera_index}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
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
    
    # ==========================================================================
    # STATE-FIRST OPTIMIZATION (Task 10, Opus 2026-05-29)
    # Serce optymalizacji: karty LOCKED sledzone tanio po konturze/IoU,
    # pelne ORB/FLANN tylko dla NEEDS_REVERIFY i nowych kandydatow.
    # Dlaczego: matching ORB = ~60ms/karte, contour tracking IoU = ~0.01ms/karte.
    # ==========================================================================

    # Lista kandydatow wykrytych w tej klatce; po petli usuwamy duplikaty przestrzenne
    detection_candidates = []
    detected_this_frame = {}
    
    all_card_names = list(reference_cards.keys())
    candidate_card_names = table_state.available_card_ids
    runtime_metrics.add("available_card_count", len(candidate_card_names))
    runtime_metrics.add("tracked_card_count", len(table_state.cards))
    runtime_metrics.add("boost_frames_remaining", boost_frames_remaining)

    # --- KROK 1: Contour tracking PRZED matchingiem ORB ---
    # Karty LOCKED z dobrym IoU sa podtrzymywane tanio — nie potrzebuja ORB.
    # Przenosimy tracking tutaj, zeby wiedziec KTORE karty mozna pominac.
    tracked_boxes = {name: box for name, box in tracked_boxes_by_name.items() if name in table_state.cards}
    locked_tracked_this_frame = {}  # Karty LOCKED utrzymane przez contour tracking
    orb_skipped_locked = 0
    tracking_reverify_count = 0

    if gray_frame is not None and tracked_boxes:
        # Prosty contour tracking: szukamy konturow prostokatnych w klatce
        # i dopasowujemy je do znanych pozycji LOCKED kart po IoU.
        # Unikamy kosztownego ORB/FLANN — to jest ~1000x tansze.
        _, thresh = cv2.threshold(gray_frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrujemy kontury do rozsadnych rozmiarow kart
        min_contour_area = frame_width * frame_height * 0.005
        max_contour_area = frame_width * frame_height * 0.5
        contour_boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_contour_area <= area <= max_contour_area:
                contour_boxes.append(cv2.boundingRect(cnt))
        
        assigned_tracked = assign_boxes_to_cards(
            tracked_boxes,
            contour_boxes,
            min_iou=tracking_iou_threshold,
        )
        runtime_metrics.add("tracked_assignments", len(assigned_tracked))
        
        # Dla kazdej LOCKED karty z dobrym IoU: podtrzymaj pozycje BEZ ORB
        for card_id, matched_box in assigned_tracked.items():
            tracked_card = table_state.cards.get(card_id)
            if tracked_card is None:
                continue
            
            phase = debounce_state.get(card_id, {}).get("phase", "DETECTING")
            
            if phase == "LOCKED" and tracked_card.phase == PHASE_LOCKED:
                # Karta LOCKED z dobrym IoU — podtrzymujemy tanio!
                tracked_card.last_seen_frame = frame_counter
                # NIE nadpisujemy tracked_boxes_by_name — zachowujemy precyzyjny bbox z ORB.
                # Konturowy bbox zawiera cienie i blat, wiec jest za duzy.
                orb_skipped_locked += 1
                
                # Obliczamy nowa pozycje na stole na podstawie centroidu rzeczywistego konturu
                bx, by, bw, bh = matched_box
                cx = bx + bw / 2.0
                cy = by + bh / 2.0
                contour_x = float((cx / frame_width * 2.0 - 1.0) * 13.0)
                contour_y = float((1.0 - (cy / frame_height) * 2.0) * 7.8)

                # Wstrzykujemy "tracking detection" do detected_this_frame
                # uzywajac nowej pozycji konturu, aby umozliwic detekcje ruchu!
                locked_tracked_this_frame[card_id] = {
                    "name": card_id,
                    "x": contour_x,
                    "y": contour_y,
                    "angle": debounce_state[card_id].get("locked_angle", tracked_card.angle),
                    # Syntetyczne wartosci — karta nie byla matchowana ORB
                    "count": 0,
                    "inlier_ratio": 1.0,
                    "area": bw * bh,
                    "dst": None,  # Brak quada z ORB — uzywamy bbox
                    "tracked_by_contour": True,  # Flaga diagnostyczna
                }
            else:
                # Karta w innej fazie — tracking OK, ale nadal moze isc do ORB
                tracked_card.last_seen_frame = frame_counter
                # NIE nadpisujemy tracked_boxes_by_name — j.w.
        
        # Karty LOCKED bez przypisania IoU — wymagaja reweryfikacji
        for card_id, tracked_card in table_state.cards.items():
            if card_id in assigned_tracked:
                continue
            if frame_counter - tracked_card.last_seen_frame >= TRACKING_REVERIFY_GAP_FRAMES:
                table_state.mark_needs_reverify(card_id, "tracking_gap")
                tracking_reverify_count += 1
    else:
        runtime_metrics.add("tracked_assignments", 0)

    runtime_metrics.add("tracking_reverify_count", tracking_reverify_count)
    runtime_metrics.add("orb_skipped_locked", orb_skipped_locked)

    # --- KROK 2: Budowa listy kart do ORB matchingu ---
    # Tylko: nowe kandydaty (available) + karty NEEDS_REVERIFY
    # LOCKED karty juz utrzymane przez contour tracking — pomijamy!
    reverify_card_names = [
        card_id for card_id, tracked_card in table_state.cards.items()
        if tracked_card.phase == PHASE_NEEDS_REVERIFY
        or should_reverify(
            frame_index=frame_counter,
            last_verified_frame=tracked_card.last_seen_frame,
            interval_frames=reverify_interval_frames,
            suspicious=False,
        )
    ]
    runtime_metrics.add("reverify_due_count", len(reverify_card_names))

    # Pula do matchingu = nowe (available) + wymagajace reweryfikacji
    # Karty LOCKED z dobrym IoU NIE trafiaja tutaj — to jest serce optymalizacji.
    orb_candidate_names = list(dict.fromkeys(candidate_card_names + reverify_card_names))

    active_count = sum(
        1
        for state in debounce_state.values()
        if state.get("stable_count", 0) > 0
    )
    schedule_mode = get_schedule_mode(
        active_count=active_count,
        boost_frames_remaining=boost_frames_remaining,
        inactive_per_frame_empty=INACTIVE_PER_FRAME_EMPTY,
        inactive_per_frame_active=INACTIVE_PER_FRAME_ACTIVE,
        inactive_per_frame_boost=INACTIVE_PER_FRAME_BOOST,
    )
    schedule_mode_name = schedule_mode.name
    inactive_per_frame = schedule_mode.inactive_per_frame
    matching_selection = choose_cards_to_match(
        all_card_names=orb_candidate_names,
        debounce_state=debounce_state,
        inactive_index=inactive_index,
        frame_counter=frame_counter,
        locked_refresh_interval=LOCKED_REFRESH_INTERVAL,
        inactive_per_frame=inactive_per_frame,
    )
    active_names = matching_selection.active_names
    inactive_names = matching_selection.inactive_names
    inactive_index = matching_selection.next_inactive_index
    cards_to_check = matching_selection.names
    runtime_metrics.add("cards_checked", len(cards_to_check))

    # --- KROK 3: Matching ORB/FLANN — tylko dla wybranych kart ---
    matching_start = time.perf_counter()
    if des_frame is not None and len(des_frame) > min_match_count:
        # Iterujemy TYLKO po kartach wymagajacych pelnego rozpoznawania
        for name in cards_to_check:
            ref_data = reference_cards.get(name)
            if ref_data is None:
                continue
            des_ref = ref_data["descriptors"]
            if des_ref is None: continue
                
            # FLANN-LSH knnMatch — 2-5x szybszy niz BruteForce
            try:
                matches = flann.knnMatch(des_ref, des_frame, k=2)
            except cv2.error:
                continue
            
            good_matches = []
            # Lowe's ratio test (odrzuca niepewne i bledne dopasowania szumu)
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < ratio_thresh * n.distance:
                        good_matches.append(m)
                    
            if len(good_matches) >= min_match_count:
                # Karta ma duzo punktow! Liczymy homografie i sprawdzamy geometrie
                ref_kp = ref_data["keypoints"]
                src_pts = np.float32([ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None and mask is not None:
                    # Sprawdzamy proporcje inlierow (czy homografia jest stabilna)
                    inlier_ratio = np.sum(mask) / len(mask)
                    if inlier_ratio < min_inlier_ratio:
                        continue
                    
                    h, w = ref_data["image"].shape
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # A. Sprawdzamy wypuklosc
                    is_convex = cv2.isContourConvex(np.int32(dst))
                    
                    # B. Sprawdzamy pole powierzchni czworokata
                    area = cv2.contourArea(dst)
                    
                    # C. Rozsadny rozmiar karty (dynamicznie skalowany do rozdzielczosci kamery)
                    max_area = frame_width * frame_height * 0.9
                    min_area = frame_width * frame_height * 0.008
                    is_reasonable_size = (min_area <= area <= max_area)
                    
                    if is_convex and is_reasonable_size and validate_quadrilateral(dst):
                        # 1. Obliczamy geometryczny srodek (centroid) karty
                        cx = float(np.mean(dst[:, 0, 0]))
                        cy = float(np.mean(dst[:, 0, 1]))
                        
                        # 2. Przeliczamy wspolrzedne — skalowanie dopasowane do pelnego pola widzenia kamery
                        pos_x = float((cx / frame_width * 2.0 - 1.0) * 13.0)
                        pos_y = float((1.0 - (cy / frame_height) * 2.0) * 7.8)
                        
                        # 3. Obliczamy kat obrotu karty na biurku
                        x0, y0 = dst[0][0][0], dst[0][0][1]
                        x3, y3 = dst[3][0][0], dst[3][0][1]
                        angle = -float(math.atan2(y3 - y0, x3 - x0))

                        # Karta przeszla wszystkie filtry! Zapisujemy kandydata detekcji
                        detection_candidates.append({
                            "name": name,
                            "count": len(good_matches),
                            "inlier_ratio": float(inlier_ratio),
                            "area": float(area),
                            "dst": dst,
                            "x": pos_x,
                            "y": pos_y,
                            "angle": angle
                        })
        
        detected_this_frame = deduplicate_detections(detection_candidates)

    # --- KROK 4: Scalenie wynikow ORB + contour tracking ---
    # Karty LOCKED utrzymane tanio przez contour tracking dokladamy do detected_this_frame,
    # zeby debounce_state utrzymal ich stable_count (nie zaczal loss_count).
    for card_id, tracked_data in locked_tracked_this_frame.items():
        if card_id not in detected_this_frame:
            detected_this_frame[card_id] = tracked_data
    runtime_metrics.add("locked_tracked_count", len(locked_tracked_this_frame))

    # Track how many observed boxes are potentially "new space" outside occupied tracked areas.
    observed_boxes = [
        quad_to_box(item["dst"]) for item in detected_this_frame.values()
        if item.get("dst") is not None
    ]
    unoccupied_observed_boxes = filter_boxes_outside_occupied(
        observed_boxes,
        list(tracked_boxes.values()),
        max_iou=0.1,
    )
    runtime_metrics.add("unoccupied_observed_boxes", len(unoccupied_observed_boxes))

    runtime_metrics.add("matching_ms", (time.perf_counter() - matching_start) * 1000.0)
                
    # 6. Dwufazowa stabilizacja: DETECTING -> LOCKED ("Zlap i Zamroz")
    # Faza DETECTING: pelna moc ORB, szybka identyfikacja, EMA wygladzanie
    # Faza LOCKED: pozycja zamrozona, aktualizacja TYLKO gdy karta ruszy sie o wiecej niz LOCK_DEAD_ZONE
    active_detected_cards = []
    
    for name in reference_cards.keys():
        if name not in debounce_state:
            debounce_state[name] = {
                "stable_count": 0, 
                "loss_count": 0,
                "phase": "DETECTING"  # DETECTING lub LOCKED
            }
            
        if name in detected_this_frame:
            debounce_state[name]["stable_count"] += 1
            debounce_state[name]["loss_count"] = 0
            
            new_x = detected_this_frame[name]["x"]
            new_y = detected_this_frame[name]["y"]
            new_angle = detected_this_frame[name]["angle"]
            
            phase = debounce_state[name]["phase"]
            
            if phase == "DETECTING":
                # Faza wykrywania — EMA wygladzanie, szybka konwergencja
                old_x = debounce_state[name].get("last_x", new_x)
                old_y = debounce_state[name].get("last_y", new_y)
                old_angle = debounce_state[name].get("last_angle", new_angle)
                
                debounce_state[name]["last_x"] = ema_alpha * new_x + (1 - ema_alpha) * old_x
                debounce_state[name]["last_y"] = ema_alpha * new_y + (1 - ema_alpha) * old_y
                debounce_state[name]["last_angle"] = ema_alpha * new_angle + (1 - ema_alpha) * old_angle
                
                # Po LOCK_AFTER_FRAMES stabilnych klatkach — zamrazamy pozycje
                if debounce_state[name]["stable_count"] >= LOCK_AFTER_FRAMES:
                    debounce_state[name]["phase"] = "LOCKED"
                    debounce_state[name]["locked_x"] = debounce_state[name]["last_x"]
                    debounce_state[name]["locked_y"] = debounce_state[name]["last_y"]
                    debounce_state[name]["locked_angle"] = debounce_state[name]["last_angle"]
                    
            elif phase == "LOCKED":
                # Faza zamrozona — ignorujemy drobne wahania ORB
                locked_x = debounce_state[name]["locked_x"]
                locked_y = debounce_state[name]["locked_y"]
                locked_angle = debounce_state[name]["locked_angle"]
                
                # Sprawdzamy czy karta NAPRAWDE sie ruszyla (duzy ruch)
                dx = abs(new_x - locked_x)
                dy = abs(new_y - locked_y)
                d_angle = abs(new_angle - locked_angle)
                
                if dx > lock_dead_zone_pos or dy > lock_dead_zone_pos or d_angle > lock_dead_zone_angle:
                    # Karta sie ruszyla! Odblokowujemy i wracamy do fazy wykrywania
                    debounce_state[name]["phase"] = "DETECTING"
                    debounce_state[name]["stable_count"] = 0
                    debounce_state[name]["last_x"] = new_x
                    debounce_state[name]["last_y"] = new_y
                    debounce_state[name]["last_angle"] = new_angle
                    boost_frames_remaining = max(boost_frames_remaining, boost_after_layout_change_frames)
                    # Zgłaszamy ruch do table_state, aby karta została zweryfikowana przez ORB w nowym miejscu
                    table_state.mark_needs_reverify(name, "motion_detected")
                    log_event(f"[RUCH] Karta {name} przesunela sie (dx={dx:.2f}, dy={dy:.2f}). Odblokowanie i zgloszenie do ORB.")
                else:
                    # Karta statyczna — uzywamy zamrozonej pozycji (ZERO jitteru)
                    debounce_state[name]["last_x"] = locked_x
                    debounce_state[name]["last_y"] = locked_y
                    debounce_state[name]["last_angle"] = locked_angle
        elif name in cards_to_check:
            debounce_state[name]["loss_count"] += 1
            if debounce_state[name]["loss_count"] >= LOSS_FRAMES:
                debounce_state[name]["stable_count"] = 0
                debounce_state[name]["phase"] = "DETECTING"  # Reset do fazy wykrywania
        else:
            # Karta nie byla matchowana w tej klatce (np. LOCKED czeka na okresowy refresh),
            # wiec nie traktujemy braku detekcji jako realnej utraty.
            pass
                
        # Karta jest uznana za aktywnie wykryta, jesli osiagnela prog stabilnosci
        if debounce_state[name]["stable_count"] >= DEBOUNCE_FRAMES:
            active_detected_cards.append({
                "name": name,
                "x": round(debounce_state[name].get("last_x", 0.0), 4),
                "y": round(debounce_state[name].get("last_y", 0.0), 4),
                "angle": round(debounce_state[name].get("last_angle", 0.0), 4)
            })

    active_card_names = {card["name"] for card in active_detected_cards}
    for card in active_detected_cards:
        table_state.upsert_locked(
            card_id=card["name"],
            x=card["x"],
            y=card["y"],
            angle=card["angle"],
            confidence=1.0,
            frame_index=frame_counter,
        )
    # Usuwamy nieaktywne karty z table_state, które naprawde zniknely ze stolu (potwierdzone przez LOSS_FRAMES)
    for name in list(table_state.cards.keys()):
        if name in debounce_state and debounce_state[name]["loss_count"] >= LOSS_FRAMES:
            table_state.remove_card(name)
            log_event(f"[USUNIECIE] Karta {name} zniknela ze stolu. Usuniecie ze stanu i powrot do puli dostepnych.")
    for name, item in detected_this_frame.items():
        # Karty sledzone przez contour tracking maja dst=None — nie nadpisujemy ich bbox
        if item.get("dst") is not None:
            tracked_boxes_by_name[name] = quad_to_box(item["dst"])
    newly_active_cards = active_card_names - previous_active_card_names
    if newly_active_cards:
        boost_frames_remaining = max(boost_frames_remaining, boost_after_layout_change_frames)
        previous_active_card_names = active_card_names
    elif active_card_names != previous_active_card_names:
        previous_active_card_names = active_card_names
    elif boost_frames_remaining > 0:
        boost_frames_remaining -= 1
            
    # Aktualizujemy wspoldzielony stan (bezpieczna gleboka kopia wewnatrz locka)
    metrics_snapshot = runtime_metrics.snapshot()
    runtime_snapshot = {
        "profile": RUNTIME_PROFILE,
        "camera_index": camera_index,
        "capture_width": frame_width,
        "capture_height": frame_height,
        "camera_focus_locked": CAMERA_FOCUS_LOCKED,
        "camera_exposure_locked": CAMERA_EXPOSURE_LOCKED
    }
    runtime_snapshot["schedule_mode"] = schedule_mode_name
    runtime_snapshot["boost_frames_remaining"] = boost_frames_remaining
    runtime_snapshot["available_card_count"] = len(table_state.available_card_ids)
    runtime_snapshot["tracked_card_count"] = len(table_state.cards)
    runtime_snapshot["reverify_interval_frames"] = reverify_interval_frames
    runtime_snapshot["tracking_iou_threshold"] = tracking_iou_threshold
    status_update_start = time.perf_counter()
    with status_lock:
        current_status["detected"] = len(active_detected_cards) > 0
        current_status["cards"] = active_detected_cards
        current_status["metrics"] = metrics_snapshot
        current_status["runtime"] = runtime_snapshot
        current_status["operator"] = build_operator_snapshot()
    runtime_metrics.add("status_update_ms", (time.perf_counter() - status_update_start) * 1000.0)

    diagnostics_time = time.time()
    if diagnostics_time - last_diagnostics_time >= 1.0:
        append_diagnostics(metrics_snapshot, runtime_snapshot, active_detected_cards)
        last_diagnostics_time = diagnostics_time

    # 7. Rysowanie ramek — kolor zalezy od fazy:
    # ZIELONA = DETECTING, NIEBIESKO-ZLOTA = LOCKED (ORB), TURKUSOWA = LOCKED (contour tracking)
    for name, data in detected_this_frame.items():
        dst = data.get("dst")
        match_count = data["count"]
        is_contour_tracked = data.get("tracked_by_contour", False)
        
        # Sprawdzamy faze karty
        phase = debounce_state.get(name, {}).get("phase", "DETECTING")
        
        if is_contour_tracked:
            box_color = (200, 200, 0)   # Turkusowa (BGR) — tracking bez ORB
            text_color = (200, 200, 0)
            status_text = "TRACKED"
        elif phase == "LOCKED":
            box_color = (255, 180, 0)   # Niebiesko-zlota (BGR) — zamrozona
            text_color = (255, 180, 0)
            status_text = "LOCKED"
        else:
            box_color = (0, 255, 0)     # Zielona — aktywne wykrywanie
            text_color = (0, 0, 255)
            status_text = "DETECTING"
        
        # Karty sledzone przez contour tracking nie maja quada ORB — rysujemy bbox
        if dst is not None:
            display_frame = cv2.polylines(display_frame, [np.int32(dst)], True, box_color, 3, cv2.LINE_AA)
            top_y = min([pt[0][1] for pt in dst])
            top_x = min([pt[0][0] for pt in dst])
        elif name in tracked_boxes_by_name:
            bx, by, bw, bh = tracked_boxes_by_name[name]
            cv2.rectangle(display_frame, (bx, by), (bx + bw, by + bh), box_color, 3, cv2.LINE_AA)
            top_y = by
            top_x = bx
        else:
            continue
        
        cv2.putText(display_frame, f"{name.upper()} ({match_count} pkt) [{status_text}]", 
                    (int(top_x), int(top_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, text_color, 2, cv2.LINE_AA)

    # Obliczanie i rysowanie FPS na żywo (pomaga w weryfikacji wydajności)
    current_time = time.time()
    time_diff = current_time - prev_time
    fps = 1.0 / time_diff if time_diff > 0 else 0.0
    prev_time = current_time
    runtime_metrics.add("fps", fps)
    
    cv2.putText(display_frame, f"FPS: {fps:.1f}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(display_frame, f"ORB: {len(cards_to_check)} | IoU: {orb_skipped_locked} | Pula: {len(inactive_names)}", 
                (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    runtime_metrics.add("frame_loop_ms", (time.perf_counter() - frame_loop_start) * 1000.0)

    cv2.imshow('TarotVision - AI Detection (Wcisnij Q by wyjsc)', display_frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif ord('0') <= key <= ord('5'):
        new_index = key - ord('0')
        log_event(f"Zmiana kamery na indeks: {new_index}")
        cap.release()
        cap = cv2.VideoCapture(new_index)
        camera_index = new_index
        frame_width, frame_height = configure_camera_capture(cap)
        log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")

cap.release()
cv2.destroyAllWindows()
