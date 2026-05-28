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

# Konfiguracja
CV_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", "rider-waite-smith", "produkcja", "wzorce_cv"))
MIN_MATCH_COUNT = 18   # Obnizony do 18 — filtry geometryczne (homografia + validate_quad + aspect ratio + inlier ratio) skutecznie eliminuja szum
RATIO_THRESH = 0.79    # Zaostrzone z 0.83 do 0.79 dla czystosci dopasowan cech ORB
MIN_INLIER_RATIO = 0.3 # Minimalna proporcja inlierow w homografii RANSAC (odrzuca niestabilne dopasowania)
CARD_ASPECT_RATIO = 1.72  # Standardowy stosunek wysokosc/szerokosc kart tarota RWS (~1.72)
CARD_ASPECT_TOLERANCE = 0.65  # Tolerancja odchylenia aspect ratio (poluzowana — perspektywa kamery silnie znieksztalca proporcje)
EMA_ALPHA = 0.4        # Wspolczynnik wygladzania Exponential Moving Average dla pozycji (0 = pelne wygladzanie, 1 = brak)

# System dwufazowy "Zlap i Zamroz" — eliminuje mikro-jitter statycznych kart
LOCK_AFTER_FRAMES = 8      # Klatki stabilnej detekcji zanim pozycja zostanie zamrozona
LOCK_DEAD_ZONE_POS = 1.5   # Minimalny ruch pozycji (w jednostkach sceny) zeby odblokowac karte
LOCK_DEAD_ZONE_ANGLE = 0.3 # Minimalny ruch kata (w radianach, ~17 stopni) zeby odblokowac karte

# Stan wspoldzielony miedzy watkiem wizyjnym (CV) a watkiem serwera WebSocket
status_lock = threading.Lock()
current_status = {
    "detected": False,
    "cards": []
}

# Zestaw polaczonych klientow
connected_clients = set()

async def handler(websocket):
    print(f"[WEBSOCKET] Polaczono klienta: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        # Wyslij natychmiast obecny stan (bezpieczna gleboka kopia)
        with status_lock:
            state = copy.deepcopy(current_status)
        await websocket.send(json.dumps(state))
        
        # Utrzymujemy polaczenie otwarte
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[WEBSOCKET] Rozlaczono klienta: {websocket.remote_address}")

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
        print("[WEBSOCKET] Serwer WebSocket dziala pod adresem ws://localhost:8765")
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

print("========================================")
print("[TAROT VISION] Computer Vision Module v2.0 (Audited)")
print("========================================")

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
print(f"[INFO] Ladowanie cyfrowych wzorcow z {CV_ASSETS_DIR}")
reference_cards = {}
file_paths = glob.glob(os.path.join(CV_ASSETS_DIR, "*.jpg"))

if not file_paths:
    print("[BLAD] Nie znaleziono zadnych plikow wzorcow .jpg w katalogu!")
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

print(f"[OK] Zaladowano {len(reference_cards)} wzorcow do pamieci!")

# 3. Inicjalizacja Kamery — jawnie ustawiamy 720p (1280x720) dla wiecej cech ORB z wiekszej odleglosci
print("[KAMERA] Uruchamianie kamery... (Wcisnij 'q' by zamknac, cyfry '0'-'9' by przelaczac kamery w locie!)")
camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("[OSTRZEZENIE] Brak kamery pod indeksem 0. Wcisnij np. 1 lub 2 by zmienic.")

# Wymuszamy 720p — wiecej pikseli per karta = wiecej cech ORB = lepsza detekcja z dystansu
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
print(f"[KAMERA] Rozdzielczosc: {frame_width}x{frame_height}")

# Parametry stabilizacji detekcji (debouncing) dla wielu kart
debounce_state = {}
DEBOUNCE_FRAMES = 3  # Karta musi byc stabilnie wykryta przez 3 klatki z rzedu
LOSS_FRAMES = 8      # Karta musi zniknac na 8 klatek z rzedu, aby zostala schowana

# Zoptymalizowana kolejka round-robin do sprawdzania nieaktywnych kart
inactive_index = 0
prev_time = time.time()  # Do pomiaru FPS

# Petla glowna (Live feed)
while True:
    ret, frame = cap.read()
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
    
    # 4. Wykrywamy punkty kluczowe w obecnej klatce
    if gray_frame is not None:
        kp_frame, des_frame = orb.detectAndCompute(gray_frame, None)
    else:
        des_frame = None
    
    # Slownik przechowujacy wykryte w tej klatce karty i ich dane
    detected_this_frame = {}
    
    # Określamy aktywne karty w tym momencie (faza DETECTING lub LOCKED)
    active_names = []
    for name, state in debounce_state.items():
        if state.get("stable_count", 0) > 0:
            active_names.append(name)
            
    # Pozostałe, nieaktywne karty
    all_card_names = list(reference_cards.keys())
    inactive_names = [n for n in all_card_names if n not in active_names]
    
    # Sprawdzamy czy w ogole cokolwiek na kamerze ma ostre krawedzie
    if des_frame is not None and len(des_frame) > MIN_MATCH_COUNT:
        # Zoptymalizowany round-robin dla kart nieaktywnych (sprawdzamy tylko podzbiór 4 kart per frame)
        NUM_INACTIVE_PER_FRAME = 4
        inactive_to_check = []
        if inactive_names:
            if inactive_index >= len(inactive_names):
                inactive_index = 0
            for i in range(min(NUM_INACTIVE_PER_FRAME, len(inactive_names))):
                idx = (inactive_index + i) % len(inactive_names)
                inactive_to_check.append(inactive_names[idx])
            inactive_index = (inactive_index + len(inactive_to_check)) % len(inactive_names)
            
        # Łączymy zbiory: zawsze sprawdzamy wszystkie aktywne + rotujący podzbiór nieaktywnych
        cards_to_check = list(set(active_names + inactive_to_check))
        
        # 5. Iterujemy po wybranych kartach i szukamy spelniajacych prog
        for name in cards_to_check:
            ref_data = reference_cards[name]
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
                    if m.distance < RATIO_THRESH * n.distance:
                        good_matches.append(m)
                    
            if len(good_matches) >= MIN_MATCH_COUNT:
                # Karta ma duzo punktow! Liczymy homografie i sprawdzamy geometrie
                ref_kp = ref_data["keypoints"]
                src_pts = np.float32([ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None and mask is not None:
                    # Sprawdzamy proporcje inlierow (czy homografia jest stabilna)
                    inlier_ratio = np.sum(mask) / len(mask)
                    if inlier_ratio < MIN_INLIER_RATIO:
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

                        # Karta przeszla wszystkie filtry! Zapisujemy dane detekcji
                        detected_this_frame[name] = {
                            "count": len(good_matches),
                            "dst": dst,
                            "x": pos_x,
                            "y": pos_y,
                            "angle": angle
                        }
                
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
                
                debounce_state[name]["last_x"] = EMA_ALPHA * new_x + (1 - EMA_ALPHA) * old_x
                debounce_state[name]["last_y"] = EMA_ALPHA * new_y + (1 - EMA_ALPHA) * old_y
                debounce_state[name]["last_angle"] = EMA_ALPHA * new_angle + (1 - EMA_ALPHA) * old_angle
                
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
                
                if dx > LOCK_DEAD_ZONE_POS or dy > LOCK_DEAD_ZONE_POS or d_angle > LOCK_DEAD_ZONE_ANGLE:
                    # Karta sie ruszyla! Odblokowujemy i wracamy do fazy wykrywania
                    debounce_state[name]["phase"] = "DETECTING"
                    debounce_state[name]["stable_count"] = 0
                    debounce_state[name]["last_x"] = new_x
                    debounce_state[name]["last_y"] = new_y
                    debounce_state[name]["last_angle"] = new_angle
                else:
                    # Karta statyczna — uzywamy zamrozonej pozycji (ZERO jitteru)
                    debounce_state[name]["last_x"] = locked_x
                    debounce_state[name]["last_y"] = locked_y
                    debounce_state[name]["last_angle"] = locked_angle
        else:
            debounce_state[name]["loss_count"] += 1
            if debounce_state[name]["loss_count"] >= LOSS_FRAMES:
                debounce_state[name]["stable_count"] = 0
                debounce_state[name]["phase"] = "DETECTING"  # Reset do fazy wykrywania
                
        # Karta jest uznana za aktywnie wykryta, jesli osiagnela prog stabilnosci
        if debounce_state[name]["stable_count"] >= DEBOUNCE_FRAMES:
            active_detected_cards.append({
                "name": name,
                "x": round(debounce_state[name].get("last_x", 0.0), 4),
                "y": round(debounce_state[name].get("last_y", 0.0), 4),
                "angle": round(debounce_state[name].get("last_angle", 0.0), 4)
            })
            
    # Aktualizujemy wspoldzielony stan (bezpieczna gleboka kopia wewnatrz locka)
    with status_lock:
        current_status["detected"] = len(active_detected_cards) > 0
        current_status["cards"] = active_detected_cards

    # 7. Rysowanie ramek — kolor zalezy od fazy: ZIELONA = DETECTING, NIEBIESKA = LOCKED
    for name, data in detected_this_frame.items():
        dst = data["dst"]
        match_count = data["count"]
        
        # Sprawdzamy faze karty
        phase = debounce_state.get(name, {}).get("phase", "DETECTING")
        
        if phase == "LOCKED":
            box_color = (255, 180, 0)   # Niebiesko-zlota (BGR) — zamrozona
            text_color = (255, 180, 0)
            status_text = "LOCKED"
        else:
            box_color = (0, 255, 0)     # Zielona — aktywne wykrywanie
            text_color = (0, 0, 255)
            status_text = "DETECTING"
        
        display_frame = cv2.polylines(display_frame, [np.int32(dst)], True, box_color, 3, cv2.LINE_AA)
        
        top_y = min([pt[0][1] for pt in dst])
        top_x = min([pt[0][0] for pt in dst])
        
        cv2.putText(display_frame, f"{name.upper()} ({match_count} pkt) [{status_text}]", 
                    (int(top_x), int(top_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, text_color, 2, cv2.LINE_AA)

    # Obliczanie i rysowanie FPS na żywo (pomaga w weryfikacji wydajności)
    current_time = time.time()
    time_diff = current_time - prev_time
    fps = 1.0 / time_diff if time_diff > 0 else 0.0
    prev_time = current_time
    
    cv2.putText(display_frame, f"FPS: {fps:.1f}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(display_frame, f"Sledzone: {len(active_names)} | Pula: {len(inactive_names)}", 
                (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.imshow('TarotVision - AI Detection (Wcisnij Q by wyjsc)', display_frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif ord('0') <= key <= ord('5'):
        new_index = key - ord('0')
        print(f"Zmiana kamery na indeks: {new_index}")
        cap.release()
        cap = cv2.VideoCapture(new_index)
        camera_index = new_index
        # Aktualizacja rozdzielczosci po zmianie kamery
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        print(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")

cap.release()
cv2.destroyAllWindows()
