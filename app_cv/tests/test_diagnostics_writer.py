# -*- coding: utf-8 -*-
import unittest
import os
import json
import tempfile
import shutil
from tarotvision.status.diagnostics_writer import DiagnosticsWriter

class TestDiagnosticsWriter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_initialization_creates_dir(self):
        nested_dir = os.path.join(self.test_dir, "nested_logs")
        writer = DiagnosticsWriter(nested_dir)
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.isdir(nested_dir))

    def test_reset_on_start(self):
        filename = "test_metrics.jsonl"
        filepath = os.path.join(self.test_dir, filename)
        
        # Tworzymy plik z testową zawartością
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("existing content\n")
            
        # Inicjalizujemy bez resetowania
        writer1 = DiagnosticsWriter(self.test_dir, filename=filename, reset_on_start=False)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "existing content\n")
            
        # Inicjalizujemy z resetowaniem
        writer2 = DiagnosticsWriter(self.test_dir, filename=filename, reset_on_start=True)
        self.assertFalse(os.path.exists(filepath)) # Plik powinien być usunięty przy inicjalizacji
        
        # Zapisujemy nową zawartość
        writer2.append({"fps": 30.0}, {}, ["01_magician"])
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertNotIn("existing content", content)
            self.assertIn("01_magician", content)

    def test_append_writes_valid_json_lines(self):
        writer = DiagnosticsWriter(self.test_dir, filename="metrics.jsonl")
        
        metrics1 = {"fps": 25.5, "latency_ms": 40.0}
        runtime1 = {"threshold": 120}
        cards1 = ["00_fool"]
        
        metrics2 = {"fps": 30.0, "latency_ms": 33.3}
        runtime2 = {"threshold": 120}
        cards2 = ["00_fool", "02_high_priestess"]
        
        # Zapis dwóch klatek
        writer.append(metrics1, runtime1, cards1)
        writer.append(metrics2, runtime2, cards2)
        
        filepath = os.path.join(self.test_dir, "metrics.jsonl")
        self.assertTrue(os.path.exists(filepath))
        
        # Odczyt i weryfikacja linii
        lines = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    lines.append(json.loads(line.strip()))
                    
        self.assertEqual(len(lines), 2)
        
        # Pierwsza linia
        self.assertTrue(lines[0]["detected"])
        self.assertEqual(lines[0]["card_count"], 1)
        self.assertEqual(lines[0]["cards"], cards1)
        self.assertEqual(lines[0]["metrics"], metrics1)
        self.assertEqual(lines[0]["runtime"], runtime1)
        self.assertIn("timestamp", lines[0])
        
        # Druga linia
        self.assertTrue(lines[1]["detected"])
        self.assertEqual(lines[1]["card_count"], 2)
        self.assertEqual(lines[1]["cards"], cards2)
        self.assertEqual(lines[1]["metrics"], metrics2)
        self.assertEqual(lines[1]["runtime"], runtime2)

    def test_append_handles_empty_state(self):
        writer = DiagnosticsWriter(self.test_dir, filename="empty_metrics.jsonl")
        writer.append({}, {}, [])
        
        filepath = os.path.join(self.test_dir, "empty_metrics.jsonl")
        with open(filepath, "r", encoding="utf-8") as f:
            line = json.loads(f.read().strip())
            
        self.assertFalse(line["detected"])
        self.assertEqual(line["card_count"], 0)
        self.assertEqual(line["cards"], [])
        self.assertEqual(line["metrics"], {})
        self.assertEqual(line["runtime"], {})

if __name__ == '__main__':
    unittest.main()
