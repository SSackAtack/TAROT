# -*- coding: utf-8 -*-
import unittest
import numpy as np
from tarotvision.pipelines import VisionPipeline

class MockVisionPipeline(VisionPipeline):
    def process_frame(self, frame):
        return {
            "cards": [],
            "metrics": {"fps": 30.0},
            "warnings": [],
            "display_frame": frame.copy()
        }


class TestPipelinesContract(unittest.TestCase):
    def test_mock_pipeline_satisfies_contract(self):
        pipeline = MockVisionPipeline()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = pipeline.process_frame(frame)
        
        # Weryfikacja kontraktu wyjściowego
        self.assertIn("cards", result)
        self.assertIn("metrics", result)
        self.assertIn("warnings", result)
        self.assertIn("display_frame", result)
        
        self.assertEqual(result["cards"], [])
        self.assertEqual(result["metrics"]["fps"], 30.0)
        self.assertEqual(result["warnings"], [])
        self.assertTrue(isinstance(result["display_frame"], np.ndarray))

if __name__ == '__main__':
    unittest.main()
