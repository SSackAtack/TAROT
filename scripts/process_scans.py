import cv2
import numpy as np
import os
import sys
import argparse
import time

# Lista 22 Wielkich Arkanów w kolejności numerycznej
MAJOR_ARCANAS = [
    "00_fool", "01_magician", "02_high_priestess", "03_empress", "04_emperor",
    "05_hierophant", "06_lovers", "07_chariot", "08_strength", "09_hermit",
    "10_wheel_of_fortune", "11_justice", "12_hanged_man", "13_death", "14_temperance",
    "15_devil", "16_tower", "17_star", "18_moon", "19_sun", "20_judgement", "21_world"
]

# Próba importu pywin32 do sprzętowej obsługi skanera na Windowsie
HAS_WIA = False
if sys.platform == "win32":
    try:
        import win32com.client
        HAS_WIA = True
    except ImportError:
        HAS_WIA = False

def order_points(pts):
    """
    Porządkuje 4 punkty wierzchołkowe w stałej kolejności:
    [top-left, top-right, bottom-right, bottom-left]
    """
    rect = np.zeros((4, 2), dtype="float32")
    
    # top-left ma najmniejszą sumę x+y, bottom-right ma największą sumę x+y
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # top-right ma najmniejszą różnicę y-x, bottom-left ma największą różnicę y-x
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def create_rounded_mask(width, height, radius):
    """
    Tworzy 1-kanałową maskę z zaokrąglonymi rogami z wygładzaniem krawędzi (antyaliasing).
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Rysujemy prostokąty krzyżowe wewnętrzne
    cv2.rectangle(mask, (radius, 0), (width - radius, height), 255, -1)
    cv2.rectangle(mask, (0, radius), (width, height - radius), 255, -1)
    
    # Rysujemy 4 koła narożne
    cv2.circle(mask, (radius, radius), radius, 255, -1)
    cv2.circle(mask, (width - radius, radius), radius, 255, -1)
    cv2.circle(mask, (radius, height - radius), radius, 255, -1)
    cv2.circle(mask, (width - radius, height - radius), radius, 255, -1)
    
    # Dodajemy delikatne rozmycie Gaussowskie na masce, aby wygładzić krawędzie
    mask_blurred = cv2.GaussianBlur(mask, (3, 3), 0)
    return mask_blurred

def detect_background_dark(img_gray):
    """
    Automatyczna detekcja jasności tła skanera na podstawie krawędzi arkusza.
    Zwraca True, jeśli tło jest ciemne, False w przeciwnym wypadku.
    """
    h, w = img_gray.shape[:2]
    border_pixels = []
    
    # Pobieramy piksele z krawędzi arkusza (pasek o szerokości 15 pikseli)
    border_pixels.extend(img_gray[0:15, :].flatten())
    border_pixels.extend(img_gray[h-15:h, :].flatten())
    border_pixels.extend(img_gray[:, 0:15].flatten())
    border_pixels.extend(img_gray[:, w-15:w].flatten())
    
    median_val = np.median(border_pixels)
    return median_val < 100

def scan_image_via_wia():
    """
    Uruchamia fizyczne skanowanie za pomocą systemowego okna dialogowego WIA na Windowsie.
    Zapisuje obraz tymczasowy w scans_input i zwraca jego ścieżkę.
    """
    if not HAS_WIA:
        print("\n[BŁĄD] Bezpośrednia obsługa skanera jest niedostępna!")
        print("Powody:")
        print("1. Nie pracujesz na systemie Windows (WIA działa tylko na Windows).")
        print("2. Brak biblioteki pywin32. Uruchom 'install_dependencies.bat', aby ją zainstalować.")
        return None

    print("\n[WIA] Inicjalizacja sprzętowa skanera...")
    try:
        # Tworzymy systemowy obiekt dialogu skanowania WIA
        dialog = win32com.client.Dispatch("WIA.CommonDialog")
        
        print(" -> Oczekiwanie na interakcję w systemowym oknie skanowania...")
        
        # Otwieramy systemowe okno dialogowe wyboru i skanowania obrazu
        image = dialog.ShowAcquireImage(
            1, # DeviceType (ScannerDeviceType)
            0, # Intent (UnspecifiedIntent, pozwala wybrać profil w UI)
            16384, # Bias (MaximizeQuality)
            "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", # FormatID (JPEG)
            False, # AlwaysSelectDevice
            True, # UseCommonUI
            True # CancelError
        )
        
        if image:
            temp_filename = f"scan_wia_{int(time.time())}.jpg"
            scans_input_dir = os.path.abspath("scans_input")
            os.makedirs(scans_input_dir, exist_ok=True)
            temp_path = os.path.join(scans_input_dir, temp_filename)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            image.SaveFile(temp_path)
            print("[SUKCES] Fizyczne skanowanie ukończone!")
            print(f" -> Zapisano plik tymczasowy: {temp_filename}")
            return temp_path
            
    except Exception as e:
        err_str = str(e)
        # Sprawdzamy czy użytkownik po prostu kliknął 'Anuluj'
        if "0x800704c7" in err_str.lower() or "anulowano" in err_str.lower() or "canceled" in err_str.lower():
            print("\n[WIA] Skanowanie zostało anulowane przez użytkownika.")
        else:
            print(f"\n[BŁĄD] Wystąpił błąd komunikacji WIA ze skanerem: {e}")
            print("Upewnij się, że skaner jest podłączony do prądu, włączony i podpięty kablem USB do komputera.")
    return None

def process_scanned_sheet(sheet_path, output_dir, args, start_index=0):
    """
    Wczytuje skan całego arkusza, wykrywa prostokąty kart w niskiej rozdzielczości roboczej,
    a następnie precyzyjnie wycina je w oryginalnej wysokiej rozdzielczości.
    """
    if not os.path.exists(sheet_path):
        print(f"[BŁĄD] Plik skanu nie istnieje: {sheet_path}")
        return start_index, 0

    # Wczytanie obrazu w oryginalnej wysokiej rozdzielczości
    img = cv2.imread(sheet_path)
    if img is None:
        print(f"[BŁĄD] Nie można załadować obrazu: {sheet_path}")
        return start_index, 0

    h_orig, w_orig = img.shape[:2]
    print(f"\nPrzetwarzam arkusz: {os.path.basename(sheet_path)} ({w_orig}x{h_orig} px)...")

    # Krok 1: Przeskalowanie robocze do wykrywania konturów
    WORK_WIDTH = 1600
    scale = WORK_WIDTH / w_orig
    work_height = int(h_orig * scale)
    img_work = cv2.resize(img, (WORK_WIDTH, work_height), interpolation=cv2.INTER_AREA)

    # Konwersja do skali szarości i rozmycie obrazu roboczego
    gray = cv2.cvtColor(img_work, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Detekcja jasności tła
    is_dark = True
    if args.background == "auto":
        is_dark = detect_background_dark(gray)
        print(f" -> [AUTO] Wykryto tło: {'CIEMNE' if is_dark else 'JASNE'}")
    else:
        is_dark = (args.background == "dark")
        print(f" -> Tło ustawione jako: {'CIEMNE' if is_dark else 'JASNE'}")

    # Progowanie w zależności od tła
    if is_dark:
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Czyszczenie morfologiczne (zamknięcie)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Detekcja konturów
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrowanie konturów pod kątem rozmiaru kart
    min_area = WORK_WIDTH * work_height * 0.015
    max_area = WORK_WIDTH * work_height * 0.30
    
    card_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) >= 4 and len(approx) <= 6:
                card_contours.append(cnt)

    print(f" -> Wykryto {len(card_contours)} potencjalnych kart na arkuszu.")

    # Sortowanie konturów od góry do dołu, a potem od lewej do prawej
    def get_contour_precedence(contour, cols=3):
        box = cv2.boundingRect(contour)
        row_height = work_height // 5
        return (box[1] // row_height) * cols + (box[0] // (WORK_WIDTH // cols))

    card_contours = sorted(card_contours, key=get_contour_precedence)

    saved_count = 0
    corner_radius = int(args.target_width * 0.07)
    alpha_mask = create_rounded_mask(args.target_width, args.target_height, corner_radius)

    img_debug = None
    if args.debug_overlay:
        img_debug = img_work.copy()

    for idx, cnt in enumerate(card_contours):
        card_number = start_index + saved_count
        
        # Generowanie nazwy pliku
        if args.naming == "arcana" and card_number < len(MAJOR_ARCANAS):
            filename = f"{MAJOR_ARCANAS[card_number]}.{args.format}"
        else:
            filename = f"card_{card_number:02d}.{args.format}"

        # Znajdujemy obrócony prostokąt
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        
        # Dodajemy informacje debugowania
        if args.debug_overlay:
            cv2.drawContours(img_debug, [cnt], -1, (0, 255, 0), 3)
            M_moment = cv2.moments(cnt)
            if M_moment["m00"] != 0:
                cX = int(M_moment["m10"] / M_moment["m00"])
                cY = int(M_moment["m01"] / M_moment["m00"])
            else:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                cX, cY = bx + bw // 2, by + bh // 2
            cv2.putText(img_debug, f"#{card_number:02d}", (cX - 35, cY), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 5, cv2.LINE_AA)
            cv2.putText(img_debug, f"#{card_number:02d}", (cX - 35, cY), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 2, cv2.LINE_AA)

        # PRZELICZENIE PUNKTÓW
        box_orig = box / scale
        ordered_box = order_points(box_orig)

        width = int(rect[1][0] / scale)
        height = int(rect[1][1] / scale)

        if width > height:
            src_pts = ordered_box
            dst_pts = np.array([
                [0, 0],
                [0, args.target_height - 1],
                [args.target_width - 1, args.target_height - 1],
                [args.target_width - 1, 0]
            ], dtype="float32")
        else:
            src_pts = ordered_box
            dst_pts = np.array([
                [0, 0],
                [args.target_width - 1, 0],
                [args.target_width - 1, args.target_height - 1],
                [0, args.target_height - 1]
            ], dtype="float32")

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(img, M, (args.target_width, args.target_height), flags=cv2.INTER_CUBIC)

        out_path = os.path.join(output_dir, filename)

        if args.dry_run:
            print(f"   [DRY-RUN] Wykryto i dopasowano: {filename} ({args.target_width}x{args.target_height} px)")
        else:
            if args.format in ["png", "webp"]:
                bgra = cv2.cvtColor(warped, cv2.COLOR_BGR2BGRA)
                bgra[:, :, 3] = alpha_mask
                if args.format == "webp":
                    cv2.imwrite(out_path, bgra, [int(cv2.IMWRITE_WEBP_QUALITY), args.quality])
                else:
                    cv2.imwrite(out_path, bgra)
            else:
                bg_color = (0, 0, 0) if is_dark else (255, 255, 255)
                mask_3d = np.repeat(alpha_mask[:, :, np.newaxis], 3, axis=2)
                bg_fill = np.ones_like(warped) * bg_color
                warped_jpg = np.where(mask_3d == 255, warped, bg_fill).astype(np.uint8)
                cv2.imwrite(out_path, warped_jpg, [int(cv2.IMWRITE_JPEG_QUALITY), args.quality])

            print(f"   -> Wycięto i zapisano: {filename} ({args.target_width}x{args.target_height} px)")
        
        saved_count += 1

    if args.debug_overlay and len(card_contours) > 0:
        debug_filename = f"debug_{os.path.splitext(os.path.basename(sheet_path))[0]}.jpg"
        debug_path = os.path.join(output_dir, debug_filename)
        cv2.imwrite(debug_path, img_debug)
        print(f" -> [DEBUG] Zapisano obraz podglądu detekcji: {debug_filename}")

    return start_index + saved_count, saved_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ultra-precyzyjny skrypt do masowej obróbki i autokadrowania skanów kart tarota (OpenCV).")
    parser.add_argument("scans_dir", nargs="?", default="scans_input", help="Katalog wejściowy ze skanami (domyślnie: scans_input)")
    parser.add_argument("output_dir", nargs="?", default="scans_output", help="Katalog wyjściowy dla wyciętych kart (domyślnie: scans_output)")
    parser.add_argument("--scan", action="store_true", help="Uruchamia fizyczne skanowanie za pomocą systemowego WIA przed kadrowaniem")
    parser.add_argument("--background", choices=["dark", "light", "auto"], default="dark", help="Typ tła skanera (domyślnie: dark)")
    parser.add_argument("--format", choices=["png", "jpg", "webp"], default="webp", help="Format zapisu wyjściowego kart (domyślnie: webp)")
    parser.add_argument("--naming", choices=["arcana", "generic"], default="arcana", help="Styl nazywania kart: arcana lub generic (domyślnie: arcana)")
    parser.add_argument("--start-index", type=int, choices=[0, 1], default=0, help="Indeks startowy numeracji kart (domyślnie: 0)")
    parser.add_argument("--target-width", type=int, default=600, help="Szerokość docelowa karty w px (domyślnie: 600)")
    parser.add_argument("--target-height", type=int, default=1032, help="Wysokość docelowa karty w px (domyślnie: 1032)")
    parser.add_argument("--quality", type=int, default=95, help="Jakość kompresji JPG/WebP (0-100, domyślnie: 95)")
    parser.add_argument("--debug-overlay", action="store_true", help="Generuje obraz z narysowanymi konturami i indeksami kart")
    parser.add_argument("--dry-run", action="store_true", help="Analizuje skany bez zapisu kart na dysk")

    args = parser.parse_args()

    os.makedirs(args.scans_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    start_time = time.time()

    print("=== ULTRA-PRECYZYJNA OBRÓBKA I PROSTOWANIE SKANÓW (OPENCV) ===")
    
    files = []
    
    # Krok A: Sprawdzamy czy włączono skanowanie bezpośrednie ze sprzętu
    if args.scan:
        wia_temp_file = scan_image_via_wia()
        if wia_temp_file is None:
            print("[INFO] Skanowanie bezpośrednie nie powiodło się lub zostało anulowane. Zamykam program.")
            sys.exit(0)
        # Przekazujemy nowo utworzony plik do dalszej analizy
        args.scans_dir = os.path.dirname(wia_temp_file)
        files = [os.path.basename(wia_temp_file)]
    else:
        # Krok B: Klasyczne wyszukiwanie plików graficznych w katalogu scans_dir
        extensions = (".jpg", ".jpeg", ".png", ".tiff", ".tif")
        files = [f for f in os.listdir(args.scans_dir) if f.lower().endswith(extensions)]

    if args.dry_run:
        print(" [TRYB DRY-RUN: Symulacja bez zapisu kart produkcyjnych]")
    print(f"Katalog wejściowy : {args.scans_dir}")
    print(f"Katalog wyjściowy : {args.output_dir}")
    print(f"Docelowy format   : {args.format.upper()} (jakość: {args.quality}%)")
    print(f"Styl nazywania    : {args.naming.upper()}")
    print(f"Rozmiar karty     : {args.target_width}x{args.target_height} px")
    print(f"Indeks startowy   : {args.start_index}")
    print("="*70)

    if not files:
        print(f"\n[INFO] Brak skanów w katalogu '{args.scans_dir}'.")
        print("Umieść tam pliki skanera lub uruchom skrypt z flagą --scan.")
        sys.exit(0)

    scan_stats = {}
    current_idx = args.start_index
    total_extracted = 0

    for file in sorted(files):
        sheet_path = os.path.join(args.scans_dir, file)
        current_idx, extracted_count = process_scanned_sheet(
            sheet_path, args.output_dir, args, start_index=current_idx
        )
        scan_stats[file] = extracted_count
        total_extracted += extracted_count

    elapsed_time = time.time() - start_time

    print("\n" + "="*70)
    print("=== RAPORT KOŃCOWY PRZETWARZANIA SKANÓW ===")
    print("="*70)
    print(f"Łączna liczba przeanalizowanych arkuszy : {len(files)}")
    if args.dry_run:
        print(f"Całkowita liczba wykrytych kart (dry)   : {total_extracted}")
    else:
        print(f"Całkowita liczba wyciętych kart         : {total_extracted}")
    print(f"Czas operacji                           : {elapsed_time:.2f} s")
    print(f"Lokalizacja plików                      : {args.output_dir}")
    print("-"*70)
    print("Szczegóły detekcji per arkusz:")
    for file, count in scan_stats.items():
        print(f" -> {file:<30} : Wykryto {count} kart")
    print("="*70)
    print("[SUKCES] Masowa obróbka zakończona powodzeniem!")
    print("="*70)
