import os
import json
import sys

def print_banner(text, success=True):
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    border = "=" * len(text)
    print(f"\n{color}{border}\n{text}\n{border}{reset}\n")

def validate():
    success = True
    manifest_path = "app_ar/public/decks_manifest.json"
    active_path = "app_ar/public/active_decks.json"
    
    print("Rozpoczynam rygorystyczną walidację manifestu talii i konfiguracji aktywnej sesji...")
    
    # 1. Check if files exist
    if not os.path.exists(manifest_path):
        print(f"[-] BŁĄD: Brak pliku manifestu w ścieżce {manifest_path}")
        return False
    if not os.path.exists(active_path):
        print(f"[-] BŁĄD: Brak pliku aktywnych talii w ścieżce {active_path}")
        return False
        
    # 2. Parse JSONs
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"[+] Pomyślnie wczytano manifest talii (Wersja: {manifest.get('version')})")
    except Exception as e:
        print(f"[-] BŁĄD: Manifest talii nie jest poprawnym plikiem JSON: {e}")
        return False
        
    try:
        with open(active_path, "r", encoding="utf-8") as f:
            active_data = json.load(f)
        print(f"[+] Pomyślnie wczytano plik aktywnych talii (Wersja: {active_data.get('version')})")
    except Exception as e:
        print(f"[-] BŁĄD: Plik aktywnych talii nie jest poprawnym plikiem JSON: {e}")
        return False

    # 3. Validate decks manifest structure
    decks = manifest.get("decks", [])
    if not isinstance(decks, list) or len(decks) == 0:
        print("[-] BŁĄD: Brak zdefiniowanych talii w manifeście.")
        success = False
        
    deck_ids = set()
    print(f"\nWalidacja {len(decks)} talii w manifeście:")
    for deck in decks:
        d_id = deck.get("id")
        d_name = deck.get("display_name")
        prefix = deck.get("prefix")
        card_count = deck.get("card_count")
        has_back = deck.get("has_back")
        ar_template = deck.get("ar_path_template")
        back_texture = deck.get("back_texture")
        cv_path = deck.get("cv_path")
        
        print(f"\n  Talia: '{d_name}' (ID: '{d_id}')")
        
        # Check required fields
        if not d_id:
            print("    [-] BŁĄD: Brak pola 'id'!")
            success = False
            continue
            
        if d_id in deck_ids:
            print(f"    [-] BŁĄD: Zdublowane 'id': '{d_id}'!")
            success = False
        deck_ids.add(d_id)
        
        if not d_name or not prefix:
            print("    [-] BŁĄD: Brak 'display_name' lub 'prefix'!")
            success = False
            
        # Standard card count validation
        if card_count != 78:
            print(f"    [-] BŁĄD: Liczba kart 'card_count' wynosi {card_count}, a wymagane jest dokładnie 78!")
            success = False
        else:
            print(f"    [+] Liczba kart: 78 (OK)")
            
        if has_back is not True:
            print("    [-] BŁĄD: Pole 'has_back' musi mieć wartość true!")
            success = False
        else:
            print("    [+] Rewers aktywny (OK)")
            
        # Check paths existence
        if cv_path:
            # Normalize path for check
            normalized_cv = os.path.normpath(cv_path)
            if not os.path.exists(normalized_cv):
                print(f"    [-] BŁĄD: Ścieżka CV nie istnieje na dysku: '{normalized_cv}'!")
                success = False
            else:
                print(f"    [+] Ścieżka CV istnieje: '{normalized_cv}' (OK)")
        else:
            print("    [-] BŁĄD: Brak zdefiniowanego 'cv_path'!")
            success = False
            
        # Check ar assets
        if ar_template and back_texture:
            # Check back texture path
            back_full_path = os.path.normpath("app_ar/public" + back_texture)
            if not os.path.exists(back_full_path):
                print(f"    [-] BŁĄD: Plik rewersu nie istnieje: '{back_full_path}'!")
                success = False
            else:
                print(f"    [+] Plik rewersu istnieje: '{back_texture}' (OK)")
                
            # Check sample card template path (e.g. index 00)
            sample_path = ar_template.replace("{index}", "00")
            sample_full_path = os.path.normpath("app_ar/public" + sample_path)
            if not os.path.exists(sample_full_path):
                print(f"    [-] BŁĄD: Przykładowy plik karty nie istnieje: '{sample_full_path}' (Sprawdź prefix/nazwę)!")
                success = False
            else:
                print(f"    [+] Przykładowe pliki AR istnieją (Szablon: '{ar_template}') (OK)")
        else:
            print("    [-] BŁĄD: Brak 'ar_path_template' lub 'back_texture'!")
            success = False

    # 4. Validate active decks session config
    active_decks = active_data.get("active_decks", [])
    max_active = manifest.get("default_max_active_decks", 3)
    
    print(f"\nWalidacja konfiguracji aktywnych talii (Limit: 1-{max_active} talie):")
    print(f"  Aktywne talie w tej sesji: {active_decks}")
    
    if not isinstance(active_decks, list):
        print("  [-] BŁĄD: 'active_decks' w active_decks.json musi być listą!")
        success = False
        return False

    if len(active_decks) < 1 or len(active_decks) > max_active:
        print(f"  [-] BŁĄD: Liczba aktywnych talii wynosi {len(active_decks)}. Dozwolony limit to od 1 do {max_active}!")
        success = False
    else:
        print(f"  [+] Liczba aktywnych talii mieści się w limicie 1-{max_active} (OK)")
        
    for act_id in active_decks:
        if act_id not in deck_ids:
            print(f"  [-] BŁĄD: Aktywna talia '{act_id}' nie istnieje w manifeście dostępnych talii!")
            success = False
        else:
            print(f"  [+] Aktywna talia '{act_id}' zweryfikowana pomyślnie w manifeście (OK)")
            
    return success

if __name__ == "__main__":
    is_valid = validate()
    if is_valid:
        print_banner("WALIDACJA ZAKOŃCZONA SUKCESEM: MANIFEST I SESJA SĄ ZGODNE I SPÓJNE!", success=True)
        sys.exit(0)
    else:
        print_banner("BŁĄD WALIDACJI: WYKRYTO NIEZGODNOŚCI W PLIKACH MANIFESTU LUB SESJI!", success=False)
        sys.exit(1)
