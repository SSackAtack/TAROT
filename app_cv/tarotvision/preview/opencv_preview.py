# -*- coding: utf-8 -*-
"""
Moduł obsługi okna podglądu OpenCV (OpenCvPreview) TarotVision.
"""
import cv2
import logging
import os

class OpenCvPreview:
    def __init__(self, window_title="TarotVision - AI Detection (Wcisnij Q by wyjsc)"):
        self.window_title = window_title
        self.enabled = os.environ.get("TAROTVISION_DISABLE_OPENCV_PREVIEW", "0") != "1"

    def draw_hud(self, frame, fps, status_line=None):
        """
        Rysuje HUD diagnostyczny na klatce.
        
        Args:
            frame (numpy.ndarray): Klatka obrazu do modyfikacji.
            fps (float): Aktualna wartość FPS.
            status_line (str, optional): Dodatkowa linia statusu (np. snapshot lub szczegóły ORB).
        """
        # Rysowanie FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Rysowanie statusu
        if status_line:
            cv2.putText(frame, status_line, (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    def show(self, frame):
        """Wyświetla klatkę w oknie OpenCV."""
        if not self.enabled:
            return
        cv2.imshow(self.window_title, frame)

    def handle_keyboard(self, camera_session):
        """
        Obsługuje zdarzenia klawiatury.
        
        Args:
            camera_session (CameraSession): Instancja sesji kamery do ewentualnego przełączenia.
            
        Returns:
            str: "quit" jeśli naciśnięto 'q', "switch" jeśli zmieniono kamerę, None w przeciwnym wypadku.
        """
        if not self.enabled:
            return None
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return "quit"
        elif ord('0') <= key <= ord('5'):
            new_index = key - ord('0')
            logging.info(f"[OpenCvPreview] Żądanie przełączenia kamery na indeks: {new_index}")
            if camera_session.switch(new_index):
                return "switch"
        return None

    def close(self):
        """Zamyka wszystkie okna OpenCV."""
        if self.enabled:
            cv2.destroyAllWindows()
