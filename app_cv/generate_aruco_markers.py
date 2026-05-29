"""Generowanie markerow ArUco do wydruku dla TarotVision.

Uruchomienie:
    python app_cv/generate_aruco_markers.py

Tworzy:
    - Pojedyncze markery PNG (aruco_10.png, aruco_11.png, aruco_12.png, aruco_13.png)
    - Zbiorczy arkusz A4 do wydruku (aruco_print_sheet.png)

Wszystko zapisywane do: docs/aruco/
"""

import os
import sys

import cv2
import numpy as np


# Konfiguracja markerow — musi byc zgodna z table_calibration.py
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_IDS = {
    10: "LEWY GORNY",
    11: "PRAWY GORNY",
    12: "PRAWY DOLNY",
    13: "LEWY DOLNY",
}

# Rozmiar markera w pikselach (300px przy 300 DPI = ~2.54 cm = 1 cal)
MARKER_SIZE_PX = 300
# Margines bialy wokol markera (potrzebny do poprawnej detekcji!)
MARGIN_PX = 60

# Rozmiar arkusza A4 przy 300 DPI (orientacja pozioma)
A4_WIDTH = 3508   # 297mm
A4_HEIGHT = 2480  # 210mm


def generate_single_marker(marker_id, size=MARKER_SIZE_PX):
    """Wygeneruj pojedynczy marker ArUco jako obraz."""
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    return marker_img


def add_margin_and_label(marker_img, marker_id, label, margin=MARGIN_PX):
    """Dodaj bialy margines i etykiete pod markerem."""
    h, w = marker_img.shape[:2]
    label_height = 50

    # Nowy obraz z marginesem i miejscem na etykiete
    total_w = w + 2 * margin
    total_h = h + 2 * margin + label_height
    canvas = np.ones((total_h, total_w), dtype=np.uint8) * 255

    # Wklej marker na srodek
    canvas[margin:margin + h, margin:margin + w] = marker_img

    # Dodaj etykiete
    text = f"ID {marker_id} — {label}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (total_w - text_size[0]) // 2
    text_y = margin + h + margin // 2 + text_size[1]
    cv2.putText(canvas, text, (text_x, text_y), font, font_scale, 0, thickness)

    return canvas


def create_print_sheet():
    """Stworz zbiorczy arkusz A4 z 4 markerami + instrukcja rozlozenia."""
    canvas = np.ones((A4_HEIGHT, A4_WIDTH), dtype=np.uint8) * 255

    markers = {}
    for marker_id, label in MARKER_IDS.items():
        raw = generate_single_marker(marker_id)
        labeled = add_margin_and_label(raw, marker_id, label)
        markers[marker_id] = labeled

    # Uklad na arkuszu: 2x2 siatka
    m_h, m_w = list(markers.values())[0].shape[:2]
    gap_x = (A4_WIDTH - 2 * m_w) // 3
    gap_y = 200  # od gory

    positions = {
        10: (gap_x, gap_y),                          # lewy gorny
        11: (gap_x + m_w + gap_x, gap_y),            # prawy gorny
        13: (gap_x, gap_y + m_h + 100),              # lewy dolny
        12: (gap_x + m_w + gap_x, gap_y + m_h + 100),  # prawy dolny
    }

    for marker_id, (x, y) in positions.items():
        marker = markers[marker_id]
        h, w = marker.shape
        canvas[y:y + h, x:x + w] = marker

    # Tytul
    title = "TarotVision — Markery ArUco do wydruku"
    cv2.putText(canvas, title, (A4_WIDTH // 2 - 400, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)

    # Instrukcje pod markerami
    instructions_y = gap_y + 2 * m_h + 300
    instructions = [
        "INSTRUKCJA ROZLOZENIA:",
        "",
        "1. Wytnij 4 markery wzdluz bialej ramki (zostaw bialy margines!)",
        "2. Rozloz na stole/macie w nastepujacy sposob:",
        "",
        "     [ID 10]  --------  [ID 11]",
        "        |    KARTY SA    |",
        "        |   ROZKLADANE   |",
        "        |    TUTAJ       |",
        "     [ID 13]  --------  [ID 12]",
        "",
        "3. Markery musza byc plasko przylezone do powierzchni",
        "4. Bialy margines wokol markera jest WYMAGANY (min. 1 cm)",
        "5. Kamera musi widziec wszystkie 4 markery — gdy tak sie stanie,",
        "   w HUD pojawi sie 'ArUco: TAK'",
    ]

    for i, line in enumerate(instructions):
        cv2.putText(canvas, line, (200, instructions_y + i * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, 0, 1)

    return canvas


def main():
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "docs", "aruco"
    )
    os.makedirs(output_dir, exist_ok=True)

    print("Generowanie markerow ArUco dla TarotVision...")
    print(f"Slownik: DICT_4X4_50")
    print(f"Rozmiar markera: {MARKER_SIZE_PX}px ({MARKER_SIZE_PX / 300 * 2.54:.1f} cm przy 300 DPI)")
    print()

    # Pojedyncze markery
    for marker_id, label in MARKER_IDS.items():
        raw = generate_single_marker(marker_id)
        labeled = add_margin_and_label(raw, marker_id, label)
        filename = f"aruco_{marker_id}.png"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, labeled)
        print(f"  Zapisano: {filepath}  (ID {marker_id} — {label})")

    # Arkusz zbiorczy
    sheet = create_print_sheet()
    sheet_path = os.path.join(output_dir, "aruco_print_sheet.png")
    cv2.imwrite(sheet_path, sheet)
    print(f"\n  Arkusz do wydruku: {sheet_path}")
    print(f"\n--- Gotowe! Wydrukuj arkusz na drukarce i wytnij markery. ---")


if __name__ == "__main__":
    main()
