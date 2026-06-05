# -*- coding: utf-8 -*-
"""
Moduł pomocniczy do zapisu debug snapshotów w kreatorze kalibracji (Faza Diagnostyczna).
Zapewnia automatyczną rotację plików debug do maksymalnie 10 ostatnich zestawów.
"""
import os
import json
import time
import glob
import cv2

def save_calibration_debug(frame, scenario, detected_count, expected_count, detection_debug, log_dir):
    """
    Zapisuje obraz i szczegóły detekcji do folderu logs/debug_calibration.
    Zapewnia rotację plików, utrzymując maksymalnie 10 zestawów.
    """
    if frame is None:
        return
        
    debug_dir = os.path.join(log_dir, "debug_calibration")
    try:
        os.makedirs(debug_dir, exist_ok=True)
    except Exception:
        return # Bezpieczny fallback przy braku uprawnień
        
    # Rotacja plików - utrzymujemy max 10 zestawów (para jpg + json)
    try:
        cleanup_old_debug_files(debug_dir, max_sets=10)
    except Exception:
        pass

    # Generowanie unikalnej nazwy pliku
    timestamp = int(time.time() * 1000)
    base_name = f"wizard_{scenario}_{timestamp}_det_{detected_count}_exp_{expected_count}"
    
    jpg_path = os.path.join(debug_dir, f"{base_name}.jpg")
    json_path = os.path.join(debug_dir, f"{base_name}.json")
    
    # 1. Zapis obrazu
    try:
        cv2.imwrite(jpg_path, frame)
    except Exception:
        pass
        
    # 2. Zapis metadanych
    metadata = {
        "scenario": scenario,
        "timestamp_ms": timestamp,
        "detected_count": detected_count,
        "expected_count": expected_count,
        "best_profile": detection_debug.get("best_profile") if detection_debug else None,
        "quads_final": detection_debug.get("quads_final") if detection_debug else 0,
        "background_mask_nonzero_ratio": detection_debug.get("background_mask_nonzero_ratio") if detection_debug else None,
        "profiles": []
    }
    
    if detection_debug and "profiles" in detection_debug:
        for p in detection_debug["profiles"]:
            metadata["profiles"].append({
                "name": p.get("name"),
                "mode": p.get("mode"),
                "quads": p.get("quads"),
                "contours_total": p.get("contours_total"),
                "candidates_after_quad": p.get("candidates_after_quad"),
                "min_area_rect_candidates": p.get("min_area_rect_candidates"),
                "min_area_rect_accepted": p.get("min_area_rect_accepted"),
                "reject_reasons": p.get("reject_reasons", {})
            })
            
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def cleanup_old_debug_files(debug_dir, max_sets=10):
    """
    Wyszukuje pliki json i jpg w katalogu debug i usuwa najstarsze zestawy,
    pozostawiając maksymalnie max_sets.
    """
    json_files = glob.glob(os.path.join(debug_dir, "wizard_*.json"))
    if len(json_files) < max_sets:
        return
        
    # Sortowanie plików po czasie modyfikacji (najstarsze na początku)
    json_files.sort(key=os.path.getmtime)
    
    # Pliki do usunięcia
    to_remove = json_files[:-max_sets]
    for j_path in to_remove:
        try:
            os.remove(j_path)
            # Próbujemy usunąć pasujący obraz jpg
            jpg_path = j_path.replace(".json", ".jpg")
            if os.path.exists(jpg_path):
                os.remove(jpg_path)
        except Exception:
            pass
