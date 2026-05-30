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
            # Chcemy upewnić się, że nie jest to odwołanie globalne/lokalne do starej zmiennej.
            # Dopuszczamy tylko wystąpienie w słownikach jako klucz (co w AST jest traktowane jako Constant lub str w nowszych wersjach,
            # ale Name może wystąpić jeśli jest używane jako wartość).
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

if __name__ == '__main__':
    unittest.main()
