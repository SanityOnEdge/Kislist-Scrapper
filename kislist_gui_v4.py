#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kislist.com Scraper v4.0 - GUI Version z pełnym scrapingiem dostawców
Program do pobierania produktów z kislist.com z pełną ekstrykcją wariantów ze stron dostawców
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import re
import json
import os
import requests
from pathlib import Path
from urllib.parse import urljoin
import time

from supplier_scrapers import SupplierScraperFactory
from variant_detector_simple import ProductVariant

class KislistGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kislist.com Scraper v4.0 - Enhanced Edition")
        self.root.geometry("650x900")
        self.root.resizable(True, True)
        self.root.minsize(600, 800)

        self.output_dir = None
        self.scraping_thread = None
        self.is_scraping = False

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_label = ttk.Label(main_frame, text="Kislist.com Scraper v4.0",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        subtitle_label = ttk.Label(main_frame, text="Enhanced Edition - Z pełnym scrapingiem dostawców",
                                  font=("Arial", 10), foreground="blue")
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(main_frame, text="Link do listy kislist.com:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar(value="https://kislist.com/list-preview/")
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(main_frame, text="Gdzie zapisać produkty:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))

        self.dir_frame = ttk.Frame(main_frame)
        self.dir_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, width=50, state="readonly")
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.browse_btn = ttk.Button(self.dir_frame, text="Wybierz folder", command=self.browse_directory)
        self.browse_btn.grid(row=0, column=1, padx=(10, 0))

        self.desktop_btn = ttk.Button(self.dir_frame, text="Pulpit", command=self.set_desktop_directory)
        self.desktop_btn.grid(row=0, column=2, padx=(5, 0))

        options_frame = ttk.LabelFrame(main_frame, text="Opcje scrapingu", padding="10")
        options_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.deep_scraping = tk.BooleanVar(value=True)
        deep_check = ttk.Checkbutton(options_frame, text="Głęboki scraping (wchodzi na strony dostawców)",
                                   variable=self.deep_scraping)
        deep_check.grid(row=0, column=0, sticky=tk.W)

        self.max_variants = tk.IntVar(value=10)
        ttk.Label(options_frame, text="Max wariantów na produkt:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        max_spin = ttk.Spinbox(options_frame, from_=1, to=50, textvariable=self.max_variants, width=5)
        max_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        self.use_ai_scraper = tk.BooleanVar(value=False)
        ai_check = ttk.Checkbutton(options_frame, text="Użyj AI do inteligentnego scrapowania (wymagane Ollama lub OpenAI)",
                                 variable=self.use_ai_scraper, command=self.toggle_ai_scraper)
        ai_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        self.custom_output = tk.BooleanVar(value=False)
        custom_check = ttk.Checkbutton(options_frame, text="Własna nazwa folderu wyjściowego",
                                     variable=self.custom_output, command=self.toggle_custom_output)
        custom_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        self.custom_output_frame = ttk.Frame(options_frame)
        self.custom_output_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        ttk.Label(self.custom_output_frame, text="Nazwa folderu:").grid(row=0, column=0, sticky=tk.W)
        self.custom_folder_var = tk.StringVar(value="Produkty_z_Kislist")
        self.custom_folder_entry = ttk.Entry(self.custom_output_frame, textvariable=self.custom_folder_var, width=20, state="disabled")
        self.custom_folder_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))

        info_frame = ttk.LabelFrame(main_frame, text="Informacje v4.0", padding="10")
        info_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        info_text = """NOWOŚCI W WERSJI 4.0 AI ENHANCED:

- AI-powered scraping - inteligentne wykrywanie wariantów
- Analiza nazw obrazów - wykrywa warianty kolorów z nazw plików
- Rzeczywiste zdjęcia produktów w różnych kolorach (nie tylko tekstury)
- Automatyczne sortowanie obrazów według kolorów
- Konfigurowalna nazwa folderu wyjściowego
- Okno można powiększać/zmniejszać
- Brak limitu wariantów (1-50)
- Obsługa Ollama i OpenAI API

Struktura wyników:
[FOLDER]/typ_produktu/NR_nazwa_WYMIARY/Bialy|Jablon|Dab/image_01.jpg..."""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground="blue").pack(anchor=tk.W)

        self.progress_var = tk.StringVar(value="Gotowy do pobierania")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=8, column=0, sticky=tk.W, pady=(0, 5))

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=(0, 10))

        self.start_btn = ttk.Button(button_frame, text="POBIERZ PRODUKTY v4.0", command=self.start_scraping)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="ZATRZYMAJ", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(main_frame, text="Logi", padding="5")
        log_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        self.log_text = tk.Text(log_frame, height=8, width=75)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        self.dir_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        self.custom_output_frame.columnconfigure(1, weight=1)

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.set_desktop_directory()
        self.log("[INFO] KislistScraper v4.0 Enhanced Edition gotowy do użycia!")

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Wybierz folder do zapisania produktów")
        if directory:
            self.dir_var.set(directory)
            self.output_dir = Path(directory)

    def set_desktop_directory(self):
        possible_desktop_paths = [
            Path.home() / "Desktop",
            Path.home() / "Pulpit",
            Path.home() / "Bureau",
            Path.home() / "Escritorio",
        ]

        desktop_path = None
        for path in possible_desktop_paths:
            if path.exists():
                desktop_path = path
                break

        if not desktop_path:
            desktop_path = Path.home()

        self.dir_var.set(str(desktop_path))
        self.output_dir = desktop_path

    def toggle_ai_scraper(self):
        if self.use_ai_scraper.get():
            self.log("[INFO] Włączono AI scraper - będzie używany do inteligentnego wykrywania wariantów")
            self.log("   [OSTRZEŻENIE] Upewnij się, że masz zainstalowane Ollama lub klucz OpenAI w zmiennych środowiskowych")
        else:
            self.log("[INFO] Wyłączono AI scraper - używany będzie tradycyjny scraper")

    def toggle_custom_output(self):
        if self.custom_output.get():
            self.custom_folder_entry.config(state="normal")
            self.log("[INFO] Włączono własną nazwę folderu wyjściowego")
        else:
            self.custom_folder_entry.config(state="disabled")
            self.log("[INFO] Wyłączono własną nazwę folderu - używam 'Produkty_Kislist'")

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_scraping(self):
        url = self.url_var.get().strip()

        if not url or "kislist.com" not in url:
            messagebox.showerror("Błąd", "Podaj prawidłowy link do kislist.com!")
            return

        if not self.output_dir:
            messagebox.showerror("Błąd", "Wybierz folder do zapisania produktów!")
            return

        self.is_scraping = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start(10)
        self.progress_var.set("Pobieranie w toku...")

        self.scraping_thread = threading.Thread(target=self.scrape_products, args=(url,))
        self.scraping_thread.start()

    def stop_scraping(self):
        self.is_scraping = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.progress_var.set("Zatrzymano")
        self.log("[INFO] Zatrzymano przez użytkownika")

    def scrape_products(self, url):
        output_folder_name = self.custom_folder_var.get() if self.custom_output.get() else "Produkty_Kislist"

        scraper = KislistScraperV4(
            self.output_dir,
            self.log,
            lambda: self.is_scraping,
            deep_scraping=self.deep_scraping.get(),
            max_variants=self.max_variants.get(),
            custom_folder_name=output_folder_name,
            use_ai_scraper=self.use_ai_scraper.get()
        )

        try:
            scraper.scrape(url)
            if self.is_scraping:
                self.root.after(0, self.scraping_finished, True)
        except Exception as e:
            self.root.after(0, self.scraping_finished, False, str(e))

    def scraping_finished(self, success, error_message=None):
        self.is_scraping = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()

        if success:
            self.progress_var.set("Pobieranie zakończone!")
            self.log("[OK] Wszystkie produkty zostały pobrane z pełnymi wariantami!")
            messagebox.showinfo("Sukces!", f"Produkty zostały zapisane w:\n{self.output_dir}")
        else:
            self.progress_var.set("Błąd podczas pobierania")
            self.log(f"[BŁĄD] {error_message}")
            messagebox.showerror("Błąd", f"Wystąpił błąd:\n{error_message}")

    def run(self):
        self.root.mainloop()

class KislistScraperV4:
    def __init__(self, output_dir, log_callback, is_running_callback, deep_scraping=True, max_variants=5, custom_folder_name="Produkty_Kislist", use_ai_scraper=False):
        self.output_dir = Path(output_dir) / custom_folder_name
        self.log = log_callback
        self.is_running = is_running_callback
        self.deep_scraping = deep_scraping
        self.max_variants = max_variants
        self.custom_folder_name = custom_folder_name
        self.use_ai_scraper = use_ai_scraper

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def sanitize_filename(self, filename):
        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ż': 'z', 'ź': 'z',
            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
            'Ó': 'O', 'Ś': 'S', 'Ż': 'Z', 'Ź': 'Z'
        }

        for polish, latin in replacements.items():
            filename = filename.replace(polish, latin)

        filename = re.sub(r'[<>:\"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)

        return filename.strip('_')

    def download_image(self, url, filepath):
        try:
            if not url:
                self.log(f"[OSTRZEŻENIE] Pusty URL obrazu dla {filepath.name}")
                return False

            if filepath.exists():
                self.log(f"[INFO] Pomijam (już istnieje): {filepath.name}")
                return True

            self.log(f"[INFO] Pobieranie: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            if len(response.content) < 1000:
                self.log(f"[OSTRZEŻENIE] Obraz zbyt mały ({len(response.content)} bajtów): {url}")
                return False

            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.log(f"[OK] Pobrano ({len(response.content)//1000}KB): {filepath.name}")
            return True

        except requests.exceptions.Timeout:
            self.log(f"[OSTRZEŻENIE] Timeout pobierania: {url}")
        except requests.exceptions.HTTPError as e:
            self.log(f"[BŁĄD] HTTP {e.response.status_code}: {url}")
        except Exception as e:
            self.log(f"[BŁĄD] Błąd pobierania {url}: {str(e)[:80]}")
        return False

    def extract_data_from_page(self, url):
        try:
            self.log(f"[INFO] Pobieranie danych z: {url}")
            response = self.session.get(url)
            response.raise_for_status()

            content = response.text
            pattern = r'window\.sections\s*=\s*(\[.*?\]);'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                json_str = match.group(1)
                sections_data = json.loads(json_str)
                return sections_data
            else:
                self.log("[BŁĄD] Nie znaleziono danych window.sections na stronie")
                return []

        except Exception as e:
            self.log(f"[BŁĄD] Błąd podczas pobierania strony: {e}")
            return []

    def scrape(self, url):
        if not self.is_running():
            return

        mode = "GŁĘBOKI" if self.deep_scraping else "PODSTAWOWY"
        self.log(f"[INFO] Rozpoczynam scraping v4.0 ({mode})...")

        sections_data = self.extract_data_from_page(url)

        if not sections_data:
            raise Exception("Nie udało się pobrać danych ze strony!")

        self.log(f"[INFO] Znaleziono {len(sections_data)} sekcji produktów")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        total_products = 0
        downloaded_images = 0
        deep_scraped_products = 0

        for section in sections_data:
            if not self.is_running():
                break

            raw_section_name = section.get('name', 'bez_nazwy')
            section_name = self.sanitize_filename(raw_section_name)
            self.log(f"\n[INFO] Przetwarzam: {raw_section_name}")

            items = section.get('items', [])
            self.log(f"   Produktów: {len(items)}")

            for idx, item in enumerate(items, 1):
                if not self.is_running():
                    break

                product_name_base = item.get('collection') or f"produkt_{idx:03d}"
                product_name = self.sanitize_filename(str(product_name_base))

                size = item.get('size', '').strip()
                if size:
                    size_clean = self.sanitize_filename(size)
                    product_name_with_size = f"{product_name}_{size_clean}"
                else:
                    product_name_with_size = product_name

                numbered_product_name = f"{idx:03d}_{product_name_with_size}"

                total_products += 1

                if self.deep_scraping and item.get('url'):
                    supplier_url = item.get('url')
                    self.log(f"   [INFO] Głęboki scraping: {numbered_product_name}")

                    try:
                        variants = SupplierScraperFactory.scrape_product_url(supplier_url, self.session, use_ai_scraper=self.use_ai_scraper)

                        if variants:
                            deep_scraped_products += 1

                            self.log(f"     [OK] Znaleziono {len(variants)} wariantów")

                            for variant_idx, variant in enumerate(variants, 1):
                                if not self.is_running():
                                    break

                                variant_dir = self.output_dir / section_name / numbered_product_name / variant.color
                                variant_dir.mkdir(parents=True, exist_ok=True)

                                for img_idx, img_url in enumerate(variant.images[:3], 1):
                                    if not self.is_running():
                                        break

                                    img_filename = f"image_{img_idx:02d}.jpg"
                                    img_path = variant_dir / img_filename

                                    if self.download_image(img_url, img_path):
                                        downloaded_images += 1

                                self.log(f"     [INFO] {variant.color}: {len(variant.images)} obrazów")
                        else:
                            self._download_basic_product_images(item, section_name, numbered_product_name)
                            downloaded_images += 1
                            self.log(f"     [INFO] Fallback: podstawowy obraz")

                    except Exception as e:
                        self.log(f"     [BŁĄD] Błąd głębokiego scrapingu: {str(e)[:30]}...")
                        self._download_basic_product_images(item, section_name, numbered_product_name)
                        downloaded_images += 1
                        self.log(f"     [INFO] Fallback: podstawowy obraz")
                else:
                    self._download_basic_product_images(item, section_name, numbered_product_name)
                    downloaded_images += 1
                    self.log(f"   [OK] {numbered_product_name}")

        if self.is_running():
            self.log(f"\n[OK] GOTOWE!")
            self.log(f"[INFO] Produktów: {total_products}")
            if self.deep_scraping:
                self.log(f"[INFO] Głęboko przeskanowanych: {deep_scraped_products}")
            self.log(f"[INFO] Pobranych zdjęć: {downloaded_images}")
            self.log(f"[INFO] Zapisano w: {self.output_dir}")

    def _download_basic_product_images(self, item, section_name, numbered_product_name):
        notes = item.get('notes', '').lower()
        collection = item.get('collection', '').lower()

        colors = {
            'Bialy': ['biały', 'białe', 'white', 'bianco', 'biała'],
            'Czarny': ['czarny', 'czarne', 'black', 'nero', 'graphite', 'grafit', 'czarna'],
            'Szary': ['szary', 'szare', 'grey', 'gray', 'grys', 'szara'],
            'Brazowy': ['brązowy', 'brązowe', 'brown', 'braun', 'brązowa'],
            'Bezowy': ['beżowy', 'beżowe', 'beige', 'beż', 'beżowa'],
            'Niebieski': ['niebieski', 'niebieskie', 'blue', 'blu', 'niebieska']
        }

        text_to_check = f"{notes} {collection}".lower()
        detected_color = None

        for color_key, color_variants in colors.items():
            for variant in color_variants:
                if variant in text_to_check:
                    detected_color = color_key
                    break
            if detected_color:
                break

        def _detect_type(name, url):
            text = f"{name} {url}".lower()
            mapping = {
                'drzwi': ['door', 'drzwi', 'porta', 'verte'],
                'plytki': ['płytka', 'plytka', 'ceramic', 'tile', 'paradyż', 'paradyz', 'tubądzin', 'tubadzin', 'opoczno'],
            }
            for t, kws in mapping.items():
                for kw in kws:
                    if kw in text:
                        return t
            return 'produkty'

        type_folder = _detect_type(section_name, item.get('url', ''))
        color_dir = detected_color if detected_color else "Domyslny"
        product_dir = self.output_dir / type_folder / numbered_product_name / color_dir

        product_dir.mkdir(parents=True, exist_ok=True)

        photo_info = item.get('photo', {})
        thumb_urls = photo_info.get('thumb_urls', {})

        for file_ref, urls in thumb_urls.items():
            tiny_thumb = urls.get('tiny_thumb')
            if tiny_thumb:
                img_filepath = product_dir / "image.jpg"
                self.download_image(tiny_thumb, img_filepath)
                break

def main():
    app = KislistGUI()
    app.run()

if __name__ == "__main__":
    main()
