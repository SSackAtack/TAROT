import os
import sys
import json
import glob
from PIL import Image

# Konfiguracja ścieżek
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_DIR = os.path.join(PROJECT_ROOT, "scans_output", "Zodiak")
DECK_DIR = os.path.join(PROJECT_ROOT, "biblioteka_talii", "zodiak")

MASTERY_DIR = os.path.join(DECK_DIR, "mastery")
PROD_KARTY_DIR = os.path.join(DECK_DIR, "produkcja", "karty")
PROD_CV_DIR = os.path.join(DECK_DIR, "produkcja", "wzorce_cv")
PROD_THUMB_DIR = os.path.join(DECK_DIR, "produkcja", "miniatury")
FRONTEND_KARTY_DIR = os.path.join(PROJECT_ROOT, "app_ar", "public", "karty")

def setup_directories():
    for d in [MASTERY_DIR, PROD_KARTY_DIR, PROD_CV_DIR, PROD_THUMB_DIR, FRONTEND_KARTY_DIR]:
        os.makedirs(d, exist_ok=True)
    print(f"[KATALOGI] Zbudowano strukture katalogow w {DECK_DIR} oraz {FRONTEND_KARTY_DIR}")

def get_source_images():
    print(f"[SZUKAJ] Szukam wycietych kart w: {SOURCE_DIR}...")
    png_files = glob.glob(os.path.join(SOURCE_DIR, "Zodiak_*.png"))
    
    # Sortowanie numeryczne na podstawie końcówki
    def get_index(filepath):
        basename = os.path.basename(filepath)
        if "back" in basename:
            return 999
        try:
            return int(basename.replace("Zodiak_", "").replace(".png", ""))
        except ValueError:
            return 999

    png_files.sort(key=get_index)
    
    if not png_files:
        print(f"[BLAD] Nie znaleziono plikow Zodiak_*.png w {SOURCE_DIR}!")
        sys.exit(1)
        
    print(f"[OK] Znaleziono {len(png_files)} plikow kart (w tym potencjalnie rewers).")
    return png_files

def process_image(filepath):
    filename = os.path.basename(filepath)
    name_no_ext = os.path.splitext(filename)[0]
    
    try:
        # Wczytujemy obraz źródłowy z przezroczystością (RGBA)
        with Image.open(filepath) as img:
            # Upewnijmy się, że to RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # 1. Kopia zapasowa do "mastery" (jako PNG bezstratny)
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
            
            # Tworzymy czarne tło i nakładamy na nie obrazek z uwzględnieniem przezroczystości
            black_bg = Image.new("RGBA", img_cv_rgba.size, (0, 0, 0, 255))
            combined = Image.alpha_composite(black_bg, img_cv_rgba).convert("RGB")
            
            cv_path = os.path.join(PROD_CV_DIR, f"{name_no_ext}.jpg")
            combined.save(cv_path, "JPEG", quality=85)
            
        print(f"  --> Przetworzono pomyslnie: {filename}")
        return True
    except Exception as e:
        print(f"[BLAD] Podczas przetwarzania {filename}: {e}")
        return False

def generate_info_json(files):
    cards = []
    card_count = 0
    
    for f in files:
        basename = os.path.basename(f)
        name_no_ext = os.path.splitext(basename)[0]
        
        if "back" in name_no_ext:
            continue
            
        try:
            # Wyodrębnienie numeru karty z nazwy np. Zodiak_05 -> 5
            card_id = int(name_no_ext.replace("Zodiak_", ""))
            cards.append({
                "id": card_id,
                "file_base": name_no_ext
            })
            card_count += 1
        except ValueError:
            print(f"[OSTRZEZENIE] Pomijam plik o nieprawidlowym formacie numeracji: {basename}")

    info = {
        "deck_name": "Zodiak",
        "deck_id": "zodiak_physical_scans",
        "language": "pl",
        "copyright": "private",
        "card_count": card_count,
        "source": "Fizyczne skany uzytkownika z urzadzenia WIA",
        "cards": sorted(cards, key=lambda x: x["id"])
    }
    
    info_path = os.path.join(DECK_DIR, "info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Wygenerowano plik metadanych: {info_path}")

def main():
    print("====================================================")
    print("ASYSTENT BIBLIOTEKI - IMPORT TALII ZODIAK")
    print("====================================================")
    
    setup_directories()
    source_files = get_source_images()
    
    success_count = 0
    print("Rozpoczynam konwersje i optymalizacje obrazow...")
    for file_path in source_files:
        if process_image(file_path):
            success_count += 1
            
    generate_info_json(source_files)
    
    print("====================================================")
    print(f"SUKCES! Pomyslnie zaimportowano {success_count}/{len(source_files)} plikow.")
    print(f"Talia 'Zodiak' zostala dodana do biblioteki systemowej.")
    print("====================================================")

if __name__ == "__main__":
    main()
