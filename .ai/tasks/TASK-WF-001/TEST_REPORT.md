# Raport z Testów — TASK-WF-001

## 1. Testy Automatyczne Backend (Python)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv"; python -m unittest discover -s app_cv\tests -v`

### Wynik konsoli:
```text
Ran 171 tests in 0.449s
OK
```

---

## 2. Testy Kompilacji Plików (Python Compilation)
* **Status:** `PASS`
* **Komendy uruchomienia:** 
  - `python -m py_compile app_cv/main.py`
  - `python -m compileall app_cv/tarotvision`

### Wynik konsoli:
```text
Listing 'tarotvision'...
Listing 'tarotvision\\camera'...
Listing 'tarotvision\\pipelines'...
Listing 'tarotvision\\preview'...
Listing 'tarotvision\\runtime'...
Compiling 'tarotvision\\runtime\\__init__.py'...
Listing 'tarotvision\\status'...
```

---

## 3. Testy Kompilacji Frontend (Node/Vite)
* **Status:** `PASS`
* **Komenda uruchomienia:** `npm --prefix app_ar run build`

### Wynik konsoli:
```text
vite v8.0.14 building client environment for production...
transforming...✓ 24 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:   0.31 kB
dist/assets/index-BpTtr0Lx.css   17.21 kB │ gzip:   4.18 kB
dist/assets/index-CQdc6cxv.js   608.59 kB │ gzip: 156.46 kB
✓ built in 281ms
```
