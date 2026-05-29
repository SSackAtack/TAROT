import cv2
import numpy as np
import os
import sys

# Znormalizowana rozdzielczość docelowa kart (szerokość x wysokość)
TARGET_WIDTH = 600
TARGET_HEIGHT = 1032  # Zachowuje aspect ratio ~1.72

def process_scanned_sheet(sheet_path, output_dir, start_index=1, background_dark=True):
    """
    Wczytuje skan całego arkusza, wykrywa prostokąty kart, 
    prostuje je (deskewing), kadruje i zapisuje jako osobne pliki.
    """
    if not os.path.exists(sheet_path):
        print(f"[BŁĄD] Plik skanu nie istnieje: {sheet_path}")
        return start_index

    # Wczytanie obrazu w wysokiej rozdzielczości
    img = cv2.imread(sheet_path)
    if img is None:
        print(f"[BŁĄD] Nie można załadować obrazu: {sheet_path}")
        return start_index

    h_sheet, w_sheet = img.shape[:2]
    print(f"\nPrzetwarzam arkusz: {os.path.basename(sheet_path)} ({w_sheet}x{h_sheet} px)...")

    # Konwersja do skali szarości i rozmycie w celu eliminacji szumu
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Progowanie (Thresholding) w zależności od jasności tła
    if background_dark:
        # Ciemne tło (np. skanowanie z czarną podkładką/otwartą pokrywą)
        _, thresh = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY)
    else:
        # Jasne tło (pokrywa zamknięta, białe tło skanera)
        _, thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY_INV)

    # Detekcja konturów
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrowanie konturów pod kątem rozmiaru kart (od 2% do 25% powierzchni arkusza)
    min_area = w_sheet * h_sheet * 0.02
    max_area = w_sheet * h_sheet * 0.25
    
    card_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            card_contours.append(cnt)

    print(f"Wykryto {len(card_contours)} potencjalnych kart na arkuszu.")

    # Sortowanie konturów od góry do dołu, a potem od lewej do prawej
    # (ułatwia to późniejsze nazywanie plików w logicznej kolejności)
    def get_contour_precedence(contour, cols=3):
        box = cv2.boundingRect(contour)
        return (box[1] // 150) * cols + (box[0] // 150)

    card_contours = sorted(card_contours, key=get_contour_precedence)

    saved_count = 0
    for idx, cnt in enumerate(card_contours):
        # Znajdujemy obrócony prostokąt o minimalnej powierzchni (obsługuje lekkie skosy)
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)

        # Szerokość i wysokość obróconego prostokąta
        width = int(rect[1][0])
        height = int(rect[1][1])
        angle = rect[2]

        # OpenCV zwraca kąt obrotu, musimy zidentyfikować orientację (portrait vs landscape)
        if width < height:
            # Prawidłowa orientacja pionowa (portrait)
            src_pts = box.astype("float32")
            # Punkty docelowe
            dst_pts = np.array([
                [0, height - 1],
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1]
            ], dtype="float32")
        else:
            # Karta jest obrócona bokiem (landscape) w prostokącie — korygujemy
            src_pts = box.astype("float32")
            dst_pts = np.array([
                [width - 1, height - 1],
                [0, height - 1],
                [0, 0],
                [width - 1, 0]
            ], dtype="float32")
            width, height = height, width  # zamiana wymiarów na portrait

        # Obliczanie macierzy transformacji perspektywicznej i wyprostowanie
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(img, M, (width, height))

        # Skalowanie do znormalizowanej rozdzielczości docelowej
        resized = cv2.resize(warped, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_CUBIC)

        # Zapis do pliku
        filename = f"card_{start_index + saved_count:02d}.jpg"
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, resized)
        print(f" -> Zapisano wykadrowaną kartę: {filename}")
        saved_count += 1

    return start_index + saved_count

if __name__ == "__main__":
    # Skrypt uruchamiany z parametrami: python process_scans.py <scans_dir> <output_dir>
    scans_dir = sys.argv[1] if len(sys.argv) > 1 else "scans_input"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "scans_output"

    os.makedirs(scans_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("=== AUTOKADROWANIE I PROSTOWANIE SKANÓW (OPENCV) ===")
    print(f"Katalog wejściowy: {scans_dir}")
    print(f"Katalog wyjściowy: {output_dir}")
    print(f"Standard docelowy: {TARGET_WIDTH}x{TARGET_HEIGHT} px (aspect ratio ~1.72)")
    print("="*50)

    # Szukamy plików graficznych w katalogu wejściowym
    extensions = (".jpg", ".jpeg", ".png", ".tiff")
    files = [f for f in os.listdir(scans_dir) if f.lower().endswith(extensions)]

    if not files:
        print(f"\n[INFO] Brak skanów w katalogu '{scans_dir}'.")
        print("Umieść tam pliki skanera (np. scan1.jpg) i uruchom skrypt ponownie.")
        sys.exit(0)

    current_idx = 0
    # Domyślnie zakładamy ciemne tło (zalecane: skanowanie z czarną podkładką na kartach)
    for file in sorted(files):
        sheet_path = os.path.join(scans_dir, file)
        current_idx = process_scanned_sheet(sheet_path, output_dir, start_index=current_idx, background_dark=True)

    print("\n" + "="*50)
    print(f"[SUKCES] Koniec przetwarzania. Wykadrowane karty znajdziesz w katalogu: {output_dir}")
    print("Teraz wystarczy zmienić ich nazwy na właściwe (np. card_01.jpg -> 00_fool.jpg)!")
    print("="*50)
