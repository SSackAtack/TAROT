# -*- coding: utf-8 -*-
import unittest
import ast
import os

class MainStaticAuditVisitor(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Name(self, node):
        # Sprawdzamy wystąpienia surowej usuniętej zmiennej camera_index
        if node.id == "camera_index":
            self.errors.append(
                f"Wykryto zakazane odwołanie do starej zmiennej globalnej 'camera_index' na linii {node.lineno}. "
                f"Użyj 'camera_session.camera_index' zamiast 'camera_index'."
            )
        
        # Sprawdzamy wystąpienia surowej usuniętej zmiennej cap
        if node.id == "cap":
            self.errors.append(
                f"Wykryto zakazane odwołanie do starej zmiennej 'cap' na linii {node.lineno}. "
                f"Użyj 'camera_session' zamiast 'cap'."
            )

        # Sprawdzamy wystąpienia usuniętych zmiennych stanu legacy pipeline
        forbidden_legacy_vars = [
            "boost_frames_remaining",
            "boost_after_layout_change_frames",
            "debounce_state",
            "inactive_index",
            "tracked_boxes_by_name"
        ]
        if node.id in forbidden_legacy_vars:
            self.errors.append(
                f"Wykryto zakazane odwołanie do starej zmiennej stanu legacy pipeline '{node.id}' na linii {node.lineno}. "
                f"Ta zmienna powinna być hermetyzowana wewnątrz klasy StateFirstLegacyPipeline."
            )
            
        self.generic_visit(node)


class TestMainStaticAudit(unittest.TestCase):
    def setUp(self):
        self.main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))

    def test_no_dead_references_in_main(self):
        """Weryfikuje, że w main.py nie ma zakazanych, surowych odwołań do camera_index lub cap."""
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")

        with open(self.main_py_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Próba kompilacji do drzewa AST
        try:
            tree = ast.parse(source, filename="main.py")
        except SyntaxError as e:
            self.fail(f"Błąd składni w main.py podczas parsowania AST: {e}")

        # Audyt kodu przy użyciu NodeVisitora
        visitor = MainStaticAuditVisitor()
        visitor.visit(tree)

        # Jeśli wykryto błędy, zgłaszamy je w teście
        if visitor.errors:
            error_msg = "\n".join(visitor.errors)
            self.fail(f"Statyczny audyt main.py wykrył problemy:\n{error_msg}")

    def test_state_first_diff_pipeline_is_flag_gated(self):
        """Nowy pipeline diff może istnieć tylko za jawnie ustawioną flagą runtime."""
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")

        with open(self.main_py_path, "r", encoding="utf-8") as f:
            source = f.read()

        forbidden_tokens = [
            "StateFirstLegacyPipeline",
            "legacy_pipeline",
            "USE_SNAPSHOT_FIRST_CV",
            "USE_TABLE_CARD_DETECTION",
            "STATE-FIRST OPTIMIZATION",
        ]
        found = [token for token in forbidden_tokens if token in source]
        if found:
            self.fail(
                "main.py nie powinien wracać do starego legacy fallbacku; wykryto tokeny: "
                + ", ".join(found)
            )
        self.assertIn('PIPELINE_MODE = os.environ.get("TAROTVISION_PIPELINE", "snapshot_first")', source)
        self.assertIn('if PIPELINE_MODE == "state_first_diff":', source)
        self.assertIn("vision_pipeline = StateFirstDiffPipeline(", source)
        self.assertIn("vision_pipeline = snapshot_pipeline", source)

    def test_main_supports_state_first_session_commands(self):
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")

        with open(self.main_py_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertIn("snapshot_session_store.start_session()", source)
        self.assertIn("pending_session_empty_capture = True", source)
        self.assertIn("snapshot_session_store.capture_empty_reference(capture_frame)", source)
        self.assertIn("snapshot_session_store.end_session()", source)
        self.assertIn('message.type == "session_resync_table"', source)

    def test_websocket_thread_is_disabled_in_test_mode(self):
        """Import main.py w testach nie powinien startować serwera WebSocket."""
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")

        with open(self.main_py_path, "r", encoding="utf-8") as f:
            source = f.read()

        expected = (
            'if os.environ.get("TAROTVISION_TEST_MODE") != "1":\n'
            '    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)\n'
            '    ws_thread.start()'
        )
        self.assertIn(expected, source)

    def test_main_publishes_operator_explainability(self):
        """Payload operatora powinien zawierać uporządkowaną diagnostykę CV Explain."""
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")

        with open(self.main_py_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertIn("from tarotvision.operator_explainability import build_cv_explainability", source)
        self.assertIn('"explainability": build_cv_explainability(', source)

if __name__ == '__main__':
    unittest.main()
