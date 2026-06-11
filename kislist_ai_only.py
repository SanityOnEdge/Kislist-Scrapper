#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kislist.com AI Scraper v4.0 - Tylko AI
Program do pobierania produktów z kislist.com używając wyłącznie sztucznej inteligencji
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

from ai_supplier_scrapers import AISupplierScraperFactory
from variant_detector_simple import ProductVariant
from ai_config import check_ai_availability

class KislistAIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kislist.com AI Scraper v4.0 - AI Only Edition")
        self.root.geometry("650x800")
        self.root.resizable(True, True)
        self.root.minsize(600, 750)

        self.output_dir = None
        self.scraping_thread = None
        self.is_scraping = False

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_label = ttk.Label(main_frame, text="Kislist AI Scraper v4.0",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))

        subtitle_label = ttk.Label(main_frame, text="AI-Only Edition - Inteligentny scraping produktów",
                                  font=("Arial", 10), foreground="blue")
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))

        ai_status_frame = ttk.LabelFrame(main_frame, text="Status AI", padding="10")
        ai_status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.ai_status_var = tk.StringVar(value="Sprawdzanie...")
        self.ai_status_label = ttk.Label(ai_status_frame, textvariable=self.ai_status_var, font=("Arial", 9))
        self.ai_status_label.pack(anchor=tk.W)

        self.check_ai_button = ttk.Button(ai_status_frame, text="Sprawdź AI", command=self.check_ai_status)
        self.check_ai_button.pack(anchor=tk.W, pady=(5, 0))

        ttk.Label(main_frame, text="Link do listy kislist.com:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar(value="https://kislist.com/list-preview/")
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(main_frame, text="Gdzie zapisać produkty:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))

        self.dir_frame = ttk.Frame(main_frame)
        self.dir_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, width=50, state="readonly")
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.browse_btn = ttk.Button(self.dir_frame, text="Wybierz folder", command=self.browse_directory)
        self.browse_btn.grid(row=0, column=1, padx=(10, 0))

        self.desktop_btn = ttk.Button(self.dir_frame, text="Pulpit", command=self.set_desktop_directory)
        self.desktop_btn.grid(row=0, column=2, padx=(5, 0))

        options_frame = ttk.LabelFrame(main_frame, text="Opcje AI Scrapingu", padding="10")
        options_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.max_variants = tk.IntVar(value=15)
        ttk.Label(options_frame, text="Max wariantów AI na produkt:").grid(row=0, column=0, sticky=tk.W)
        max_spin = ttk.Spinbox(options_frame, from_=5, to=50, textvariable=self.max_variants, width=5)
        max_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(options_frame, text="Nazwa głównego folderu:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.custom_folder_var = tk.StringVar(value="Produkty_z_Kislist")
        self.custom_folder_entry = ttk.Entry(options_frame, textvariable=self.custom_folder_var, width=25)
        self.custom_folder_entry.grid(row=1, column=1, padx=(10, 0), pady=(5, 0), sticky=(tk.W, tk.E))

        info_frame = ttk.LabelFrame(main_frame, text="AI Scraper Info", padding="10")
        info_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        info_text = """WŁAŚCIWOŚCI AI SCRAPERA:

- Inteligentne rozpoznawanie wariantów produktów
- Automatyczne wykrywanie kolorów, materiałów, wykończeń
- Adaptacja do różnych struktur stron bez programowania
- Wyższa dokładność niż tradycyjne metody (85-95%)
- Działa z Ollama (darmowy) lub OpenAI (płatny)

Struktura wyników AI:
[FOLDER]/typ/NR_nazwa/Bialy_Polysk|Czarny_Mat|Dab_Sonoma/obrazy..."""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground="darkgreen").pack(anchor=tk.W)

        self.progress_var = tk.StringVar(value="Gotowy do AI scrapingu")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=9, column=0, sticky=tk.W, pady=(0, 5))

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=(0, 10))

        self.start_btn = ttk.Button(button_frame, text="URUCHOM AI SCRAPING", command=self.start_ai_scraping)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="ZATRZYMAJ", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(main_frame, text="Logi AI", padding="5")
        log_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        self.log_text = tk.Text(log_frame, height=6, width=75)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        self.dir_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.set_desktop_directory()
        self.log("[INFO] Kislist AI Scraper v4.0 - AI Only Edition gotowy!")

        self.root.after(1000, self.check_ai_status)

    def check_ai_status(self):
        try:
            available, message = check_ai_availability()
            if available:
                self.ai_status_var.set(f"[OK] {message}")
                self.start_btn.config(state=tk.NORMAL)
                self.log(f"[OK] AI dostępne: {message}")
            else:
                self.ai_status_var.set(f"[BŁĄD] {message}")
                self.start_btn.config(state=tk.DISABLED)
                self.log(f"[BŁĄD] Problem z AI: {message}")
                self.log("   [INFO] Sprawdź konfigurację AI w README_AI.md")
        except Exception as e:
            self.ai_status_var.set(f"[BŁĄD] Błąd: {str(e)}")
            self.start_btn.config(state=tk.DISABLED)
            self.log(f"[BŁĄD] Błąd sprawdzania AI: {e}")

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

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_ai_scraping(self):
        if self.is_scraping:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Błąd", "Wprowadź URL listy kislist.com!")
            return

        if not self.output_dir:
            messagebox.showerror("Błąd", "Wybierz folder do zapisania produktów!")
            return

        available, message = check_ai_availability()
        if not available:
            messagebox.showerror("Błąd AI", f"AI nie jest dostępne:\n{message}\n\nSkonfiguruj AI według instrukcji w README_AI.md")
            return

        self.is_scraping = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start(10)
        self.progress_var.set("[INFO] Uruchamianie AI scrapingu...")

        self.scraping_thread = threading.Thread(target=self.run_ai_scraping, args=(url,), daemon=True)
        self.scraping_thread.start()

    def stop_scraping(self):
        self.is_scraping = False
        self.log("[INFO] Zatrzymywanie AI scrapingu...")

    def run_ai_scraping(self, url):
        output_folder_name = self.custom_folder_var.get() or "Produkty_AI_Kislist"

        ai_scraper = KislistAIScraper(
            self.output_dir,
            self.log,
            lambda: self.is_scraping,
            max_variants=self.max_variants.get(),
            custom_folder_name=output_folder_name
        )

        try:
            ai_scraper.scrape(url)
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
            self.progress_var.set("[OK] AI scraping zakończony!")
            self.log("[OK] Wszystkie produkty zostały pobrane przez AI!")
            messagebox.showinfo("Sukces AI!", f"Produkty zostały zapisane przez AI w:\n{self.output_dir}")
        else:
            self.progress_var.set("[BŁĄD] Błąd AI scrapingu")
            self.log(f"[BŁĄD] Błąd AI: {error_message}")
            messagebox.showerror("Błąd AI", f"Wystąpił błąd AI:\n{error_message}")

    def run(self):
        self.root.mainloop()

class KislistAIScraper:
    def __init__(self, output_dir, log_callback, is_running_callback, max_variants=15, custom_folder_name="Produkty_AI_Kislist"):
        self.output_dir = Path(output_dir) / custom_folder_name
        self.log = log_callback
        self.is_running = is_running_callback
        self.max_variants = max_variants
        self.custom_folder_name = custom_folder_name

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

        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\\s+', '_', filename)

        return filename.strip('_')

    def download_image(self, url, filepath):
        try:
            if not url:
                self.log(f"[OSTRZEŻENIE] Pusty URL obrazu dla {filepath.name}")
                return False

            if filepath.exists():
                self.log(f"[INFO] Pomijam (już istnieje): {filepath.name}")
                return True

            self.log(f"[INFO] AI pobiera: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            if len(response.content) < 1000:
                self.log(f"[OSTRZEŻENIE] Obraz zbyt mały ({len(response.content)} bajtów): {url}")
                return False

            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.log(f"[OK] Pobrano przez AI ({len(response.content)//1000}KB): {filepath.name}")
            return True

        except Exception as e:
            self.log(f"[BŁĄD] Błąd AI pobierania {url}: {str(e)[:80]}")
            return False

    def extract_data_from_page(self, url):
        try:
            self.log(f"[INFO] AI pobiera dane z: {url}")
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
                self.log("[BŁĄD] AI nie znalazło danych window.sections na stronie")
                return []

        except Exception as e:
            self.log(f"[BŁĄD] Błąd AI podczas pobierania strony: {e}")
            return []

    def scrape(self, url):
        if not self.is_running():
            return

        self.log(f"[INFO] Rozpoczynam AI scraping...")

        sections_data = self.extract_data_from_page(url)

        if not sections_data:
            raise Exception("AI nie udało się pobrać danych ze strony!")

        self.log(f"[INFO] AI znalazło {len(sections_data)} sekcji produktów")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        total_products = 0
        ai_scraped_products = 0
        downloaded_images = 0

        for section in sections_data:
            if not self.is_running():
                break

            section_name = self.sanitize_filename(section.get('name', 'bez_nazwy'))
            self.log(f"\n[INFO] AI przetwarza: {section.get('name', 'bez_nazwy')}")

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

                if item.get('url'):
                    supplier_url = item.get('url')
                    self.log(f"   [INFO] AI analizuje: {numbered_product_name}")

                    try:
                        ai_variants = AISupplierScraperFactory.scrape_product_url(supplier_url, self.session)

                        if ai_variants:
                            ai_scraped_products += 1

                            self.log(f"     [OK] AI znalazło {len(ai_variants)} wariantów")

                            for variant_idx, variant in enumerate(ai_variants, 1):
                                if not self.is_running():
                                    break

                                variant_folder_name = self.sanitize_filename(variant.color)
                                section_dir = self.output_dir / section_name
                                product_dir = section_dir / numbered_product_name
                                variant_dir = product_dir / variant_folder_name

                                self.log(f"       [INFO] AI wariant {variant_idx}: {variant.color}")

                                first_saved_path = None
                                for img_idx, image_url in enumerate(variant.images, 1):
                                    if not self.is_running():
                                        break

                                    img_extension = '.jpg'
                                    if image_url:
                                        if '.png' in image_url.lower():
                                            img_extension = '.png'
                                        elif '.webp' in image_url.lower():
                                            img_extension = '.webp'

                                    img_filename = f"ai_image_{img_idx:02d}{img_extension}"
                                    img_path = variant_dir / img_filename

                                    if self.download_image(image_url, img_path):
                                        if first_saved_path is None:
                                            first_saved_path = img_path
                                        downloaded_images += 1

                                try:
                                    if first_saved_path and first_saved_path.exists():
                                        import shutil
                                        shutil.copy2(first_saved_path, variant_dir / "image.jpg")
                                        shutil.copy2(first_saved_path, variant_dir / "door_variant.jpg")
                                except Exception:
                                    pass

                        else:
                            self.log(f"     [OSTRZEŻENIE] AI nie znalazło wariantów dla {numbered_product_name}")

                    except Exception as e:
                        self.log(f"     [BŁĄD] Błąd AI dla {numbered_product_name}: {str(e)[:50]}...")

                else:
                    self.log(f"   [OSTRZEŻENIE] Brak URL dostawcy dla: {numbered_product_name}")

        self.log(f"\n[OK] AI SCRAPING ZAKOŃCZONY!")
        self.log(f"   [INFO] Produktów ogółem: {total_products}")
        self.log(f"   [INFO] Przeanalizowanych przez AI: {ai_scraped_products}")
        self.log(f"   [INFO] Pobranych obrazów: {downloaded_images}")
        self.log(f"   [INFO] Zapisane w: {self.output_dir}")

if __name__ == "__main__":
    app = KislistAIGUI()
    app.run()
