# -*- coding: utf-8 -*-
"""
Moduł bazowy rurociągów analizy wizyjnej (VisionPipeline) TarotVision.
"""
from abc import ABC, abstractmethod

class VisionPipeline(ABC):
    @abstractmethod
    def process_frame(self, frame):
        """
        Przetwarza klatkę obrazu.
        
        Args:
            frame (numpy.ndarray): Klatka wejściowa BGR z kamery.
            
        Returns:
            dict: Wynik analizy zawierający słownik o strukturze kontraktu wejście/wyjście.
        """
        pass
