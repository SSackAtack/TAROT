import cv2
import numpy as np
import os
import time

# Ustawienia ścieżek
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CV_ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "biblioteka_talii", "rider-waite-smith", "produkcja", "wzorce_cv"))
STAR_CARD_PATH = os.path.join(CV_ASSETS_DIR, "17_star.jpg")

print("========================================")
print("[DIAGNOSTYKA] TEST DOPASOWANIA CECH (ORB)")
print("========================================")

# 1. Inicjalizacja detektora ORB
orb = cv2.ORB_create(nfeatures=3000) # Zwiększamy liczbę punktów do diagnozy
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

# 2. Wczytanie wzorca cyfrowego karty The Star
ref_img = cv2.imread(STAR_CARD_PATH, cv2.IMREAD_GRAYSCALE)
if ref_img is None:
    print(f"[BŁĄD] Nie można załadować wzorca: {STAR_CARD_PATH}")
    exit(1)

kp_ref, des_ref = orb.detectAndCompute(ref_img, None)
print(f"[OK] Załadowano wzorzec The Star. Punkty kluczowe wzorca: {len(kp_ref)}")

# 3. Przechwycenie obrazu z kamery (Indeks 0, MSMF)
print("[KAMERA] Otwieranie kamery (Indeks 0)...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[BŁĄD] Nie można otworzyć kamery o indeksie 0!")
    exit(1)

# Czekamy na ustabilizowanie ekspozycji kamery
time.sleep(2.0)

# Pobieramy kilka klatek, aby wyczyścić bufor wideo
for _ in range(10):
    ret, frame = cap.read()

if not ret or frame is None:
    print("[BŁĄD] Nie udało się odczytać klatki z kamery!")
    cap.release()
    exit(1)

cap.release()
print("[OK] Klatka przechwycona pomyślnie.")

# Zapisujemy surową klatkę do celów debugowania
debug_frame_path = os.path.join(BASE_DIR, "debug_frame.jpg")
cv2.imwrite(debug_frame_path, frame)
print(f"[INFO] Zapisano klatkę z kamery do: {debug_frame_path}")

# Konwersja do szarości
gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
kp_frame, des_frame = orb.detectAndCompute(gray_frame, None)
print(f"[INFO] Punkty kluczowe wykryte na klatce z kamery: {len(kp_frame) if kp_frame is not None else 0}")

if des_frame is None or len(des_frame) == 0:
    print("[BŁĄD] Brak wykrytych punktów kluczowych na obrazie z kamery! Czy obiektyw jest odsłonięty i jest jasne światło?")
    exit(1)

# 4. Porównywanie przy różnych progach Lowe's Ratio Test
ratios = [0.75, 0.80, 0.85, 0.90]
matches = bf.knnMatch(des_ref, des_frame, k=2)

print("\n--- Analiza dopasowań dla różnych progów Ratio ---")
for r in ratios:
    good_matches = []
    for m, n in matches:
        if m.distance < r * n.distance:
            good_matches.append(m)
    print(f"Próg Ratio {r:.2f}: {len(good_matches)} dopasowań")
    
    # Dla aktualnie wybranego progu w programie (0.75), stwórzmy wizualizację
    if abs(r - 0.75) < 0.01:
        # Rysujemy linie dopasowania
        matching_img = cv2.drawMatches(
            ref_img, kp_ref, 
            gray_frame, kp_frame, 
            good_matches[:50], None, 
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )
        match_result_path = os.path.join(BASE_DIR, "matching_result.jpg")
        cv2.imwrite(match_result_path, matching_img)
        print(f"[INFO] Zapisano obraz dopasowań (top 50) do: {match_result_path}")

print("========================================")
