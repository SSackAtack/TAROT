import os
import sys
import json
import requests
import concurrent.futures
from PIL import Image
import io

# Konfiguracja ścieżek
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biblioteka_talii", "rider-waite-smith"))
MASTERY_DIR = os.path.join(BASE_DIR, "mastery")
PROD_KARTY_DIR = os.path.join(BASE_DIR, "produkcja", "karty")
PROD_CV_DIR = os.path.join(BASE_DIR, "produkcja", "wzorce_cv")
PROD_THUMB_DIR = os.path.join(BASE_DIR, "produkcja", "miniatury")

# API Wikipedia Commons do pobrania 100 obrazów (akurat jest ich około 78 JPGów RWS_Tarot_*)
WIKI_API_URL = "https://commons.wikimedia.org/w/api.php"

def setup_directories():
    for d in [MASTERY_DIR, PROD_KARTY_DIR, PROD_CV_DIR, PROD_THUMB_DIR]:
        os.makedirs(d, exist_ok=True)
    print(f"📁 Zbudowano strukturę katalogów w {BASE_DIR}")

def get_image_list():
    """Pobiera listę kart JPG z Wikimedia Commons mających prefix RWS_Tarot"""
    print("🔍 Szukam oryginalnych skanów na Wikimedia Commons...")
    params = {
        "action": "query",
        "list": "allimages",
        "aiprefix": "RWS_Tarot",
        "ailimit": 500,
        "format": "json"
    }
    
    headers = {
        "User-Agent": "TarotVision/1.0 (https://github.com/SSackAtack/TAROT) python-requests/2.32.3"
    }
    response = requests.get(WIKI_API_URL, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    images = []
    # Filtrujemy tylko JPG by uniknąć ikon wektorowych i duplikatów
    for img in data.get("query", {}).get("allimages", []):
        if img["name"].lower().endswith(".jpg"):
            images.append({
                "name": img["name"].replace(".jpg", "").replace("RWS_Tarot_", "").lower(),
                "url": img["url"]
            })
            
    print(f"✅ Znaleziono {len(images)} kart w najwyższej rozdzielczości.")
    return images

def process_card(img_data):
    name = img_data["name"]
    url = img_data["url"]
    
    try:
        # 1. Pobierz mastera
        headers = {
            "User-Agent": "TarotVision/1.0 (https://github.com/SSackAtack/TAROT) python-requests/2.32.3"
        }
        resp = requests.get(url, stream=True, headers=headers)
        resp.raise_for_status()
        raw_bytes = resp.content
        
        # Zapisz oryginał do mastery (bez kompresji)
        master_path = os.path.join(MASTERY_DIR, f"{name}.jpg")
        with open(master_path, 'wb') as f:
            f.write(raw_bytes)
            
        # 2. Przetwórz za pomocą Pillow (Derywaty)
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # Upewnijmy się że obraz to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # A) Produkcja - Wizualizacja AR (WebP, wysokość 1200px)
            ar_height = 1200
            ar_width = int(ar_height * img.width / img.height)
            img_ar = img.resize((ar_width, ar_height), Image.Resampling.LANCZOS)
            img_ar.save(os.path.join(PROD_KARTY_DIR, f"{name}.webp"), "WEBP", quality=90)
            
            # B) Produkcja - CV YOLO (JPG, wysokość 500px)
            cv_height = 500
            cv_width = int(cv_height * img.width / img.height)
            img_cv = img.resize((cv_width, cv_height), Image.Resampling.LANCZOS)
            img_cv.save(os.path.join(PROD_CV_DIR, f"{name}.jpg"), "JPEG", quality=85)
            
            # C) Produkcja - Miniaturki UI (WebP, wysokość 150px)
            thumb_height = 150
            thumb_width = int(thumb_height * img.width / img.height)
            img_thumb = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            img_thumb.save(os.path.join(PROD_THUMB_DIR, f"{name}_thumb.webp"), "WEBP", quality=80)
            
        print(f"  --> Zakończono: {name}")
        return True
    except Exception as e:
        print(f"❌ Błąd przy karcie {name}: {e}")
        return False

def generate_info_json(images):
    info = {
        "deck_name": "Rider-Waite-Smith",
        "deck_id": "rws_1909_wikimedia",
        "language": "en",
        "copyright": "public_domain",
        "card_count": len(images),
        "source": "Wikimedia Commons (Pamela Colman Smith Commemorative Set)",
        "cards": []
    }
    
    for i, img in enumerate(images):
        info["cards"].append({
            "id": i,
            "file_base": img["name"],
            "wiki_url": img["url"]
        })
        
    info_path = os.path.join(BASE_DIR, "info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(f"📝 Wygenerowano metadane w: {info_path}")

def main():
    print("========================================")
    print("🃏 TAROT VISION - RWS Downloader & Processor")
    print("========================================")
    
    setup_directories()
    images = get_image_list()
    
    if not images:
        print("Nie znaleziono obrazów. Kończę.")
        sys.exit(1)
        
    print(f"⚙️ Rozpoczynam pobieranie i skalowanie (używam wielu wątków)...")
    
    # Wykorzystujemy pulę wątków by pobrać to bardzo szybko
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_card, images)
        for r in results:
            if r: success_count += 1
            
    generate_info_json(images)
    print("========================================")
    print(f"🎉 SUKCES! Pomyślnie przygotowano {success_count}/{len(images)} kart.")
    print(f"Katalog z assetami: {BASE_DIR}")

if __name__ == "__main__":
    main()
