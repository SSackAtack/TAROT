import os
import sys
import json
import glob
import argparse
from PIL import Image

def main():
    parser = argparse.ArgumentParser(description="Uniwersalny asystent importu i optymalizacji nowych talii kart do biblioteki TarotVision.")
    parser.add_argument("deck_name", help="Nazwa talii do zaimportowania (np. Magic, Zodiak)")
    parser.add_argument("--lang", default="pl", help="Kod języka talii (domyślnie: pl)")
    parser.add_argument("--copyright", default="private", help="Status praw autorskich (domyślnie: private)")
    parser.add_argument("--source-info", default="Fizyczne skany uzytkownika z urzadzenia WIA", help="Opis źródła skanów")
    
    args = parser.parse_args()
    
    deck_name = args.deck_name
    deck_name_lower = deck_name.lower()
    
    # Konfiguracja ścieżek
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    SOURCE_DIR = os.path.join(PROJECT_ROOT, "scans_output", deck_name)
    DECK_DIR = os.path.join(PROJECT_ROOT, "biblioteka_talii", deck_name_lower)
    
    MASTERY_DIR = os.path.join(DECK_DIR, "mastery")
    PROD_KARTY_DIR = os.path.join(DECK_DIR, "produkcja", "karty")
    PROD_CV_DIR = os.path.join(DECK_DIR, "produkcja", "wzorce_cv")
    PROD_THUMB_DIR = os.path.join(DECK_DIR, "produkcja", "miniatury")
    FRONTEND_KARTY_DIR = os.path.join(PROJECT_ROOT, "app_ar", "public", "karty")
    
    print("====================================================")
    print(f"ASYSTENT BIBLIOTEKI - IMPORT TALII: {deck_name.upper()}")
    print("====================================================")
    
    if not os.path.exists(SOURCE_DIR):
        print(f"[BLAD] Katalog zrodlowy ze skanami nie istnieje: {SOURCE_DIR}")
        print(f"Upewnij sie, ze najpierw wyciales karty za pomoca process_scans.py z prefiksem {deck_name}!")
        sys.exit(1)
        
    # Tworzenie struktury katalogów
    for d in [MASTERY_DIR, PROD_KARTY_DIR, PROD_CV_DIR, PROD_THUMB_DIR, FRONTEND_KARTY_DIR]:
        os.makedirs(d, exist_ok=True)
    print(f"[KATALOGI] Zbudowano strukture katalogow w {DECK_DIR} oraz {FRONTEND_KARTY_DIR}")
    
    # Wyszukiwanie wyciętych kart PNG
    search_pattern = os.path.join(SOURCE_DIR, f"{deck_name}_*.png")
    png_files = glob.glob(search_pattern)
    
    # Dodatkowe sprawdzenie na wypadek małych/wielkich liter w nazwach plików
    if not png_files:
        search_pattern = os.path.join(SOURCE_DIR, f"{deck_name_lower}_*.png")
        png_files = glob.glob(search_pattern)
        
    # Wyodrębnianie indeksu numerycznego do sortowania
    def get_index(filepath):
        basename = os.path.basename(filepath)
        if "back" in basename:
            return 999
        try:
            # Usuwa prefiks talii np. "Magic_" i ".png"
            num_part = basename.split("_")[-1].replace(".png", "")
            return int(num_part)
        except (ValueError, IndexError):
            return 999

    png_files.sort(key=get_index)
    
    # Wyszukanie rewersu (np. Magic_back.png lub Magic_back.webp)
    back_files = glob.glob(os.path.join(SOURCE_DIR, f"{deck_name}_back.*"))
    if not back_files:
        back_files = glob.glob(os.path.join(SOURCE_DIR, f"{deck_name_lower}_back.*"))
        
    all_files_to_process = list(png_files)
    if back_files:
        # Dodajemy rewers na koniec listy do przetworzenia
        for bf in back_files:
            if bf not in all_files_to_process:
                all_files_to_process.append(bf)
                
    if not all_files_to_process:
        print(f"[BLAD] Nie znaleziono plikow {deck_name}_*.png w {SOURCE_DIR}!")
        sys.exit(1)
        
    print(f"[OK] Znaleziono {len(png_files)} kart awersow oraz {len(back_files)} plikow rewersu.")
    
    # Przetwarzanie obrazów
    success_count = 0
    print("\nRozpoczynam konwersje i optymalizacje obrazow...")
    
    for filepath in all_files_to_process:
        filename = os.path.basename(filepath)
        name_no_ext = os.path.splitext(filename)[0]
        
        try:
            with Image.open(filepath) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                # 1. Kopia zapasowa do "mastery"
                master_path = os.path.join(MASTERY_DIR, f"{name_no_ext}.png")
                img.save(master_path, "PNG")
                
                # 2. Skalowanie dla Wizualizacji AR (WebP, wysokość 1200px, z zachowaniem przezroczystości)
                ar_height = 1200
                ar_width = int(ar_height * img.width / img.height)
                img_ar = img.resize((ar_width, ar_height), Image.Resampling.LANCZOS)
                
                # Zapis w bibliotece talii
                webp_path = os.path.join(PROD_KARTY_DIR, f"{name_no_ext}.webp")
                img_ar.save(webp_path, "WEBP", quality=90)
                
                # Kopiowanie bezpośrednio do publicznego folderu frontendu
                frontend_path = os.path.join(FRONTEND_KARTY_DIR, f"{name_no_ext}.webp")
                img_ar.save(frontend_path, "WEBP", quality=90)
                
                # 3. Skalowanie dla miniatur UI (WebP, wysokość 150px, z zachowaniem przezroczystości)
                thumb_height = 150
                thumb_width = int(thumb_height * img.width / img.height)
                img_thumb = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                
                thumb_path = os.path.join(PROD_THUMB_DIR, f"{name_no_ext}_thumb.webp")
                img_thumb.save(thumb_path, "WEBP", quality=80)
                
                # 4. Skalowanie dla detekcji CV (JPG, wysokość 500px, tło zamienione na czarne dla stabilnego CV)
                cv_height = 500
                cv_width = int(cv_height * img.width / img.height)
                img_cv_rgba = img.resize((cv_width, cv_height), Image.Resampling.LANCZOS)
                
                black_bg = Image.new("RGBA", img_cv_rgba.size, (0, 0, 0, 255))
                combined = Image.alpha_composite(black_bg, img_cv_rgba).convert("RGB")
                
                cv_path = os.path.join(PROD_CV_DIR, f"{name_no_ext}.jpg")
                combined.save(cv_path, "JPEG", quality=85)
                
            print(f"  --> Przetworzono pomyslnie: {filename}")
            success_count += 1
        except Exception as e:
            print(f"[BLAD] Podczas przetwarzania {filename}: {e}")
            
    # Generowanie metadanych info.json
    cards = []
    card_count = 0
    
    for f in png_files:
        basename = os.path.basename(f)
        name_no_ext = os.path.splitext(basename)[0]
        
        if "back" in name_no_ext:
            continue
            
        try:
            # Pobieramy ID z nazwy np. Magic_05 -> 5
            card_id = int(name_no_ext.split("_")[-1])
            cards.append({
                "id": card_id,
                "file_base": name_no_ext
            })
            card_count += 1
        except ValueError:
            print(f"[OSTRZEZENIE] Pomijam plik o nieprawidlowym formacie numeracji: {basename}")
            
    info = {
        "deck_name": deck_name,
        "deck_id": f"{deck_name_lower}_scans",
        "language": args.lang,
        "copyright": args.copyright,
        "card_count": card_count,
        "source": args.source_info,
        "cards": sorted(cards, key=lambda x: x["id"])
    }
    
    info_path = os.path.join(DECK_DIR, "info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
        
    print(f"\n[INFO] Wygenerowano plik metadanych: {info_path}")
    print("====================================================")
    print(f"SUKCES! Pomyslnie zaimportowano {success_count}/{len(all_files_to_process)} plikow.")
    print(f"Talia '{deck_name}' zostala w pelni zintegrowana z systemem TarotVision.")
    print("====================================================")

if __name__ == "__main__":
    main()
