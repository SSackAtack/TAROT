import cv2
import numpy as np
import glob
import os
import asyncio
import threading
import json
import websockets
import math

# Konfiguracja
CV_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", "rider-waite-smith", "produkcja", "wzorce_cv"))
MIN_MATCH_COUNT = 38 # Skorygowane z 45 do 38 w celu wykrywania mniej detalicznych kart (filtr geometryczny wciąż chroni nas przed szumem)
RATIO_THRESH = 0.79  # Zaostrzone z 0.83 do 0.79 dla znacznie wyższej czystości dopasowań cech ORB

# Stan współdzielony między wątkiem wizyjnym (CV) a wątkiem serwera WebSocket
status_lock = threading.Lock()
current_status = {
    "detected": False,
    "cards": []
}

# Zestaw połączonych klientów
connected_clients = set()

async def handler(websocket):
    print(f"[WEBSOCKET] Połączono klienta: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        # Wyślij natychmiast obecny stan
        with status_lock:
            state = current_status.copy()
        await websocket.send(json.dumps(state))
        
        # Utrzymujemy połączenie otwarte
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"[WEBSOCKET] Rozłączono klienta: {websocket.remote_address}")

async def broadcast_status():
    last_sent = None
    while True:
        if connected_clients:
            with status_lock:
                state_to_send = current_status.copy()
            
            # Wysyłamy tylko przy zmianie stanu
            if state_to_send != last_sent:
                message = json.dumps(state_to_send)
                websockets_tasks = [client.send(message) for client in connected_clients]
                if websockets_tasks:
                    await asyncio.gather(*websockets_tasks, return_exceptions=True)
                last_sent = state_to_send
        await asyncio.sleep(0.05) # Odpytywanie co 50ms (20 FPS)

async def main_ws():
    async with websockets.serve(handler, "localhost", 8765):
        print("[WEBSOCKET] Serwer WebSocket działa pod adresem ws://localhost:8765")
        await broadcast_status()

def start_websocket_server():
    asyncio.run(main_ws())

# Uruchomienie serwera WebSocket w tle
ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
ws_thread.start()

def validate_quadrilateral(dst):
    # dst ma kształt (4, 1, 2)
    p0 = dst[0][0] # Górny-lewy (TL)
    p1 = dst[1][0] # Dolny-lewy (BL)
    p2 = dst[2][0] # Dolny-prawy (BR)
    p3 = dst[3][0] # Górny-prawy (TR)
    
    # 1. Obliczamy długości czterech boków
    side_left = np.linalg.norm(p1 - p0)
    side_bottom = np.linalg.norm(p2 - p1)
    side_right = np.linalg.norm(p3 - p2)
    side_top = np.linalg.norm(p0 - p3)
    
    # Zabezpieczenie przed mikroskopijnymi szumami
    if min(side_left, side_bottom, side_right, side_top) < 25.0:
        return False
        
    # 2. Sprawdzamy stosunek długości naprzeciwległych boków (lewy vs prawy, góra vs dół)
    # W rzucie perspektywicznym dopuszczamy drobne zwężenia, ale nie drastyczne kliny/trójkąty
    ratio_lr = side_left / side_right if side_left > side_right else side_right / side_left
    ratio_tb = side_top / side_bottom if side_top > side_bottom else side_bottom / side_top
    
    if ratio_lr > 1.95 or ratio_tb > 1.95:
        return False
        
    # 3. Sprawdzamy kąty wewnętrzne przy użyciu cosinusów (szukamy zbliżonych do 90 stopni)
    def get_cos_angle(a, b, c):
        ba = a - b
        bc = c - b
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba == 0 or norm_bc == 0:
            return 1.0
        return np.dot(ba, bc) / (norm_ba * norm_bc)
        
    cos_0 = abs(get_cos_angle(p3, p0, p1)) # Kąt w p0
    cos_1 = abs(get_cos_angle(p0, p1, p2)) # Kąt w p1
    cos_2 = abs(get_cos_angle(p1, p2, p3)) # Kąt w p2
    cos_3 = abs(get_cos_angle(p2, p3, p0)) # Kąt w p3
    
    # Próg 0.82 odrzuca kąty ostrzejsze niż ~35° oraz rozwarte powyżej ~145°
    MAX_COS = 0.82
    if cos_0 > MAX_COS or cos_1 > MAX_COS or cos_2 > MAX_COS or cos_3 > MAX_COS:
        return False
        
    return True

print("========================================")
print("[TAROT VISION] Computer Vision Module (WebSocket Ready)")
print("========================================")

# 1. Inicjalizacja detektora ORB (szybki i darmowy detektor cech)
# Ustawiamy maksymalną liczbę punktów na wysoki poziom, karty tarota są bardzo detaliczne
orb = cv2.ORB_create(nfeatures=2000)

# Brute-Force Matcher do porównywania deskryptorów Hamminga
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

# 2. Ładowanie szablonów (naszych wygenerowanych kart JPG)
print(f"[INFO] Ładowanie cyfrowych wzorców z {CV_ASSETS_DIR}")
reference_cards = {}
file_paths = glob.glob(os.path.join(CV_ASSETS_DIR, "*.jpg"))

if not file_paths:
    print("[BŁĄD] Nie znaleziono żadnych plików wzorców .jpg w katalogu!")
    exit(1)

for file_path in file_paths:
    card_name = os.path.basename(file_path).replace(".jpg", "")
    
    # Wczytywanie w odcieniach szarości (kolor nie ma znaczenia w geometrii kształtów)
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        continue
        
    # Wyliczamy od razu kluczowe cechy dla karty by nie powtarzać tego w pętli
    kp, des = orb.detectAndCompute(img, None)
    
    # Zapisujemy do pamięci referencyjnej
    reference_cards[card_name] = {
        "image": img,
        "keypoints": kp,
        "descriptors": des
    }

print(f"[OK] Załadowano {len(reference_cards)} wzorców do pamięci!")

# 3. Inicjalizacja Kamery (z DirectShow dla ominięcia błędów Windows MSMF)
print("[KAMERA] Uruchamianie kamery... (Wciśnij 'q' by zamknąć, cyfry '0'-'9' by przełączać kamery w locie!)")
camera_index = 0
cap = cv2.VideoCapture(camera_index) # Domyślny backend (MSMF) po naprawie kabla

if not cap.isOpened():
    print("[OSTRZEŻENIE] Brak kamery pod indeksem 0. Wciśnij np. 1 lub 2 by zmienić.")

# Parametry stabilizacji detekcji (debouncing) dla wielu kart
debounce_state = {}
DEBOUNCE_FRAMES = 3  # Karta musi być stabilnie wykryta przez 3 klatki z rzędu, aby zaktualizować WebSocket
LOSS_FRAMES = 8      # Karta musi zniknąć na 8 klatek z rzędu, aby została schowana

# Pętla główna (Live feed)
while True:
    ret, frame = cap.read()
    if not ret:
        # Zastępcze okno ostrzegawcze by użytkownik mógł zmieniać klawisze
        display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(display_frame, f"Brak wideo pod portem: {camera_index}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(display_frame, f"Wcisnij inna cyfre (0-5) by szukac.", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        gray_frame = None
    else:
        # Kopiujemy klatkę do modyfikacji wizualnych i robimy kopię czarno-białą do analizy
        display_frame = frame.copy()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Zastosowanie CLAHE w celu dynamicznego wyrównania oświetlenia i redukcji odblasków/cieni
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_frame = clahe.apply(gray_frame)
    
    # 4. Wykrywamy punkty kluczowe w obecnej klatce (to co widzi kamera)
    if gray_frame is not None:
        kp_frame, des_frame = orb.detectAndCompute(gray_frame, None)
    else:
        des_frame = None
    
    # Słownik przechowujący wykryte w tej klatce karty i ich dane
    detected_this_frame = {}
    
    # Sprawdzamy czy w ogóle cokolwiek na kamerze ma ostre krawędzie
    if des_frame is not None and len(des_frame) > MIN_MATCH_COUNT:
        
        # 5. Iterujemy po wszystkich 22 kartach w pamięci i szukamy wszystkich spełniających próg
        for name, ref_data in reference_cards.items():
            des_ref = ref_data["descriptors"]
            if des_ref is None: continue
                
            # Porównujemy (knnMatcher z k=2 szuka dwóch najlepszych dopasowań dla każdego punktu)
            matches = bf.knnMatch(des_ref, des_frame, k=2)
            
            good_matches = []
            # Lowe's ratio test (odrzuca niepewne i błędne dopasowania szumu)
            for m, n in matches:
                if m.distance < RATIO_THRESH * n.distance:
                    good_matches.append(m)
                    
            if len(good_matches) >= MIN_MATCH_COUNT:
                # Karta ma dużo punktów! Teraz liczymy homografię i sprawdzamy geometrię
                ref_kp = ref_data["keypoints"]
                src_pts = np.float32([ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    h, w = ref_data["image"].shape
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # A. Sprawdzamy wypukłość (czy linie ramki się nie krzyżują, co zapobiega pociętym ekranom)
                    is_convex = cv2.isContourConvex(np.int32(dst))
                    
                    # B. Sprawdzamy pole powierzchni czworokąta
                    area = cv2.contourArea(dst)
                    
                    # C. Rozsądny rozmiar karty na ekranie 640x480 (między 3500 a 280000 pikseli)
                    is_reasonable_size = (3500 <= area <= 280000)
                    
                    if is_convex and is_reasonable_size and validate_quadrilateral(dst):
                        # 1. Obliczamy geometryczny środek (centroid) karty na obrazie w pikselach
                        cx = float(np.mean(dst[:, 0, 0]))
                        cy = float(np.mean(dst[:, 0, 1]))
                        
                        # 2. Przeliczamy i normalizujemy współrzędne do wirtualnego świata Three.js
                        pos_x = float((cx / 640.0 * 2.0 - 1.0) * 8.5)
                        pos_y = float((1.0 - (cy / 480.0) * 2.0) * 4.0 + 4.5)
                        
                        # 3. Obliczamy kąt obrotu karty na biurku na podstawie wektora górnych rogów
                        x0, y0 = dst[0][0][0], dst[0][0][1] # Lewy górny róg
                        x3, y3 = dst[3][0][0], dst[3][0][1] # Prawy górny róg
                        angle = -float(math.atan2(y3 - y0, x3 - x0))

                        # Karta przeszła wszystkie filtry geometryczne! Zapisujemy dane detekcji i pozycje
                        detected_this_frame[name] = {
                            "count": len(good_matches),
                            "dst": dst,
                            "x": pos_x,
                            "y": pos_y,
                            "angle": angle
                        }
                
    # 6. Stabilizacja detekcji dla każdej z 22 kart (Debouncing)
    active_detected_cards = []
    
    for name in reference_cards.keys():
        # Inicjalizacja stanu debouncingu dla danej karty, jeśli nie istnieje
        if name not in debounce_state:
            debounce_state[name] = {"stable_count": 0, "loss_count": 0}
            
        if name in detected_this_frame:
            # Karta wykryta w tej klatce - uaktualniamy jej współrzędne w pamięci podręcznej debouncingu
            debounce_state[name]["stable_count"] += 1
            debounce_state[name]["loss_count"] = 0
            debounce_state[name]["last_x"] = detected_this_frame[name]["x"]
            debounce_state[name]["last_y"] = detected_this_frame[name]["y"]
            debounce_state[name]["last_angle"] = detected_this_frame[name]["angle"]
        else:
            # Brak wykrycia karty w tej klatce
            debounce_state[name]["loss_count"] += 1
            if debounce_state[name]["loss_count"] >= LOSS_FRAMES:
                debounce_state[name]["stable_count"] = 0
                
        # Karta jest uznana za aktywnie wykrytą, jeśli osiągnęła próg stabilności
        if debounce_state[name]["stable_count"] >= DEBOUNCE_FRAMES:
            active_detected_cards.append({
                "name": name,
                "x": debounce_state[name].get("last_x", 0.0),
                "y": debounce_state[name].get("last_y", 4.5),
                "angle": debounce_state[name].get("last_angle", 0.0)
            })
            
    # Aktualizujemy współdzielony stan dla serwera WebSocket
    with status_lock:
        current_status["detected"] = len(active_detected_cards) > 0
        current_status["cards"] = active_detected_cards

    # 7. Rysowanie ramek i nazw dla wszystkich stabilnych, zatwierdzonych kart
    for name, data in detected_this_frame.items():
        dst = data["dst"]
        match_count = data["count"]
        
        # Rysowanie zielonego bounding boxa (Polylines po 4 rogach)
        display_frame = cv2.polylines(display_frame, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
        
        # Obliczanie najwyższego punktu żeby ładnie nałożyć nazwę
        top_y = min([pt[0][1] for pt in dst])
        top_x = min([pt[0][0] for pt in dst])
        
        # Wypisywanie nazwy karty wielką czerwoną czcionką
        cv2.putText(display_frame, f"KARTA: {name.upper()} ({match_count} pkt)", 
                    (int(top_x), int(top_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (0, 0, 255), 2, cv2.LINE_AA)

    # Pokazujemy klatkę wynikową na ekranie
    cv2.imshow('TarotVision - AI Detection (Wcisnij Q by wyjsc)', display_frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif ord('0') <= key <= ord('5'):
        new_index = key - ord('0')
        print(f"🔄 Zmiana kamery na indeks: {new_index}")
        cap.release()
        cap = cv2.VideoCapture(new_index)
        camera_index = new_index

cap.release()
cv2.destroyAllWindows()
