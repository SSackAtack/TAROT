import cv2
import numpy as np
import os
import asyncio
import threading
import json
import copy
import websockets
import time
import logging

from tarotvision.metrics import RuntimeMetrics
from tarotvision.motion import MotionDetector
from tarotvision.runtime_config import RuntimeConfigSession, ParameterValidationError
from tarotvision.tuning_protocol import parse_control_message, ControlMessageError
from tarotvision.profile_store import ProfileStore
from tarotvision.camera_controls import read_camera_control
from tarotvision.calibration_session import choose_best_candidate
from tarotvision.table_calibration import TableCalibration
from tarotvision.card_recognition import recognize_card_crop
from tarotvision.background_model import BackgroundModel
from tarotvision.reference_loader import load_active_reference_cards
from tarotvision.card_detection_profiles import find_card_quads_multi_profile
from tarotvision.snapshot_gate import SnapshotGate, SnapshotGateConfig
from tarotvision.snapshot_analyzer import SnapshotAnalyzer
from tarotvision.camera import CameraSession
from tarotvision.preview import OpenCvPreview
from tarotvision.pipelines import SnapshotFirstPipeline
from tarotvision.frame_stream import LatestFrameStore, start_preview_server
from tarotvision.operator_explainability import build_cv_explainability
from tarotvision.autotune_session import AutotuneSession
from tarotvision.autotune_session_log import AutotuneSessionLog
from tarotvision.autotune_profiles import generate_candidate_profiles
from tarotvision.calibration_wizard_scoring import score_calibration_wizard_samples
from tarotvision.calibration_wizard_status import build_calibration_wizard_status

# Konfiguracja
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.environ.get("TAROTVISION_LOG_DIR", os.path.join(PROJECT_ROOT, "logs"))
DECK_NAME = os.environ.get("TAROTVISION_DECK", "rider-waite-smith")
CV_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", DECK_NAME, "produkcja", "wzorce_cv"))
MIN_MATCH_COUNT = 18   # Obnizony do 18 — filtry geometryczne (homografia + validate_quad + aspect ratio + inlier ratio) skutecznie eliminuja szum
RATIO_THRESH = 0.75    # Zaostrzone z 0.79 do 0.75 dla wyeliminowania dopasowan krzyzowych i poprawy homografii podobnych kart (np. Star i Moon)
MIN_INLIER_RATIO = 0.3 # Minimalna proporcja inlierow w homografii RANSAC (odrzuca niestabilne dopasowania)
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
RUNTIME_PROFILE = "cpu_baseline"
CAMERA_FOCUS_LOCKED = True      # Ustawienie operatorskie: AnkerWork C310 ma pracowac z blokada AF
CAMERA_EXPOSURE_LOCKED = True   # Ustawienie operatorskie: blokada ekspozycji zmniejsza flicker i false positives
SNAPSHOT_SETTLE_SECONDS = 0.5
SNAPSHOT_SAMPLE_COUNT = 1
SNAPSHOT_SAMPLE_INTERVAL_MS = 250

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
calibration_state = {
    "state": "idle",
    "last_score": None,
    "autotune": {
        "scenario": None,
        "state": "idle",
        "collected_count": 0,
        "required_count": 3,
        "ready_to_score": False,
        "recommendation": None,
        "last_score": None,
        "next_action": "Rozpocznij autotuning z poziomu konsoli."
    }
}
profile_store = ProfileStore(os.path.join(LOG_DIR, "calibration_profiles"))
autotune_session_log = AutotuneSessionLog(os.path.join(LOG_DIR, "autotune_sessions"))
active_tuning_profile = "default"
background_model = BackgroundModel()
pending_background_capture = False
autotune_session = None
autotune_candidate_profiles = []
autotune_quality_report = None

# Inicjalizacja DiagnosticsWriter, CameraSession i OpenCvPreview
reset_logs = os.environ.get("TAROTVISION_RESET_LOGS") == "1"
diagnostics_writer = DiagnosticsWriter(LOG_DIR, filename="cv_metrics.jsonl", reset_on_start=reset_logs)
camera_session = CameraSession(LOG_DIR, camera_width=1280, camera_height=720)
opencv_preview = OpenCvPreview("TarotVision - AI Detection (Wcisnij Q by wyjsc)")
frame_stream = LatestFrameStore()


logging.basicConfig(
    filename=os.path.join(LOG_DIR, "cv_runtime.log"),
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

def log_event(message):
    logging.info(message)
    print(message)


def build_operator_snapshot(cards=None, metrics=None, runtime=None, layout=None, warnings=None):
    calibration = copy.deepcopy(calibration_state)
    calibration["autotune"] = autotune_status_payload()
    return {
        "enabled": True,
        "active_profile": active_tuning_profile,
        "parameters": copy.deepcopy(runtime_config.values),
        "parameter_metadata": runtime_config.metadata(),
        "pending_changes": copy.deepcopy(config_session.pending_changes),
        "supported_camera_controls": copy.deepcopy(camera_session.supported_camera_controls),
        "calibration": calibration,
        "warnings": list(operator_warnings[-8:]),
        "explainability": build_cv_explainability(
            cards=cards or [],
            metrics=metrics or {},
            runtime=runtime or {},
            layout=layout or {},
            operator={"active_decks": status_store.get_status().get("operator", {}).get("active_decks", [])},
            warnings=warnings if warnings is not None else list(operator_warnings[-8:]),
        ),
    }


def add_operator_warning(message):
    operator_warnings.append(message)
    log_event(f"[OPERATOR] {message}")


def autotune_status_payload():
    return build_calibration_wizard_status(
        session=autotune_session,
        quality_report=autotune_quality_report,
        default_required_count=3,
    )


def current_active_decks():
    return status_store.get_status().get("operator", {}).get("active_decks", [])


def write_autotune_log(event, recommendation=None, profile_name=None):
    if autotune_session is None:
        return None
    try:
        return autotune_session_log.write_event(
            event=event,
            session=autotune_session,
            active_decks=current_active_decks(),
            runtime_parameters=runtime_config.values,
            recommendation=recommendation,
            profile_name=profile_name,
        )
    except OSError as exc:
        add_operator_warning(f"Nie zapisano logu autotuningu: {exc}")
        return None


def update_autotune_recommendation_from_samples():
    global calibration_state
    if autotune_session is None or not autotune_session.ready_to_score():
        return None

    samples = autotune_session.all_samples()
    profile_results = [
        {"profile": profile, "samples": samples}
        for profile in autotune_candidate_profiles
    ]
    from tarotvision.autotune_scoring import choose_best_profile_result
    best = choose_best_profile_result(profile_results)
    if best is None:
        return None

    autotune_session.set_recommendation(best)
    calibration_state = {
        "state": "recommendation_ready",
        "last_score": best["score"],
        "autotune": autotune_status_payload(),
    }
    return best


def autotune_state_collected_count(scenario):
    if autotune_session is None:
        return 0
    return len(autotune_session.samples.get(scenario, []))


def record_autotune_sample_from_snapshot(pipeline_sample):
    global calibration_state
    if autotune_session is None:
        return
        
    if autotune_session.recommendation is not None or autotune_session.ready_to_score():
        return
        
    scenario = autotune_session.current_scenario()
    expected_count = 0
    if scenario == "one_card":
        expected_count = 1
    elif scenario == "three_cards":
        expected_count = 3
        
    detected_count = pipeline_sample.get("detected_count", 0)
    accepted_count = pipeline_sample.get("accepted_count", 0)
    collected_before = len(autotune_session.samples.get(scenario, []))

    if scenario == "empty":
        if accepted_count != 0:
            log_event(
                f"[WIZARD DIAG] Odrzucono probke empty | "
                f"detected={detected_count}, accepted={accepted_count} | "
                f"expected=0/0 | reason=rejected_accepted_cards_on_empty"
            )
            add_operator_warning(
                f"Wizard: Odrzucono pusta mate - wykryto zaakceptowane karty ({accepted_count})"
            )
            return
    else:
        if detected_count != expected_count:
            log_event(
                f"[WIZARD DIAG] Odrzucono probke {scenario} | "
                f"detected={detected_count}, accepted={accepted_count} | "
                f"expected={expected_count} | reason=rejected_wrong_geometry"
            )
            add_operator_warning(
                f"Wizard: Odrzucono snapshot dla {scenario} (wykryto {detected_count} zamiast {expected_count} kart)"
            )
            return

    # Calculate false positives based on the scenario
    false_positive_count = 0
    if scenario == "empty":
        false_positive_count = detected_count
    elif scenario == "one_card":
        false_positive_count = max(0, detected_count - 1)
    elif scenario == "three_cards":
        false_positive_count = max(0, detected_count - 3)

    # Calculate recognition score as the average confidence of accepted cards
    confidences = pipeline_sample.get("recognition_confidences", [])
    recognition_score = sum(confidences) / len(confidences) if confidences else 0.0

    # Snapshot quality score serves as geometry_score
    geometry_score = pipeline_sample.get("snapshot_quality_score", 0.0)

    sample = {
        "scenario": scenario,
        "timestamp_ms": int(time.time() * 1000),
        "detected_count": detected_count,
        "candidate_count": detected_count,
        "accepted_count": accepted_count,
        "expected_count": expected_count,
        "false_positive_count": false_positive_count,
        "geometry_score": geometry_score,
        "recognition_score": recognition_score,
        "matching_ms": pipeline_sample.get("analysis_ms", 0.0),
        "analysis_ms": pipeline_sample.get("analysis_ms", 0.0),
        "snapshot_quality_score": pipeline_sample.get("snapshot_quality_score", 0.0),
        "recognition_confidences": confidences,
        "recognition_rejections": pipeline_sample.get("recognition_rejections", 0),
        "candidate_validation_rejections": pipeline_sample.get("candidate_validation_rejections", 0),
        "warnings": []
    }
    
    autotune_session.add_sample(scenario, sample)
    write_autotune_log("sample_collected")
    
    calibration_state = {
        "state": autotune_session.state,
        "last_score": autotune_session.recommendation["score"] if autotune_session.recommendation else None,
        "autotune": autotune_status_payload()
    }
    
    collected = autotune_state_collected_count(scenario)
    log_event(
        f"[WIZARD DIAG] Zebrano probke {scenario} | "
        f"Przed/Po: {collected_before}/{collected} | "
        f"detected={detected_count}, accepted={accepted_count} | reason=collected"
    )
    add_operator_warning(
        f"Wizard: Zebrano probke dla '{scenario}' ({collected}/{autotune_session.samples_per_scenario})"
    )


def handle_control_message(message, camera_session):
    global calibration_state
    global active_tuning_profile
    global pending_background_capture
    global autotune_session
    global autotune_candidate_profiles
    global autotune_quality_report

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
        values = profile_store.load_parameters(message.name)
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
        return

    if message.type == "autotune_start":
        autotune_session = AutotuneSession(
            required_scenarios=(message.scenario,),
            samples_per_scenario=3,
        )
        if message.scenario == "empty":
            background_model.clear()
        autotune_candidate_profiles = generate_candidate_profiles()
        autotune_quality_report = None
        calibration_state = {
            "state": "collecting",
            "last_score": None,
            "autotune": autotune_status_payload(),
        }
        write_autotune_log("stage_started")
        add_operator_warning(f"Autotuning: zbieram probki scenariusza {message.scenario}")
        return

    if message.type == "autotune_calibrate":
        if autotune_session is None or not autotune_session.ready_to_score():
            add_operator_warning("Brak kompletnych probek autotuningu do kalibracji")
            return
        
        autotune_quality_report = score_calibration_wizard_samples(autotune_session.samples)
        
        add_operator_warning(
            f"Wizard: Ocena stanowiska gotowa (score={autotune_quality_report['score']:.3f}, grade={autotune_quality_report['grade']})"
        )
        for issue in autotune_quality_report.get("blocking_issues", []):
            add_operator_warning(f"BLOKADA: {issue}")
        for warning in autotune_quality_report.get("warnings", []):
            add_operator_warning(f"OSTRZEZENIE: {warning}")

        recommendation = update_autotune_recommendation_from_samples()
        write_autotune_log("recommendation_ready", recommendation=recommendation)
        if recommendation is not None:
            add_operator_warning(
                f"Autotuning: rekomendacja gotowa "
                f"(score={recommendation['score']:.3f}, confidence={recommendation['confidence']})"
            )
        return

    if message.type == "autotune_cancel":
        write_autotune_log("cancelled")
        autotune_session = None
        autotune_candidate_profiles = []
        autotune_quality_report = None
        calibration_state = {
            "state": "idle",
            "last_score": None,
            "autotune": autotune_status_payload(),
        }
        add_operator_warning("Anulowano autotuning")
        return

    if message.type == "autotune_apply":
        if autotune_session is None or not autotune_session.recommendation:
            add_operator_warning("Brak rekomendacji autotuningu do zastosowania")
            return
        for param_name, value in autotune_session.recommendation["profile"].items():
            config_session.update(param_name, value)
        config_session.commit_stable()
        calibration_state = {
            "state": "applied",
            "last_score": autotune_session.recommendation["score"],
            "autotune": autotune_status_payload(),
        }
        write_autotune_log("applied", recommendation=autotune_session.recommendation)
        add_operator_warning("Zastosowano rekomendacje autotuningu")
        return

    if message.type == "autotune_save":
        if autotune_session is None or not autotune_session.recommendation:
            add_operator_warning("Brak rekomendacji autotuningu do zapisania")
            return
        profile_store.save_autotune_recommendation(message.name, autotune_session.recommendation)
        active_tuning_profile = message.name
        write_autotune_log(
            "saved",
            recommendation=autotune_session.recommendation,
            profile_name=message.name,
        )
        add_operator_warning(f"Zapisano rekomendacje autotuningu jako profil {message.name}")
        return

    if message.type == "background_capture":
        pending_background_capture = True
        add_operator_warning("Zlecono przechwycenie pustej maty z nastepnej klatki")
        return

    if message.type == "background_clear":
        background_model.clear()
        add_operator_warning("Wyczyszczono model pustej maty")
        return

    if message.type == "studio_set_recording_dir":
        from tarotvision.status.path_validator import validate_recording_path
        valid, msg = validate_recording_path(message.path)
        status_store.update_studio_state(
            recording_dir_status={
                "valid": valid,
                "message": msg,
                "path": message.path
            }
        )
        add_operator_warning(f"Studio: katalog zapisu zweryfikowany ({'OK' if valid else 'BLAD'}): {msg}")
        return

    if message.type == "studio_start_recording":
        status_store.update_studio_state(
            recording_state="recording",
            recording_id=message.recording_id,
            elapsed_ms=0,
            dropped_frames=0
        )
        add_operator_warning(f"Studio: Rozpoczeto nagrywanie, ID: {message.recording_id}")
        return

    if message.type == "studio_stop_recording":
        status_store.update_studio_state(
            recording_state="idle",
            recording_id=None,
            elapsed_ms=0,
            dropped_frames=0
        )
        add_operator_warning("Studio: Zatrzymano i zapisano nagrywanie w przegladarce")
        return

    if message.type == "studio_update_recording_status":
        status_store.update_studio_state(
            recording_state=message.recording_state,
            recording_id=message.recording_id,
            elapsed_ms=message.elapsed_ms,
            dropped_frames=message.dropped_frames
        )
        return

    if message.type == "studio_set_director_scene":
        status_store.update_studio_state(director_scene=message.scene)
        add_operator_warning(f"Studio: Zmieniono scene rezysera na: {message.scene}")
        return

    if message.type == "studio_set_audio_volume":
        status_store.update_studio_state(
            audio_channels={message.channel: {"volume": message.volume}}
        )
        add_operator_warning(f"Studio: Zmieniono glosnosc kanalu {message.channel} na {int(message.volume * 100)}%")
        return

    if message.type == "studio_set_audio_mute":
        status_store.update_studio_state(
            audio_channels={message.channel: {"muted": message.muted}}
        )
        add_operator_warning(f"Studio: {'Wyciszono' if message.muted else 'Wlaczono dzwiek'} dla kanalu {message.channel}")
        return

    if message.type == "studio_update_audio_peak":
        status_store.update_studio_state(audio_peak_db=message.peak_db)
        return

    if message.type == "studio_set_director_mode":
        status_store.update_studio_state(director_mode=message.mode)
        add_operator_warning(f"Studio: Zmieniono tryb rezysera na: {message.mode}")
        return

    if message.type == "studio_save_timeline":
        import os
        current_status = status_store.get_status()
        dir_status = current_status.get("studio", {}).get("recording_dir_status", {})

        base_dir = "./recordings"
        if dir_status and dir_status.get("valid"):
            base_dir = dir_status.get("path", "./recordings")

        rec_id = message.recording_id
        safe_rec_id = "".join(c for c in rec_id if c.isalnum() or c in "-_")
        if not safe_rec_id:
            safe_rec_id = "unknown_rec"

        filename = f"{safe_rec_id}_timeline.json"
        target_dir = os.path.abspath(base_dir)
        target_path = os.path.abspath(os.path.join(target_dir, filename))

        if os.path.commonpath([target_dir, target_path]) != target_dir:
            add_operator_warning("Studio: Zablokowano probe zapisu timeline poza dozwolonym katalogiem")
            return

        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump({
                    "recording_id": message.recording_id,
                    "markers": message.markers
                }, f, indent=2, ensure_ascii=False)
            add_operator_warning(f"Studio: Zapisano timeline dla nagrania {message.recording_id} na serwerze")
        except Exception as e:
            add_operator_warning(f"Studio: Blad zapisu timeline na serwerze: {str(e)}")
        return

    if message.type == "studio_set_active_decks":
        try:
            with open(decks_manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            manifest_decks = manifest_data.get("decks", [])
            valid_ids = {d.get("id") for d in manifest_decks}

            for deck_id in message.active_decks:
                if deck_id not in valid_ids:
                    add_operator_warning(f"Studio: Blad zmiany talii. Talia {deck_id} nie istnieje w manifeście!")
                    return

            active_data = {
                "version": 1,
                "active_decks": message.active_decks
            }
            with open(active_decks_path, "w", encoding="utf-8") as f:
                json.dump(active_data, f, indent=2, ensure_ascii=False)

            load_reference_cards(message.active_decks)
            status_store.update_active_decks(message.active_decks)
            add_operator_warning(f"Studio: Pomyslnie wdrożono aktywne talie: {message.active_decks} (Hot-Reload OK)")
        except Exception as e:
            add_operator_warning(f"Studio: Blad wdrożenia aktywnych talii: {str(e)}")
        return


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
if os.environ.get("TAROTVISION_TEST_MODE") != "1":
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()

if os.environ.get("TAROTVISION_TEST_MODE") != "1":
    preview_port = int(os.environ.get("TAROTVISION_PREVIEW_PORT", "8766"))
    try:
        start_preview_server(frame_stream, port=preview_port)
        log_event(f"[PREVIEW] Browser preview MJPEG: http://localhost:{preview_port}/video_feed.mjpg")
    except OSError as exc:
        log_event(f"[PREVIEW] Nie uruchomiono browser preview na porcie {preview_port}: {exc}")


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
reference_cards = {}
active_decks_path = os.path.join(PROJECT_ROOT, "app_ar", "public", "active_decks.json")
decks_manifest_path = os.path.join(PROJECT_ROOT, "app_ar", "public", "decks_manifest.json")

def load_reference_cards(active_ids=None):
    """Wczytuje cyfrowe wzorce kart dla aktywnych talii sesji pod lockiem."""
    global reference_cards
    result = load_active_reference_cards(
        project_root=PROJECT_ROOT,
        manifest_path=decks_manifest_path,
        active_decks_path=active_decks_path,
        fallback_deck_id=DECK_NAME,
        orb=orb,
        clahe=clahe,
        active_ids=active_ids,
        fallback_cv_path=CV_ASSETS_DIR,
    )
    reference_cards.clear()
    reference_cards.update(result.cards)

    if not reference_cards:
        log_event("[BLAD] Nie zaladowano zadnych wzorcow CV dla aktywnych talii.")
        exit(1)

    log_event(
        f"[OK] Zaladowano talie aktywne: {result.loaded_deck_ids}; "
        f"wzorce={len(reference_cards)}, pominiete={len(result.skipped_files)}"
    )
    for skipped in result.skipped_files[:10]:
        log_event(f"[OSTRZEZENIE] Pominieto nieczytelny wzorzec CV: {skipped}")

# Pierwsze wczytanie przy starcie systemu
load_reference_cards()
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


snapshot_analyzer = SnapshotAnalyzer(
    recognize_crop=recognize_snapshot_crop,
    background_model=background_model,
    find_quads_with_debug=lambda frame: find_card_quads_multi_profile(
        frame,
        background_model=background_model,
    ),
)

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
    runtime_profile=RUNTIME_PROFILE,
    autotune_sample_recorder=record_autotune_sample_from_snapshot
)
snapshot_pipeline.snapshot_sample_count = SNAPSHOT_SAMPLE_COUNT
snapshot_pipeline.snapshot_sample_interval_ms = SNAPSHOT_SAMPLE_INTERVAL_MS

# 3. Inicjalizacja Kamery — jawnie ustawiamy 720p (1280x720) dla wiecej cech ORB z wiekszej odleglosci
if os.environ.get("TAROTVISION_TEST_MODE") != "1":
    log_event("[KAMERA] Uruchamianie kamery... (Wcisnij 'q' by zamknac, cyfry '0'-'9' by przelaczac kamery w locie!)")
    if not camera_session.open(0):
        log_event("[OSTRZEZENIE] Brak kamery pod indeksem 0. Wcisnij np. 1 lub 2 by zmienic.")

    frame_width, frame_height = camera_session.frame_width, camera_session.frame_height
    log_event(f"[KAMERA] Rozdzielczosc: {frame_width}x{frame_height}")

motion_detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)

# Petla glowna (Live feed)
while True:
    if os.environ.get("TAROTVISION_TEST_MODE") == "1":
        break
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

        opencv_preview.show(display_frame)

        # Aktualizujemy status o braku kamery
        metrics_snapshot = runtime_metrics.snapshot()
        runtime_snapshot = {
            "profile": RUNTIME_PROFILE,
            "camera_index": camera_session.camera_index,
            "capture_width": frame_width,
            "capture_height": frame_height,
            "camera_focus_locked": CAMERA_FOCUS_LOCKED,
            "camera_exposure_locked": CAMERA_EXPOSURE_LOCKED,
            "schedule_mode": "no_camera"
        }
        status_store.update_cv_state(
            cards=[],
            metrics=metrics_snapshot,
            runtime=runtime_snapshot,
            operator=build_operator_snapshot(),
            warnings=list(operator_warnings[-8:]) + ["Brak sygnalu wideo z kamery!"]
        )

        key_action = opencv_preview.handle_keyboard(camera_session)
        if key_action == "quit":
            break
        elif key_action == "switch":
            frame_width, frame_height = camera_session.frame_width, camera_session.frame_height
            log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")
        continue

    # Aktualizujemy rozdzielczosc dynamicznie (na wypadek zmiany kamery)
    frame_height, frame_width = frame.shape[:2]
    frame_stream.update(frame)

    if pending_background_capture:
        capture_frame = table_calibration.warp_frame(frame) if table_calibration.calibrated else frame
        if capture_frame is not None:
            background_model.capture(capture_frame)
            add_operator_warning("Przechwycono model pustej maty")
        pending_background_capture = False

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

    if gray_frame is not None:
        motion_result = motion_detector.update(gray_frame)
    else:
        motion_result = motion_detector.update(np.zeros((8, 8), dtype=np.uint8))
    runtime_metrics.add("motion_changed_ratio", motion_result.changed_ratio)


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

camera_session.close()
opencv_preview.close()
