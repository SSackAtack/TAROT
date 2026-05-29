"""TarotVision Offline Benchmark — odtwarza nagranie MP4 przez pipeline
CV bez kamery i GUI, zapisuje metryki per-klatkę do CSV.

Uruchomienie:
    python app_cv/benchmark_video.py --video sciezka/do/nagrania.mp4 --output wyniki.csv

Opcjonalne flagi:
    --no-display     Pomija wyswietlanie okna OpenCV (headless mode)
    --max-frames N   Przetwarza tylko N pierwszych klatek
"""

import argparse
import csv
import os
import sys
import time

import cv2
import numpy as np

# Dodajemy app_cv do sciezki, zeby importy dzialaly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tarotvision.table_calibration import TableCalibration
from tarotvision.card_detection import find_card_quads
from tarotvision.metrics import RuntimeMetrics


def run_benchmark(video_path, output_path, max_frames=None, display=False):
    """Run the CV benchmark on a video file.

    Args:
        video_path:  path to MP4/AVI video file.
        output_path: path to output CSV file.
        max_frames:  optional limit on number of frames to process.
        display:     if True, show frame visualization.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"BLAD: Nie mozna otworzyc pliku wideo: {video_path}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Wideo: {video_path}")
    print(f"Klatki: {total_frames}, FPS: {video_fps:.1f}, "
          f"Rozdzielczosc: {width}x{height}")
    print(f"Zapis wynikow do: {output_path}")

    calibration = TableCalibration(table_width=width, table_height=height)
    orb = cv2.ORB_create(nfeatures=2000)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    metrics = RuntimeMetrics(maxlen=100)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "frame_number",
            "timestamp_sec",
            "preprocess_ms",
            "aruco_ms",
            "aruco_calibrated",
            "aruco_markers",
            "card_detect_ms",
            "card_quads_found",
            "feature_detect_ms",
            "total_frame_ms",
        ])

        frame_idx = 0
        while True:
            if max_frames is not None and frame_idx >= max_frames:
                break

            ret, frame = cap.read()
            if not ret:
                break

            frame_start = time.perf_counter()
            timestamp_sec = frame_idx / video_fps if video_fps > 0 else 0.0

            # Preprocessing
            preprocess_start = time.perf_counter()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = clahe.apply(gray)
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0

            # ArUco detection
            aruco_start = time.perf_counter()
            calibration.update(gray)
            aruco_ms = (time.perf_counter() - aruco_start) * 1000.0

            # Card rectangle detection
            detect_start = time.perf_counter()
            if calibration.calibrated:
                detection_input = calibration.warp_frame(frame)
            else:
                detection_input = frame
            quads = find_card_quads(detection_input) if detection_input is not None else []
            card_detect_ms = (time.perf_counter() - detect_start) * 1000.0

            # ORB feature detection
            feature_start = time.perf_counter()
            kp, des = orb.detectAndCompute(gray, None)
            feature_detect_ms = (time.perf_counter() - feature_start) * 1000.0

            total_frame_ms = (time.perf_counter() - frame_start) * 1000.0

            writer.writerow([
                frame_idx,
                round(timestamp_sec, 3),
                round(preprocess_ms, 2),
                round(aruco_ms, 2),
                calibration.calibrated,
                len(calibration.detected_marker_ids),
                round(card_detect_ms, 2),
                len(quads),
                round(feature_detect_ms, 2),
                round(total_frame_ms, 2),
            ])

            if display:
                for q in quads:
                    cv2.polylines(frame, [q], True, (0, 255, 0), 2)
                cv2.putText(frame, f"Frame: {frame_idx} | "
                           f"Quads: {len(quads)} | "
                           f"ArUco: {'TAK' if calibration.calibrated else 'NIE'}",
                           (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                           0.8, (0, 255, 255), 2)
                cv2.imshow("TarotVision Benchmark", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"  Przetworzono {frame_idx}/{total_frames} klatek "
                      f"({total_frame_ms:.1f} ms/frame)")

    cap.release()
    if display:
        cv2.destroyAllWindows()

    print(f"\nGotowe! Przetworzono {frame_idx} klatek.")
    print(f"Wyniki zapisane do: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="TarotVision Offline Benchmark — analiza nagrania wideo"
    )
    parser.add_argument("--video", required=True,
                        help="Sciezka do pliku wideo (MP4, AVI)")
    parser.add_argument("--output", default="analizy/benchmark_results.csv",
                        help="Sciezka do pliku CSV z wynikami "
                             "(domyslnie: analizy/benchmark_results.csv)")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Maksymalna liczba klatek do przetworzenia")
    parser.add_argument("--no-display", action="store_true",
                        help="Nie wyswietlaj okna podgladu")

    args = parser.parse_args()
    run_benchmark(
        video_path=args.video,
        output_path=args.output,
        max_frames=args.max_frames,
        display=not args.no_display,
    )


if __name__ == "__main__":
    main()
