import os
from pathlib import Path

def validate_recording_path(path_str):
    """Waliduje ścieżkę zapisu nagrań.
    
    Zwraca tuple (bool, str) - (valid, message).
    """
    if not path_str or not path_str.strip():
        return False, "Ścieżka nie może być pusta"
        
    path_str = path_str.strip()
    
    # Blokowanie path traversal i podejrzanych sekwencji
    if ".." in path_str:
        return False, "Ścieżka nie może zawierać sekwencji '..'"
        
    try:
        path = Path(path_str)
        # Rozwiązujemy absolutną ścieżkę
        resolved_path = path.resolve()
        
        # Ochrona przed modyfikacją katalogów systemowych (Windows i Unix)
        system_dirs = [
            "c:\\windows", "c:\\program files", "c:\\program files (x86)",
            "/etc", "/var", "/sys", "/proc", "/boot"
        ]
        resolved_str = str(resolved_path).lower()
        for sys_dir in system_dirs:
            if resolved_str == sys_dir or resolved_str.startswith(sys_dir + os.sep):
                return False, "Dostęp zabroniony: katalog systemowy"
                
        # Sprawdzamy czy ścieżka istnieje i czy jest plikiem
        if resolved_path.exists():
            if resolved_path.is_file():
                return False, f"Podana ścieżka jest plikiem, a nie katalogiem: {resolved_path.name}"
            # Sprawdzenie uprawnień do zapisu w istniejącym katalogu
            if not os.access(resolved_path, os.W_OK):
                return False, "Brak uprawnień do zapisu w wybranym katalogu"
            return True, f"Katalog istnieje i jest gotowy: {resolved_path}"
        else:
            # Katalog nie istnieje - spróbujmy go utworzyć
            try:
                resolved_path.mkdir(parents=True, exist_ok=True)
                return True, f"Utworzono nowy katalog zapisu: {resolved_path}"
            except PermissionError:
                return False, "Brak uprawnień do utworzenia katalogu zapisu"
            except Exception as exc:
                return False, f"Błąd podczas tworzenia katalogu: {str(exc)}"
                
    except Exception as exc:
        return False, f"Niepoprawny format ścieżki: {str(exc)}"
