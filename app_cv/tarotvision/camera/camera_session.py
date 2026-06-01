# -*- coding: utf-8 -*-
"""
Moduł zarządzania sesją kamery sprzętowej (CameraSession) TarotVision.
"""
import os
import json
import logging
import cv2
from tarotvision.camera_controls import read_camera_control

class CameraSession:
    def __init__(self, log_dir, camera_width=1280, camera_height=720):
        self.log_dir = log_dir
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.settings_file = os.path.join(log_dir, "camera_settings.json")
        
        self.capture = None
        self.camera_index = 0
        self.frame_width = camera_width
        self.frame_height = camera_height
        self.camera_set_cache = {}
        self.supported_camera_controls = {}
        
        # Tworzenie katalogu logów, jeśli nie istnieje
        os.makedirs(self.log_dir, exist_ok=True)

    def open(self, index=0):
        """Otwiera kamerę pod zadanym indeksem."""
        self.camera_index = index
        self.capture = cv2.VideoCapture(index)
        
        if not self.capture.isOpened():
            logging.warning(f"[CameraSession] Nie udało się otworzyć kamery pod indeksem {index}")
            return False
            
        self._configure_capture()
        self._restore_settings()
        self.probe_controls()
        logging.info(f"[CameraSession] Kamera {index} otwarta. Rozdzielczość: {self.frame_width}x{self.frame_height}")
        return True

    def is_opened(self):
        """Zwraca True, jeśli kamera jest otwarta."""
        return self.capture is not None and self.capture.isOpened()

    def read(self):
        """Odczytuje klatkę z kamery."""
        if not self.is_opened():
            return False, None
        return self.capture.read()

    def switch(self, index):
        """Zamyka obecną kamerę i otwiera nową."""
        logging.info(f"[CameraSession] Przełączanie kamery z {self.camera_index} na {index}")
        self.close()
        return self.open(index)

    def close(self):
        """Zapisuje ustawienia i zamyka kamerę."""
        if self.capture is not None:
            self._save_settings()
            self.capture.release()
            self.capture = None
            logging.info(f"[CameraSession] Kamera {self.camera_index} zamknięta.")

    def set_control(self, param, value):
        """Ustawia sprzętowy parametr kamery, zapisuje go do cache i pliku ustawień."""
        if not self.is_opened():
            return False
            
        CAMERA_PROP_IDS = {
            "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
            "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
            "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
            "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
            "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
            "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
        }
        
        if param in CAMERA_PROP_IDS:
            prop_id = CAMERA_PROP_IDS[param]
            val = float(value)
            self.capture.set(prop_id, val)
            
            # Zapisujemy w cache naszą zadaną wartość
            self.camera_set_cache[param] = val
            
            # Automatyczny zapis po zmianie
            self._save_settings()
            
            # Aktualizacja odczytu
            self.probe_controls()
            logging.info(f"[CameraSession] Ustawiono parametr kamery {param} = {val}")
            return True
        else:
            logging.warning(f"[CameraSession] Nieznany parametr sprzętowy kamery: {param}")
            return False

    def probe_controls(self):
        """Odpytuje kamerę o obsługiwane parametry."""
        if not self.is_opened():
            return {}
            
        probes = {
            "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
            "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
            "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
            "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
            "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
            "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
        }
        
        results = {}
        for name, prop_id in probes.items():
            if name in self.camera_set_cache:
                readback = self.camera_set_cache[name]
            else:
                probe = read_camera_control(self.capture, prop_id)
                readback = probe.readback_value
                
            results[name] = {
                "supported": True if readback != -1.0 else False,
                "readback_value": readback,
            }
            
        self.supported_camera_controls = results
        return results

    def _configure_capture(self):
        """Wymusza docelową rozdzielczość kamery."""
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        self.frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.camera_width
        self.frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.camera_height

    def _save_settings(self):
        """Zapisuje obecne ustawienia sprzętowe kamery do pliku."""
        if not self.is_opened():
            return
        try:
            # Some webcams report stale or normalized values after a manual set
            # (focus often reads back as 0.0). Persist the operator-requested
            # values first, then fill missing controls from hardware readback.
            settings = {
                name: float(value)
                for name, value in self.camera_set_cache.items()
            }
            probes = {
                "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
                "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
                "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
                "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
                "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
                "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
            }
            for name, prop_id in probes.items():
                if name in settings:
                    continue
                val = self.capture.get(prop_id)
                if val is not None and val != -1.0:
                    settings[name] = float(val)
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as exc:
            logging.warning(f"[CameraSession] Nie udało się zapisać ustawień kamery: {exc}")

    def _restore_settings(self):
        """Przywraca ustawienia sprzętowe kamery z pliku."""
        if not os.path.exists(self.settings_file):
            return
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            self.camera_set_cache.update(settings)
            
            probes = {
                "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
                "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
                "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
                "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
                "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
                "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
            }
            
            # Najpierw wyłączamy automaty focusa i ekspozycji
            for name in ["CAP_PROP_AUTOFOCUS", "CAP_PROP_AUTO_EXPOSURE"]:
                if name in settings and name in probes:
                    self.capture.set(probes[name], settings[name])
                    
            for name, val in settings.items():
                if name not in ["CAP_PROP_AUTOFOCUS", "CAP_PROP_AUTO_EXPOSURE"] and name in probes:
                    self.capture.set(probes[name], val)
        except Exception as exc:
            logging.warning(f"[CameraSession] Nie udało się przywrócić ustawień kamery: {exc}")
