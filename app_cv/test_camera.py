import cv2
import time

print("="*40)
print("[DIAGNOSTYKA] NARZĘDZIE DIAGNOSTYCZNE KAMER")
print("="*40)

backends = [
    ("Domyślny (MSMF)", cv2.CAP_ANY),
    ("DirectShow", cv2.CAP_DSHOW)
]

for backend_name, backend_flag in backends:
    print(f"\n--- Testowanie silnika: {backend_name} ---")
    
    for i in range(5):
        print(f"Sprawdzam indeks {i}... ", end="", flush=True)
        cap = cv2.VideoCapture(i, backend_flag)
        
        if not cap.isOpened():
            print("Brak / Nie można otworzyć.")
            cap.release()
            continue
            
        print("Otwarte! Czytanie klatki... ", end="", flush=True)
        ret, frame = cap.read()
        
        if not ret:
            print("BŁĄD. Otwarto urządzenie, ale read() zwraca False (Czarny Ekran/Pusty Strumień).")
        else:
            if frame is None:
                print("BŁĄD. Klatka to 'None'.")
            else:
                h, w, c = frame.shape
                # Sprawdzanie czarnych klatek (jeśli wszystkie piksele to zera)
                if not frame.any():
                    print(f"SUKCES CZYTANIA [{w}x{h}], ALE KLATKA JEST CAŁKOWICIE CZARNA (0,0,0)!")
                else:
                    print(f"PEŁEN SUKCES! Wczytano poprawną klatkę wideo: rozdzielczość {w}x{h}.")
        
        cap.release()
        time.sleep(0.5)

print("\nKoniec diagnozy.")
