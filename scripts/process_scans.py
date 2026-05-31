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

def log_to_file(message, level="INFO"):
    """Zapisuje zdarzenie do dedykowanego pliku logów logs/process_scans.log"""
    try:
        log_dir = os.path.abspath("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "process_scans.log")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception:
        pass

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

def get_orientation_score(img_bgr, target_width, target_height):
    """
    Oblicza jasność regionów krawędziowych karty w celu wyznaczenia jej prawidłowej orientacji.
    Regiony górny/dolny powinny zawierać białe etykiety tekstowe (np. numer/nazwa karty),
    podczas gdy brzegi lewy/prawy powinny mieć minimalną jasność (kara za etykietę leżącą bokiem).
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    W, H = target_width, target_height
    
    # Proporcje grubości pasków (12% wysokości i szerokości)
    pad_h = int(H * 0.12)
    pad_w = int(W * 0.12)
    margin_w = int(W * 0.10)
    margin_h = int(H * 0.10)
    
    # Wycinamy regiony, omijając zaokrąglone rogi
    top_region = gray[0:pad_h, margin_w:W-margin_w]
    bottom_region = gray[H-pad_h:H, margin_w:W-margin_w]
    left_region = gray[margin_h:H-margin_h, 0:pad_w]
    right_region = gray[margin_h:H-margin_h, W-pad_w:W]
    
    # Obliczamy średnią jasność
    avg_top = float(np.mean(top_region)) if top_region.size > 0 else 0.0
    avg_bottom = float(np.mean(bottom_region)) if bottom_region.size > 0 else 0.0
    avg_left = float(np.mean(left_region)) if left_region.size > 0 else 0.0
    avg_right = float(np.mean(right_region)) if right_region.size > 0 else 0.0
    
    # Wyznaczamy ostateczny score: preferujemy paski poziome, karzemy pionowe
    score = (avg_top + avg_bottom) - (avg_left + avg_right)
    return score, (avg_top, avg_bottom, avg_left, avg_right)

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
        log_to_file("Próba skanowania WIA bez zainstalowanej biblioteki pywin32 lub na systemie innym niż Windows", "ERROR")
        return None

    try:
        # Tworzymy systemowy obiekt dialogu skanowania WIA
        log_to_file("Inicjalizacja sprzętowa skanera WIA...", "INFO")
        dialog = win32com.client.Dispatch("WIA.CommonDialog")
        
        print("\n -> [WIA] Inicjalizacja sprzetowa skanera...")
        print("    [UWAGA] Bezposrednie skanowanie WIA w systemie Windows wymusza tymczasowy format JPEG")
        print("    ze wzgledu na ograniczenia systemowych obiektow COM. Dla najwyzszej, bezkompromisowej")
        print("    jakosci referencyjnej (Master) zalecamy tradycyjny workflow: skanowanie do bezstratnego")
        print("    formatu PNG / TIFF za pomoca oprogramowania skanera, a nastepnie obrobke z scans_input.")
        print(" -> Otwieranie systemowego kreatora skanowania Windows...")
        
        # Otwieramy systemowe okno dialogowe wyboru i skanowania obrazu
        image = dialog.ShowAcquireImage(
            1, # DeviceType (ScannerDeviceType)
            0, # Intent (UnspecifiedIntent)
            16384, # Bias (MaximizeQuality)
            "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", # FormatID (JPEG)
            False, # AlwaysSelectDevice
            True, # UseCommonUI
            True # CancelError
        )
        
        if image:
            temp_filename = f"scan_wia_temp.{int(time.time())}.jpg"
            scans_input_dir = os.path.abspath("scans_input")
            os.makedirs(scans_input_dir, exist_ok=True)
            temp_path = os.path.join(scans_input_dir, temp_filename)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            image.SaveFile(temp_path)
            # Zapisujemy stałą kopię diagnostyczną, która nie jest usuwana
            try:
                import shutil
                shutil.copy2(temp_path, os.path.join(scans_input_dir, "last_wia_scan.jpg"))
                log_to_file("Zapisano kopię diagnostyczną scans_input/last_wia_scan.jpg", "INFO")
            except Exception as e:
                log_to_file(f"Nie udało się zapisać kopii last_wia_scan.jpg: {e}", "ERROR")
            print(" -> [SUKCES] Pobrano skan z urządzenia!")
            log_to_file(f"Pomyślnie pobrano skan z urządzenia WIA i zapisano jako plik tymczasowy: {temp_path}", "INFO")
            return temp_path
            
    except Exception as e:
        err_str = str(e)
        if "0x800704c7" in err_str.lower() or "anulowano" in err_str.lower() or "canceled" in err_str.lower():
            print("\n[WIA] Skanowanie zostało anulowane przez użytkownika.")
            log_to_file("Skanowanie WIA zostało anulowane przez użytkownika.", "WARNING")
        else:
            print(f"\n[BŁĄD] Wystąpił błąd komunikacji WIA ze skanerem: {e}")
            print("Upewnij się, że skaner jest podłączony do prądu, włączony i podpięty do komputera USB.")
            log_to_file(f"Błąd komunikacji WIA ze skanerem: {e}", "ERROR")
    return None

def process_scanned_sheet(sheet_path, output_dir, args, start_index=0, custom_prefix=None, is_back=False):
    """
    Wczytuje skan całego arkusza, wykrywa prostokąty kart w niskiej rozdzielczości roboczej,
    a następnie precyzyjnie wycina je w oryginalnej wysokiej rozdzielczości.
    """
    if not os.path.exists(sheet_path):
        print(f"[BŁĄD] Plik skanu nie istnieje: {sheet_path}")
        log_to_file(f"Plik skanu nie istnieje: {sheet_path}", "ERROR")
        return start_index, 0

    # Wczytanie obrazu w oryginalnej wysokiej rozdzielczości
    img = cv2.imread(sheet_path)
    if img is None:
        print(f"[BŁĞD] Nie można załadować obrazu: {sheet_path}")
        log_to_file(f"Nie można załadować obrazu za pomocą OpenCV: {sheet_path}", "ERROR")
        return start_index, 0

    h_orig, w_orig = img.shape[:2]
    print(f"\nPrzetwarzam arkusz: {os.path.basename(sheet_path)} ({w_orig}x{h_orig} px)...")
    log_to_file(f"Rozpoczęto przetwarzanie arkusza: {sheet_path} ({w_orig}x{h_orig} px)", "INFO")

    # Krok 1: Przeskalowanie robocze do wykrywania konturów
    WORK_WIDTH = 1600
    scale = WORK_WIDTH / w_orig
    work_height = int(h_orig * scale)
    img_work = cv2.resize(img, (WORK_WIDTH, work_height), interpolation=cv2.INTER_AREA)

    # Konwersja do skali szarości i rozmycie obrazu roboczego
    gray = cv2.cvtColor(img_work, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Detekcja jasności tła do celów operatorskich (JPG/logowanie)
    is_dark = True
    if args.background == "auto":
        is_dark = detect_background_dark(gray)
        print(f" -> [AUTO] Wykryto tło: {'CIEMNE' if is_dark else 'JASNE'}")
        log_to_file(f"Autodetekcja tła dla {os.path.basename(sheet_path)}: {'CIEMNE' if is_dark else 'JASNE'}", "INFO")
    else:
        is_dark = (args.background == "dark")
        print(f" -> Tło ustawione jako: {'CIEMNE' if is_dark else 'JASNE'}")
        log_to_file(f"Ustawiono tło manualnie dla {os.path.basename(sheet_path)}: {'CIEMNE' if is_dark else 'JASNE'}", "INFO")

    # Budowa modelu koloru tła w przestrzeni CIE L*a*b* na podstawie krawędzi obrazu roboczego
    # Delikatne rozmycie koloru redukuje mikroszum matrycy skanera
    img_work_blurred = cv2.GaussianBlur(img_work, (5, 5), 0)
    img_lab = cv2.cvtColor(img_work_blurred, cv2.COLOR_BGR2LAB)
    
    h_lab, w_lab = img_lab.shape[:2]
    border_pixels = []
    # Pobieramy próbki pikseli tła z krawędzi (szerokość 15 px)
    border_pixels.extend(img_lab[0:15, :, :].reshape(-1, 3))
    border_pixels.extend(img_lab[h_lab-15:h_lab, :, :].reshape(-1, 3))
    border_pixels.extend(img_lab[:, 0:15, :].reshape(-1, 3))
    border_pixels.extend(img_lab[:, w_lab-15:w_lab, :].reshape(-1, 3))
    border_pixels = np.array(border_pixels)
    
    # Mediana koloru tła (wektor 3-kanałowy LAB)
    bg_color_lab = np.median(border_pixels, axis=0)
    log_to_file(f"Model koloru tła LAB: L={bg_color_lab[0]:.1f}, A={bg_color_lab[1]:.1f}, B={bg_color_lab[2]:.1f}", "INFO")

    # Obliczenie euklidesowego dystansu barwnego każdego piksela do modelu tła
    diff = img_lab.astype(np.float32) - bg_color_lab
    dist = np.sqrt(np.sum(diff**2, axis=2))
    
    # Skalowanie dystansu do standardowej głębi 8-bit
    dist_normalized = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Progowanie mapy dystansu: automatyczne Otsu z progiem bezpieczeństwa (bezpiecznik przed szumem)
    otsu_thresh, thresh_color = cv2.threshold(dist_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    if otsu_thresh < 20:
        # Bardzo jednolite tło bez kart - podnosimy próg, by uniknąć wykrywania szumu
        _, thresh_color = cv2.threshold(dist_normalized, 20, 255, cv2.THRESH_BINARY)
        log_to_file(f"Zastosowano próg bezpieczeństwa (20), bo Otsu dało zbyt niską wartość: {otsu_thresh:.1f}", "INFO")
    else:
        log_to_file(f"Progowanie Otsu dla odległości LAB: {otsu_thresh:.1f}", "INFO")

    # Detekcja krawędzi Canny'ego na rozmytym obrazie szarym (wygładzanie Canny'ego na krawędziach kart)
    canny_edges = cv2.Canny(blurred, 30, 100)

    # Łączenie logicznym OR maski barwnej i krawędzi (scala ciemne karty na ciemnym tle)
    combined_mask = cv2.bitwise_or(thresh_color, canny_edges)

    # Czyszczenie i domknięcie morfologiczne większym kernelem (11x11)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    thresh = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

    # Detekcja konturów
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrowanie konturów pod kątem rozmiaru kart
    min_area = WORK_WIDTH * work_height * 0.015
    max_area = WORK_WIDTH * work_height * 0.30
    
    card_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            rect = cv2.minAreaRect(cnt)
            (x, y), (w_rect, h_rect), angle = rect
            if min(w_rect, h_rect) > 0:
                aspect_ratio = max(w_rect, h_rect) / min(w_rect, h_rect)
                
                # Solidity zapobiega wykrywaniu dziwnych, ażurowych kształtów
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                # Karty Tarota mają Aspect Ratio w okolicach 1.6-1.7, dajemy bezpieczny przedział 1.3 - 2.1
                # Solidity na poziomie >= 0.6 pozwala na wykrycie kart z refleksami świetlnymi
                if 1.3 <= aspect_ratio <= 2.1 and solidity >= 0.6:
                    card_contours.append(cnt)
                    log_to_file(f"Zaakceptowano kontur karty: pow={area:.1f}, AR={aspect_ratio:.2f}, solidity={solidity:.2f}", "INFO")
                else:
                    log_to_file(f"Odrzucono kontur: pow={area:.1f}, AR={aspect_ratio:.2f}, solidity={solidity:.2f} (złe AR lub solidity)", "DEBUG")

    print(f" -> Wykryto {len(card_contours)} potencjalnych kart na arkuszu.")
    log_to_file(f"Wykryto {len(card_contours)} konturów kart spełniających kryteria wymiarów na arkuszu {os.path.basename(sheet_path)}", "INFO")
    if len(card_contours) == 0:
        log_to_file(f"OSTRZEŻENIE: Wykryto 0 kart na arkuszu: {os.path.basename(sheet_path)}. Prawdopodobnie brak kontrastu z tłem lub złe DPI.", "WARNING")
        print("\n    [INFO] Wykryto 0 kart na arkuszu! Najczestsze przyczyny:")
        print("    1. Brak kontrastu: Jasne karty na jasnym/bialym tle skanera (zamknieta biała pokrywa).")
        print("       -> Rozwiazanie: Skanuj z otwarta pokrywa (ciemne tlo) lub podloz czarna podkladke.")
        print("    2. Zly parametr DPI: Upewnij sie, ze skanujesz w zalecanym standardzie 300 DPI.")
        print("       (Przy 100 DPI karty sa za male i algorytm je ignoruje).")

    # Sortowanie konturów od góry do dołu, a potem od lewej do prawej
    def get_contour_precedence(contour, cols=3):
        box = cv2.boundingRect(contour)
        row_height = work_height // 5
        return (box[1] // row_height) * cols + (box[0] // (WORK_WIDTH // cols))

    card_contours = sorted(card_contours, key=get_contour_precedence)

    if is_back and len(card_contours) > 0:
        # Wybieramy tylko jeden, największy kontur rewersu, aby uniknąć nadpisywania tego samego pliku
        card_contours = [max(card_contours, key=cv2.contourArea)]

    saved_count = 0
    corner_radius = int(args.target_width * 0.07)
    alpha_mask = create_rounded_mask(args.target_width, args.target_height, corner_radius)

    img_debug = None
    if args.debug_overlay:
        img_debug = img_work.copy()

    for idx, cnt in enumerate(card_contours):
        card_number = start_index + saved_count
        
        # Generowanie nazwy pliku w zależności od prefiksu, rewersu lub figur
        if is_back:
            filename = f"{custom_prefix}_back.{args.format}" if custom_prefix else f"back.{args.format}"
        elif custom_prefix:
            filename = f"{custom_prefix}_{card_number:02d}.{args.format}"
        elif args.naming == "arcana" and card_number < len(MAJOR_ARCANAS):
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

        # Wyliczamy parametry do logowania
        area = cv2.contourArea(cnt)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        rect = cv2.minAreaRect(cnt)
        (x_mid, y_mid), (w_rect, h_rect), angle_rect = rect
        aspect_ratio = max(w_rect, h_rect) / min(w_rect, h_rect) if min(w_rect, h_rect) > 0 else 1.0

        # Wyliczamy rzeczywistą szerokość i wysokość karty na skanie na podstawie ordered_box
        width_real = (
            np.linalg.norm(ordered_box[0] - ordered_box[1]) +
            np.linalg.norm(ordered_box[3] - ordered_box[2])
        ) / 2.0

        height_real = (
            np.linalg.norm(ordered_box[0] - ordered_box[3]) +
            np.linalg.norm(ordered_box[1] - ordered_box[2])
        ) / 2.0

        is_landscape_on_scan = width_real > height_real

        # Wycinek standardowy (pionowy: 600x1032)
        dst_pts_pion = np.array([
            [0, 0],
            [args.target_width - 1, 0],
            [args.target_width - 1, args.target_height - 1],
            [0, args.target_height - 1]
        ], dtype="float32")
        M_pion = cv2.getPerspectiveTransform(ordered_box, dst_pts_pion)
        warped_pion = cv2.warpPerspective(img, M_pion, (args.target_width, args.target_height), flags=cv2.INTER_CUBIC)

        # Wycinek poziomy (1032x600 - na wypadek gdyby karta na skanie leżała bokiem)
        dst_pts_poziom = np.array([
            [0, 0],
            [args.target_height - 1, 0],
            [args.target_height - 1, args.target_width - 1],
            [0, args.target_width - 1]
        ], dtype="float32")
        M_poziom = cv2.getPerspectiveTransform(ordered_box, dst_pts_poziom)
        warped_poziom = cv2.warpPerspective(img, M_poziom, (args.target_height, args.target_width), flags=cv2.INTER_CUBIC)

        # Generujemy warianty o docelowych wymiarach pionowych (600x1032) w zależności od fizycznej orientacji na skanie
        if is_landscape_on_scan:
            candidates = {
                "rot_90_cw": cv2.rotate(warped_poziom, cv2.ROTATE_90_CLOCKWISE),
                "rot_90_ccw": cv2.rotate(warped_poziom, cv2.ROTATE_90_COUNTERCLOCKWISE)
            }
        else:
            candidates = {
                "rot_0": warped_pion,
                "rot_180": cv2.rotate(warped_pion, cv2.ROTATE_180)
            }

        # Obliczamy scoring jasności dla każdego z wariantów
        best_cand_name = "rot_0"
        best_score = -999999.0
        best_details = (0.0, 0.0, 0.0, 0.0)
        cand_scores = {}

        for cand_name, cand_img in candidates.items():
            score, details = get_orientation_score(cand_img, args.target_width, args.target_height)
            cand_scores[cand_name] = score
            if score > best_score:
                best_score = score
                best_cand_name = cand_name
                best_details = details

        # Zapisujemy najlepszy wariant
        warped = candidates[best_cand_name]
        avg_top, avg_bottom, avg_left, avg_right = best_details

        # Dokładny log diagnostyczny zgodnie z wymaganiami TASK-SCAN-004
        log_to_file(
            f"Karta #{card_number:02d} ({filename}) -> "
            f"area={area:.1f}, aspect_ratio={aspect_ratio:.2f}, solidity={solidity:.2f}, "
            f"background_mode={'dark' if is_dark else 'light'}, "
            f"selected_orientation={best_cand_name} (score={best_score:.2f}), "
            f"orientation_scores={ {k: round(v, 2) for k, v in cand_scores.items()} }. "
            f"Srednia jasnosc regionow (top/bottom/left/right): {avg_top:.1f}/{avg_bottom:.1f}/{avg_left:.1f}/{avg_right:.1f}",
            "INFO"
        )

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
            log_to_file(f"Zapisano wyciętą kartę: {filename} w {output_dir}", "INFO")
        
        saved_count += 1

    if args.debug_overlay and len(card_contours) > 0:
        debug_filename = f"debug_{os.path.splitext(os.path.basename(sheet_path))[0]}.jpg"
        debug_path = os.path.join(output_dir, debug_filename)
        cv2.imwrite(debug_path, img_debug)
        print(f" -> [DEBUG] Zapisano obraz podglądu detekcji: {debug_filename}")
        log_to_file(f"Zapisano obraz podglądu detekcji: {debug_path}", "INFO")

    return start_index + saved_count, saved_count

def run_interactive_assistant(args):
    """
    Prowadzi użytkownika krok po kroku przez proces skanowania masowego i testowego.
    """
    print("\n=============================================================")
    print("        TAROTVISION - INTERAKTYWNY ASYSTENT SKANOWANIA")
    print("=============================================================")
    
    # Krok 1: Wybór trybu (Testowy / Pełny)
    mode = input("\nCzy chcesz zrobic szybki SKAN PROBNY (T) czy SKANOWAC CALA TALIE (C)? [T/C]: ").strip().upper()
    
    if mode == "T":
        # Scenariusz A: Skan próbny
        log_to_file("Rozpoczęto interaktywny SKAN PRÓBNY", "INFO")
        print("\n -> Wybrano tryb SKANU PROBNEGO (prefiks plikow: Test_XX).")
        print(" -> Skaner wykona 1 probny skan, a gotowe karty zapisze jako Test_XX.")
        print(" -> Przygotuj skaner, poloz karty i nacisnij Enter, aby rozpoczac...")
        input()
        
        wia_temp_file = scan_image_via_wia()
        if wia_temp_file is None:
            print("[INFO] Skanowanie probne przerwane.")
            log_to_file("Skanowanie próbne zostało przerwane (brak pliku ze skanera WIA).", "WARNING")
            return
            
        # Przetwarzamy pojedynczy arkusz testowy
        next_idx, extracted_count = process_scanned_sheet(wia_temp_file, args.output_dir, args, start_index=0, custom_prefix="Test")
        
        # Jeśli nie wykryto żadnej karty, zachowujemy plik tymczasowy w celach diagnostycznych
        if extracted_count == 0:
            failed_filename = f"failed_scan_{int(time.time())}.jpg"
            failed_path = os.path.join(os.path.dirname(wia_temp_file), failed_filename)
            try:
                os.rename(wia_temp_file, failed_path)
                print(f"\n[DIAGNOSTYKA] Zachowano surowy skan do analizy w: scans_input/{failed_filename}")
                print("Możesz go otworzyć i sprawdzić, czy obraz jest prawidłowo naświetlony oraz czy tło jest kontrastowe.")
                log_to_file(f"Nie wykryto kart w skanie próbnym. Zachowano surowy skan jako: {failed_path}", "WARNING")
            except Exception as e:
                log_to_file(f"Błąd przy zachowywaniu nieudanego skanu: {e}", "ERROR")
        else:
            # Usuwamy plik tymczasowy tylko w przypadku sukcesu
            try:
                os.remove(wia_temp_file)
            except:
                pass
            log_to_file(f"Skan próbny zakończony pomyślnie. Wycięto kart: {extracted_count}.", "INFO")
            
        print("\n[SUKCES] Probna obrobka zakonczona pomyslnie!")
        print("Otwieranie folderu scans_output...")
        try:
            os.system("explorer scans_output")
        except:
            pass
            
    elif mode == "C":
        # Scenariusz B: Masowe skanowanie całej talii
        deck_name = input("\n[1/2] Podaj unikalna nazwe kolekcji/talii (np. tarot_marsylski): ").strip()
        if not deck_name:
            deck_name = "talia"
        deck_name = deck_name.replace(" ", "_") # Bezpieczeństwo nazw plików
        
        # Określamy dedykowany katalog wyjściowy dla danej talii
        deck_output_dir = os.path.join(args.output_dir, deck_name)
        os.makedirs(deck_output_dir, exist_ok=True)
        
        if args.total_cards is not None:
            total_cards = args.total_cards
            print(f"[2/2] Calkowita ilosc kart w tej talii ustawiona z CLI: {total_cards}")
        else:
            total_cards_str = input("[2/2] Podaj calkowita ilosc kart w tej talii (np. 22 lub 78): ").strip()
            try:
                total_cards = int(total_cards_str)
            except ValueError:
                total_cards = 22
                print(f" -> [INFO] Niepoprawna liczba. Ustawiono domyslnie: {total_cards} kart.")
            
        print(f"\n -> Rozpoczynamy skanowanie calej talii '{deck_name}' ({total_cards} kart).")
        print(f" -> Pliki beda zapisywane w dedykowanym folderze: {deck_output_dir}/{deck_name}_XX.{args.format}")
        
        scanned_count = 0
        sheet_index = 1
        log_to_file(f"Rozpoczęto masowe skanowanie talii '{deck_name}' (oczekiwane karty: {total_cards})", "INFO")
        
        while scanned_count < total_cards:
            print(f"\n=============================================================")
            print(f" ARKUSZ #{sheet_index} | Zeskanowano: {scanned_count} z {total_cards} kart")
            print(f"=============================================================")
            print("Instrukcja:")
            print(f"1. Poloz kolejne karty na szybie skanera (np. 4 sztuki).")
            print(f"2. Nacisnij Enter, aby wywolac systemowe skanowanie...")
            input()
            
            wia_temp_file = scan_image_via_wia()
            if wia_temp_file is None:
                print("\n[INFO] Skanowanie tego arkusza nie powiodlo sie.")
                log_to_file(f"Skanowanie arkusza #{sheet_index} nie powiodło się lub zostało przerwane.", "WARNING")
                retry = input("Czy chcesz sprobowac ponownie skanowac ten arkusz? [T/N]: ").strip().upper()
                if retry == "T":
                    continue
                else:
                    print(f"\n[INFO] Skanowanie przerwane. Zapisano lacznie {scanned_count} kart.")
                    log_to_file(f"Skanowanie przerwane przez użytkownika. Zapisano łącznie {scanned_count} z {total_cards} kart.", "INFO")
                    break
            
            # Przetwarzamy skan z poprawnym dynamicznym indeksem startowym
            next_idx, extracted_count = process_scanned_sheet(
                wia_temp_file, deck_output_dir, args, start_index=scanned_count, custom_prefix=deck_name
            )
            
            # Jeśli nie wykryto żadnej karty, zachowujemy plik tymczasowy do diagnostyki
            if extracted_count == 0:
                failed_filename = f"failed_scan_{deck_name}_sheet_{sheet_index}_{int(time.time())}.jpg"
                failed_path = os.path.join(os.path.dirname(wia_temp_file), failed_filename)
                try:
                    os.rename(wia_temp_file, failed_path)
                    print(f"\n[DIAGNOSTYKA] Z powodu braku wykrycia kart, zachowano surowy skan w: scans_input/{failed_filename}")
                    log_to_file(f"Nie wykryto kart na arkuszu #{sheet_index} talii '{deck_name}'. Zachowano surowy skan jako: {failed_path}", "WARNING")
                except Exception as e:
                    log_to_file(f"Błąd przy zachowywaniu nieudanego skanu: {e}", "ERROR")
            else:
                scanned_count += extracted_count
                sheet_index += 1
                # Usuwamy plik tymczasowy
                try:
                    os.remove(wia_temp_file)
                except:
                    pass
                log_to_file(f"Pomyślnie przetworzono arkusz #{sheet_index-1}. Zeskanowano łącznie {scanned_count} kart.", "INFO")
                
            if scanned_count >= total_cards:
                print(f"\n=============================================================")
                print(f" [SUKCES] BRAWO! ZESKANOWANO CALA TALIE! ({scanned_count}/{total_cards} kart)")
                print(f" Wszystkie pliki znajdziesz w folderze: {deck_output_dir}")
                print("=============================================================")
                break
                
            print(f"\n -> [POSTEP] Zeskanowano {scanned_count} z {total_cards} kart. Pozostalo: {total_cards - scanned_count} kart.")
            cont = input("Czy chcesz skanowac kolejny arkusz? [T/N]: ").strip().upper()
            if cont != "T":
                print(f"\n[INFO] Skanowanie przerwane na prosbe uzytkownika. Zapisano {scanned_count} kart.")
                break
                
        # Jeśli zeskanowano całą talię, dodajemy krok na skanowanie rewersu (koszulki)
        if scanned_count >= total_cards:
            log_to_file("Rozpoczęto dodatkowy krok: skanowanie rewersu kart", "INFO")
            print(f"\n=============================================================")
            print(f"       KROK DODATKOWY: SKANOWANIE REWERSU (KOSZULKI)")
            print(f"=============================================================")
            print("Instrukcja:")
            print("1. Połóż JEDNĄ dowolną kartę rewersem (tyłem) do dołu na szybie skanera.")
            print("2. Naciśnij Enter, aby rozpocząć skanowanie rewersu...")
            input()
            
            print("\n -> Uruchamianie skanowania rewersu...")
            wia_temp_file = scan_image_via_wia()
            if wia_temp_file is not None:
                print(" -> Przetwarzanie skanu rewersu...")
                # Przetwarzamy obraz z flagą is_back=True
                _, extracted_count = process_scanned_sheet(
                    wia_temp_file, deck_output_dir, args, start_index=0, custom_prefix=deck_name, is_back=True
                )
                
                # Jeśli nie wykryto rewersu, zachowujemy plik tymczasowy
                if extracted_count == 0:
                    failed_filename = f"failed_scan_{deck_name}_back_{int(time.time())}.jpg"
                    failed_path = os.path.join(os.path.dirname(wia_temp_file), failed_filename)
                    try:
                        os.rename(wia_temp_file, failed_path)
                        print(f"\n[DIAGNOSTYKA] Nie wykryto rewersu! Zachowano surowy skan w: scans_input/{failed_filename}")
                        log_to_file(f"Nie wykryto rewersu kart talii '{deck_name}'. Zachowano surowy skan jako: {failed_path}", "WARNING")
                    except Exception as e:
                        log_to_file(f"Błąd przy zachowywaniu nieudanego skanu rewersu: {e}", "ERROR")
                else:
                    # Usuwamy plik tymczasowy
                    try:
                        os.remove(wia_temp_file)
                    except:
                        pass
                    print(f"\n -> [SUKCES] Rewers został pomyślnie zeskanowany i zapisany!")
                    log_to_file(f"Pomyślnie zeskanowano i zapisano rewers kart talii '{deck_name}'", "INFO")
            else:
                print("\n[INFO] Skanowanie rewersu zostało pominięte lub nie powiodło się.")

        # Otwieramy katalog wyjściowy
        if scanned_count > 0:
            print(f"\nOtwieranie folderu {deck_output_dir}...")
            try:
                os.system(f"explorer {os.path.abspath(deck_output_dir)}")
            except:
                pass
    else:
        print("[INFO] Niepoprawny wybor trybu. Asystent zostal zamkniety.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ultra-precyzyjny skrypt do masowej obróbki i autokadrowania skanów kart tarota (OpenCV).")
    parser.add_argument("scans_dir", nargs="?", default="scans_input", help="Katalog wejściowy ze skanami (domyślnie: scans_input)")
    parser.add_argument("output_dir", nargs="?", default="scans_output", help="Katalog wyjściowy dla wyciętych kart (domyślnie: scans_output)")
    parser.add_argument("--scan", action="store_true", help="Uruchamia fizyczne skanowanie za pomocą systemowego WIA przed kadrowaniem")
    parser.add_argument("--background", choices=["dark", "light", "auto"], default="auto", help="Typ tła skanera (domyślnie: auto)")
    parser.add_argument("--format", choices=["png", "jpg", "webp"], default="webp", help="Format zapisu wyjściowego kart (domyślnie: webp)")
    parser.add_argument("--naming", choices=["arcana", "generic"], default="arcana", help="Styl nazywania kart: arcana lub generic (domyślnie: arcana)")
    parser.add_argument("--start-index", type=int, choices=[0, 1], default=0, help="Indeks startowy numeracji kart (domyślnie: 0)")
    parser.add_argument("--target-width", type=int, default=600, help="Szerokość docelowa karty w px (domyślnie: 600)")
    parser.add_argument("--target-height", type=int, default=1032, help="Wysokość docelowa karty w px (domyślnie: 1032)")
    parser.add_argument("--quality", type=int, default=95, help="Jakość kompresji JPG/WebP (0-100, domyślnie: 95)")
    parser.add_argument("--debug-overlay", action="store_true", help="Generuje obraz z narysowanymi konturami i indeksami kart")
    parser.add_argument("--dry-run", action="store_true", help="Analizuje skany bez zapisu kart na dysk")
    parser.add_argument("--interactive", action="store_true", help="Uruchamia asystenta krok po kroku (pętla masowego skanowania)")
    parser.add_argument("--prefix", type=str, default=None, help="Niestandardowy prefiks dla nazw wycinanych kart")
    parser.add_argument("--total-cards", type=int, default=None, help="Maksymalna oczekiwana liczba kart w talii")

    args = parser.parse_args()

    os.makedirs(args.scans_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    start_time = time.time()

    # Sprawdzamy czy użytkownik chce uruchomić asystenta masowego skanowania
    if args.interactive:
        run_interactive_assistant(args)
        sys.exit(0)

    print("=== ULTRA-PRECYZYJNA OBRÓBKA I PROSTOWANIE SKANÓW (OPENCV) ===")
    
    files = []
    
    if args.scan:
        wia_temp_file = scan_image_via_wia()
        if wia_temp_file is None:
            print("[INFO] Skanowanie bezpośrednie nie powiodło się lub zostało anulowane. Zamykam program.")
            sys.exit(0)
        args.scans_dir = os.path.dirname(wia_temp_file)
        files = [os.path.basename(wia_temp_file)]
    else:
        extensions = (".jpg", ".jpeg", ".png", ".tiff", ".tif")
        files = [f for f in os.listdir(args.scans_dir) if f.lower().endswith(extensions)]

    if args.dry_run:
        print(" [TRYB DRY-RUN: Symulacja bez zapisu kart produkcyjnych]")
    print(f"Katalog wejściowy : {args.scans_dir}")
    print(f"Katalog wyjściowy : {args.output_dir}")
    print(f"Docelowy format   : {args.format.upper()} (jakość: {args.quality}%)")
    print(f"Styl nazywania    : {args.naming.upper()}")
    if args.prefix:
        print(f"Prefiks plikow    : {args.prefix}")
    print(f"Rozmiar karty     : {args.target_width}x{args.target_height} px")
    print(f"Indeks startowy   : {args.start_index}")
    print("="*70)

    if not files:
        print(f"\n[INFO] Brak skanów w katalogu '{args.scans_dir}'.")
        print("Umieść tam pliki skanera lub uruchom skrypt z flagą --scan lub --interactive.")
        sys.exit(0)

    scan_stats = {}
    current_idx = args.start_index
    total_extracted = 0

    for file in sorted(files):
        sheet_path = os.path.join(args.scans_dir, file)
        current_idx, extracted_count = process_scanned_sheet(
            sheet_path, args.output_dir, args, start_index=current_idx, custom_prefix=args.prefix
        )
        scan_stats[file] = extracted_count
        total_extracted += extracted_count

        # Jeśli skrypt był uruchomiony z plikiem tymczasowym WIA, czyścimy go po obróbce
        if args.scan:
            try:
                os.remove(sheet_path)
            except:
                pass

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
    if total_extracted == 0:
        print("[OSTRZEŻENIE] Nie wycięto ani jednej karty! Sprawdź jasność tła oraz czy karty nie leżą poza obszarem skanowania.")
    else:
        print("[SUKCES] Masowa obróbka zakończona powodzeniem!")
    print("="*70)
