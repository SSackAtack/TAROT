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

    def _read_main_source(self):
        self.assertTrue(os.path.exists(self.main_py_path), f"Plik {self.main_py_path} nie istnieje")
        with open(self.main_py_path, "r", encoding="utf-8") as f:
            return f.read()

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

    def test_snapshot_first_is_the_only_runtime_pipeline(self):
        """Weryfikuje, że main.py nie utrzymuje już runtime'owego fallbacku state-first."""
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
                "main.py powinien uruchamiać wyłącznie SnapshotFirstPipeline; wykryto legacy tokeny: "
                + ", ".join(found)
            )

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
        source = self._read_main_source()

        self.assertIn("from tarotvision.operator_explainability import build_cv_explainability", source)
        self.assertIn('"explainability": build_cv_explainability(', source)

    def test_main_handles_autotune_without_auto_apply(self):
        """Autotuning ma publikować rekomendację, ale nie stosować jej bez komendy operatora."""
        source = self._read_main_source()

        self.assertIn("from tarotvision.autotune_session import AutotuneSession", source)
        self.assertIn("from tarotvision.autotune_profiles import generate_candidate_profiles", source)
        self.assertIn("from tarotvision.autotune_scoring import choose_best_profile_result", source)
        self.assertIn('message.type == "autotune_start"', source)
        self.assertIn('message.type == "autotune_apply"', source)
        self.assertIn("set_recommendation", source)
        self.assertNotIn("auto_apply_recommendation", source)

    def test_main_saves_autotune_recommendation_with_metadata(self):
        """autotune_save powinien zapisywać rekomendację z metadanymi, nie surową mapę parametrów."""
        source = self._read_main_source()

        self.assertIn('message.type == "autotune_save"', source)
        self.assertIn("save_autotune_recommendation", source)
        self.assertIn("load_parameters", source)
        self.assertNotIn('profile_store.save(message.name, autotune_session.recommendation["profile"])', source)

if __name__ == '__main__':
    unittest.main()
