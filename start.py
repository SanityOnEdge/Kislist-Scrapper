#!/usr/bin/env python3
"""
KislistScraper Pro - Main Launcher
Prosty launcher do uruchamiania głównej aplikacji
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    print("KislistScraper Pro Launcher")
    print("=" * 40)

    # Sprawdź czy jesteśmy w poprawnym katalogu
    if not Path("selenium_gui.py").exists():
        print("[BŁĄD] Nie znaleziono pliku selenium_gui.py")
        print("[INFO] Uruchom skrypt z folderu KislistScraper_Pro")
        return 1

    # Sprawdź Python i moduły
    print("[INFO] Sprawdzanie wymagań...")

    try:
        import selenium
        print("[OK] Selenium")
    except ImportError:
        print("[BŁĄD] Brak modułu Selenium")
        print("[INFO] Zainstaluj: sudo pacman -S python-selenium")
        return 1

    try:
        import psutil
        print("[OK] psutil")
    except ImportError:
        print("[OSTRZEŻENIE] Brak psutil - auto-detekcja zasobów wyłączona")

    try:
        import requests
        print("[OK] requests")
    except ImportError:
        print("[BŁĄD] Brak modułu requests")
        return 1

    # Sprawdź ChromeDriver
    chromedriver_path = "/usr/bin/chromedriver"
    if Path(chromedriver_path).exists():
        print("[OK] ChromeDriver")
    else:
        print("[BŁĄD] Brak ChromeDriver")
        print("[INFO] Sprawdź ścieżkę: which chromedriver")
        return 1

    print("\n[OK] Wszystkie wymagania spełnione.")
    print("[INFO] Inicjalizacja interfejsu graficznego (GUI)...\n")

    # Uruchom główną aplikację
    try:
        subprocess.run([sys.executable, "selenium_gui.py"])
    except KeyboardInterrupt:
        print("\n[INFO] Zamknięto przez użytkownika")
    except Exception as e:
        print(f"\n[BŁĄD] Błąd uruchamiania: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
