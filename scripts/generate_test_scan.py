import cv2
import numpy as np
import os
import argparse

def create_synthetic_dark_sheet(output_path):
    width, height = 2000, 3000
    sheet = np.zeros((height, width, 3), dtype=np.uint8)
    # Dodanie szumu tła skanera
    noise = np.random.normal(10, 2, (height, width, 3)).astype(np.uint8)
    sheet = cv2.add(sheet, noise)

    # Karta 1: THE FOOL
    card1_w, card1_h = 500, 860
    card1 = np.ones((card1_h, card1_w, 3), dtype=np.uint8) * 220
    cv2.rectangle(card1, (20, 20), (card1_w - 20, card1_h - 20), (180, 180, 180), -1)
    cv2.putText(card1, "THE FOOL", (80, card1_h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 50, 50), 4, cv2.LINE_AA)
    cv2.circle(card1, (card1_w // 2, card1_h // 2 - 150), 100, (100, 150, 220), -1)
    
    # Karta 2: THE MAGICIAN
    card2 = np.ones((card1_h, card1_w, 3), dtype=np.uint8) * 230
    cv2.rectangle(card2, (20, 20), (card1_w - 20, card1_h - 20), (190, 190, 190), -1)
    cv2.putText(card2, "THE MAGICIAN", (40, card1_h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 50, 50), 4, cv2.LINE_AA)
    cv2.circle(card2, (card1_w // 2, card1_h // 2 - 150), 100, (220, 150, 100), -1)

    def paste_rotated_card(bg, card, center, angle_deg):
        ch, cw = card.shape[:2]
        card_mask = np.ones((ch, cw), dtype=np.uint8) * 255
        rot_mat = cv2.getRotationMatrix2D((cw // 2, ch // 2), angle_deg, 1.0)
        rotated_card = cv2.warpAffine(card, rot_mat, (cw, ch), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        rotated_mask = cv2.warpAffine(card_mask, rot_mat, (cw, ch), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        
        tx = center[0] - cw // 2
        ty = center[1] - ch // 2
        
        roi = bg[ty:ty+ch, tx:tx+cw]
        mask_3d = np.repeat(rotated_mask[:, :, np.newaxis], 3, axis=2)
        pasted = np.where(mask_3d == 255, rotated_card, roi)
        bg[ty:ty+ch, tx:tx+cw] = pasted

    paste_rotated_card(sheet, card1, (600, 1200), -12)
    paste_rotated_card(sheet, card2, (1400, 1600), 8)

    cv2.imwrite(output_path, sheet)
    print(f" -> Wygenerowano syntetyczny ciemny skan: {output_path}")

def create_synthetic_light_sheet(output_path):
    width, height = 2000, 3000
    sheet = np.ones((height, width, 3), dtype=np.uint8) * 245
    noise = np.random.normal(2, 1, (height, width, 3)).astype(np.uint8)
    sheet = cv2.subtract(sheet, noise)

    # Karta 1: THE EMPRESS
    card1_w, card1_h = 500, 860
    card1 = np.ones((card1_h, card1_w, 3), dtype=np.uint8) * 190
    cv2.rectangle(card1, (20, 20), (card1_w - 20, card1_h - 20), (150, 150, 150), -1)
    cv2.putText(card1, "THE EMPRESS", (60, card1_h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 50, 50), 4, cv2.LINE_AA)
    cv2.circle(card1, (card1_w // 2, card1_h // 2 - 150), 100, (100, 100, 100), -1)
    
    # Karta 2: THE EMPEROR
    card2 = np.ones((card1_h, card1_w, 3), dtype=np.uint8) * 180
    cv2.rectangle(card2, (20, 20), (card1_w - 20, card1_h - 20), (140, 140, 140), -1)
    cv2.putText(card2, "THE EMPEROR", (50, card1_h // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (50, 50, 50), 4, cv2.LINE_AA)
    cv2.circle(card2, (card1_w // 2, card1_h // 2 - 150), 100, (120, 120, 120), -1)

    def paste_rotated_card(bg, card, center, angle_deg):
        ch, cw = card.shape[:2]
        card_mask = np.ones((ch, cw), dtype=np.uint8) * 255
        rot_mat = cv2.getRotationMatrix2D((cw // 2, ch // 2), angle_deg, 1.0)
        rotated_card = cv2.warpAffine(card, rot_mat, (cw, ch), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(245,245,245))
        rotated_mask = cv2.warpAffine(card_mask, rot_mat, (cw, ch), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        
        tx = center[0] - cw // 2
        ty = center[1] - ch // 2
        
        roi = bg[ty:ty+ch, tx:tx+cw]
        mask_3d = np.repeat(rotated_mask[:, :, np.newaxis], 3, axis=2)
        pasted = np.where(mask_3d == 255, rotated_card, roi)
        bg[ty:ty+ch, tx:tx+cw] = pasted

    paste_rotated_card(sheet, card1, (600, 1200), -5)
    paste_rotated_card(sheet, card2, (1400, 1600), 12)

    cv2.imwrite(output_path, sheet)
    print(f" -> Wygenerowano syntetyczny jasny skan: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generator syntetycznych skanow kart w celach testowych i reprodukcyjnych.")
    parser.add_argument("--output-dir", default="scans_input", help="Katalog wyjsciowy dla arkuszy (domyślnie: scans_input)")
    parser.add_argument("--dark-only", action="store_true", help="Generuje tylko ciemny skan")
    parser.add_argument("--light-only", action="store_true", help="Generuje tylko jasny skan")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=== INICJALIZACJA TESTOWYCH ARKUSZY SYNTETYCZNYCH ===")
    
    if not args.light_only:
        create_synthetic_dark_sheet(os.path.join(args.output_dir, "synthetic_scan.jpg"))
        
    if not args.dark_only:
        create_synthetic_light_sheet(os.path.join(args.output_dir, "synthetic_scan_light.jpg"))
        
    print("=====================================================")
    print("[SUKCES] Arkusze testowe gotowe do użycia w scripts/process_scans.py")
