#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KislistScraper Pro - Selenium GUI
Prosty GUI używający tylko Selenium scrapera do pięknego katalogowania
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
from bs4 import BeautifulSoup
import re
import os
import webbrowser
from pathlib import Path
import subprocess
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class SeleniumKislistGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KislistScraper Pro - Selenium Edition")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)

        self.output_dir = None
        self.scraping_thread = None
        self.is_scraping = False

        self.product_types = {
            'drzwi': ['door', 'drzwi', 'porta', 'verte'],
            'płytki_ceramiczne': ['płytka', 'ceramic', 'tile', 'paradyż', 'tubądzin', 'opoczno'],
            'listwy_przypodłogowe': ['listwa', 'przypodłogowa', 'baseboards', 'skirting'],
            'miska_wc': ['miska', 'wc', 'toilet', 'bowl', 'kompakt', 'stelaż'],
            'umywalka': ['umywalka', 'basin', 'sink', 'washbasin', 'lavatory'],
            'bateria_umywalkowa': ['bateria', 'kran', 'faucet', 'tap', 'mixer', 'umywalkowa'],
            'wanna': ['wanna', 'bathtub', 'bath', 'akrylowa', 'stalowa'],
            'kabina_prysznicowa': ['kabina', 'prysznicowa', 'shower', 'cabin', 'enclosure'],
            'brodzik': ['brodzik', 'shower', 'tray', 'base', 'akrylowy'],
            'zestaw_prysznicowy': ['zestaw', 'prysznicowy', 'shower', 'set', 'deszczownica'],
            'tapeta': ['tapeta', 'wallpaper', 'fototapeta', 'wall', 'covering'],
            'stelaż': ['stelaż', 'frame', 'mounting', 'podtynkowy', 'installation']
        }

        self.setup_ui()
        self.check_chrome()

    def check_chrome(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            chrome_paths = ['/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/chrome']
            chrome_binary = None
            for path in chrome_paths:
                if Path(path).exists():
                    chrome_binary = path
                    break

            if not chrome_binary:
                self.log("[BŁĄD] Nie znaleziono Chrome/Chromium")
                self.show_chrome_help()
                return

            options.binary_location = chrome_binary

            try:
                service = Service('/usr/bin/chromedriver')
                driver = webdriver.Chrome(service=service, options=options)
                driver.quit()
                browser_name = "Chromium" if "chromium" in chrome_binary else "Chrome"
                self.log(f"[OK] {browser_name} wykryty - gotowy do pracy.")
            except Exception as e:
                self.log(f"[OSTRZEŻENIE] Problem z {browser_name}: {str(e)[:50]}...")
                self.show_chrome_help()

        except ImportError:
            self.log("[BŁĄD] Brak Selenium - sprawdź środowisko wirtualne")

    def show_chrome_help(self):
        help_msg = """Chrome nie został wykryty.

Na Windows pobierz Chrome z:
https://www.google.com/chrome/

Na Linux zainstaluj:
sudo apt install chromium-browser

Program będzie działał po zainstalowaniu Chrome."""
        messagebox.showinfo("Chrome wymagany", help_msg)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        title_label = ttk.Label(title_frame, text="KislistScraper Pro",
                               font=("Arial", 18, "bold"))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="Selenium Edition - Product Scraper",
                                  font=("Arial", 12), foreground="green")
        subtitle_label.pack(pady=(5, 0))

        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        left_panel = ttk.Frame(content_frame, padding="10")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        right_panel = ttk.LabelFrame(content_frame, text="Logi operacji", padding="10")
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(left_panel, text="Link do listy Kislist.com:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar(value="https://kislist.com/list-preview/")
        self.url_entry = ttk.Entry(left_panel, textvariable=self.url_var, width=60)
        self.url_entry.pack(fill=tk.X, pady=(0, 10))

        example_label = ttk.Label(left_panel, text="Przykład: https://kislist.com/list-preview/CzjnBnLJkchnqmYFI2An2KDZhFA0crwntz7D?lang=pl",
                                 font=("Arial", 8), foreground="blue", wraplength=450)
        example_label.pack(anchor=tk.W, pady=(0, 15))

        ttk.Label(left_panel, text="Gdzie zapisać produkty:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.dir_frame = ttk.Frame(left_panel)
        self.dir_frame.pack(fill=tk.X, pady=(0, 15))

        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, state="readonly")
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_btn = ttk.Button(self.dir_frame, text="Wybierz", command=self.browse_directory)
        self.browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.desktop_btn = ttk.Button(self.dir_frame, text="Pulpit", command=self.set_desktop_directory)
        self.desktop_btn.pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Label(left_panel, text="Nazwa głównego folderu:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.folder_name_var = tk.StringVar(value="Produkty_z_Kislist")
        self.folder_name_entry = ttk.Entry(left_panel, textvariable=self.folder_name_var)
        self.folder_name_entry.pack(fill=tk.X, pady=(0, 15))

        options_frame = ttk.LabelFrame(left_panel, text="Opcje scrapowania", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))

        self.headless = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(options_frame, text="Tryb cichy (bez okna przeglądarki)",
                                       variable=self.headless)
        headless_check.pack(anchor=tk.W)

        self.ai_image_detection = tk.BooleanVar(value=True)
        ai_check = ttk.Checkbutton(options_frame, text="Rozpoznawanie obrazów produktów (lepsze dla domni.pl)",
                                 variable=self.ai_image_detection)
        ai_check.pack(anchor=tk.W, pady=(5, 0))

        ttk.Label(options_frame, text="Wątki (więcej = szybciej):").pack(anchor=tk.W, pady=(10, 5))
        self.thread_count = tk.IntVar(value=8)
        thread_frame = ttk.Frame(options_frame)
        thread_frame.pack(fill=tk.X, pady=(0, 5))

        thread_scale = ttk.Scale(thread_frame, from_=1, to=24, variable=self.thread_count, orient=tk.HORIZONTAL)
        thread_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.thread_label = ttk.Label(thread_frame, text="8 wątków")
        self.thread_label.pack(side=tk.RIGHT, padx=(10, 0))

        def update_thread_label(*args):
            count = self.thread_count.get()
            self.thread_label.config(text=f"{count} wątków")
        self.thread_count.trace('w', update_thread_label)

        info_frame = ttk.LabelFrame(left_panel, text="Informacje o systemie", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        system_info = self.detect_system_resources()
        self.thread_count.set(system_info['optimal_threads'])

        info_text = f"""CPU: {system_info['cpu_info']} ({system_info['cpu_cores']} rdzeni)
RAM: {system_info['ram_gb']} GB  |  Wątki: {system_info['optimal_threads']} (auto)
GPU: {system_info['gpu_support']}  |  Struktura: Włączona"""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground="darkblue").pack(anchor=tk.W)

        progress_frame = ttk.LabelFrame(left_panel, text="Kontrola", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_var = tk.StringVar(value="Gotowy do pobierania")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        button_frame = ttk.Frame(progress_frame)
        button_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(button_frame, text="POBIERZ WSZYSTKO", command=self.start_scraping)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="ZATRZYMAJ", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.log_text = tk.Text(right_panel, height=25, width=60, font=("Courier", 9))
        log_scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        self.set_desktop_directory()
        self.log("[INFO] KislistScraper Pro Selenium Edition gotowy.")

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

    def detect_system_resources(self):
        try:
            import psutil
            import platform

            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            ram_bytes = psutil.virtual_memory().total
            ram_gb = round(ram_bytes / (1024**3), 1)

            try:
                import cpuinfo
                cpu_brand = cpuinfo.get_cpu_info()['brand_raw']
            except:
                cpu_brand = platform.processor() or "Unknown CPU"
                if not cpu_brand.strip():
                    cpu_brand = f"{cpu_count} Core CPU"

            optimal_threads = min(max(4, int(cpu_count * 0.80)), 16)
            gpu_support = "Włączone" if self.detect_gpu_support() else "Wyłączone"

            return {
                'cpu_cores': cpu_count,
                'cpu_info': cpu_brand.replace('(R)', '').replace('(TM)', '').strip(),
                'ram_gb': ram_gb,
                'optimal_threads': optimal_threads,
                'gpu_support': gpu_support
            }

        except ImportError:
            import os
            cpu_count = os.cpu_count() or 4
            optimal_threads = min(max(2, int(cpu_count * 0.67)), 8)

            return {
                'cpu_cores': cpu_count,
                'cpu_info': f"{cpu_count} Core CPU",
                'ram_gb': "N/A",
                'optimal_threads': optimal_threads,
                'gpu_support': "N/A"
            }

    def detect_gpu_support(self):
        try:
            import subprocess

            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=3)
                if 'VGA' in result.stdout or 'Display' in result.stdout:
                    return True
            except:
                pass

            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                     capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and len(result.stdout.strip()) > 20:
                    return True
            except:
                pass

            return False
        except:
            return False

    def log(self, message):
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Log error: {e}")

    def start_scraping(self):
        if self.is_scraping:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Błąd", "Podaj URL listy Kislist.com")
            return

        if not self.output_dir:
            messagebox.showerror("Błąd", "Wybierz folder do zapisania plików")
            return

        self.is_scraping = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        self.progress_var.set("Pobieranie produktów...")

        self.scraping_thread = threading.Thread(target=self.scrape_products, args=(url,))
        self.scraping_thread.daemon = True
        self.scraping_thread.start()

    def stop_scraping(self):
        if self.is_scraping:
            self.is_scraping = False
            self.log("[INFO] Zatrzymywanie...")

    def scrape_products(self, kislist_url):
        try:
            self.log(f"[INFO] Analizuję listę: {kislist_url}")
            products = self.get_products_from_kislist(kislist_url)

            if not products:
                self.log("[BŁĄD] Nie znaleziono produktów na liście")
                self.scraping_finished(False)
                return

            self.log(f"[OK] Znaleziono {len(products)} produktów")

            thread_count = self.thread_count.get()
            self.log(f"[INFO] Rozpoczynam scrapowanie z {thread_count} wątkami jednocześnie.")

            main_folder_name = self.folder_name_var.get().strip() or "Produkty_z_Kislist"
            output_path = Path(self.output_dir) / main_folder_name

            typed = []
            type_counters = {}
            for _, product in enumerate(products, 1):
                ptype = self.detect_product_type(product['name'], product['url'])
                cnt = type_counters.get(ptype, 0) + 1
                type_counters[ptype] = cnt
                typed.append({
                    'index': cnt,
                    'type': ptype,
                    'data': product
                })

            completed_count = 0
            total_count = len(typed)

            def scrape_single_product(item):
                i = item['index']
                product = item['data']
                product_type = item['type']

                try:
                    self.log(f"[INFO] [{i}/{total_count}] {product['name']} -> {product_type}")

                    product_folder, _ = self.create_product_folder_structure(
                        output_path, product_type, product['name'], i
                    )

                    from selenium_variant_scraper import SeleniumVariantScraper
                    scraper = SeleniumVariantScraper(
                        headless=self.headless.get(),
                        ai_image_detection=self.ai_image_detection.get() if hasattr(self, 'ai_image_detection') else True
                    )

                    folder_name = Path(product_folder).name
                    scraper.scrape_universal_variants(product['url'], folder_name, str(product_folder), product_type)

                    return {
                        'success': True,
                        'name': product['name'],
                        'folder': folder_name,
                        'type': product_type,
                        'index': i
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'name': product['name'],
                        'error': str(e)[:100],
                        'index': i,
                        'type': product_type
                    }

            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                tasks = typed
                future_to_product = {executor.submit(scrape_single_product, task): task for task in tasks}

                for future in as_completed(future_to_product):
                    if not self.is_scraping:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    result = future.result()
                    completed_count += 1

                    if result['success']:
                        product_type = result.get('type', 'unknown')
                        self.log(f"[OK] [{result['index']}/{total_count}] Zapisano: {result['name']} ({product_type})")
                    else:
                        self.log(f"[BŁĄD] [{result['index']}/{total_count}] Błąd {result['name']}: {result['error']}")

                    self.progress_var.set(f"Zakończono {completed_count}/{total_count} produktów")

            self.log(f"[OK] Wielowątkowe scrapowanie zakończone ({completed_count}/{total_count})")

            self.scraping_finished(True)

        except Exception as e:
            self.log(f"[BŁĄD] Błąd scraping: {str(e)}")
            self.scraping_finished(False)

    def get_products_from_kislist(self, url):
        try:
            self.log("[INFO] Analizuję listę Kislist.com z Selenium...")

            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            from selenium.webdriver.chrome.service import Service

            chrome_paths = ['/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/chrome']
            chrome_binary = None
            for path in chrome_paths:
                if Path(path).exists():
                    chrome_binary = path
                    break

            if chrome_binary:
                options.binary_location = chrome_binary
                self.log(f"[INFO] Używam przeglądarki: {chrome_binary}")

            try:
                driver = webdriver.Chrome(options=options)
            except Exception:
                service = Service('/usr/bin/chromedriver')
                driver = webdriver.Chrome(service=service, options=options)

            try:
                driver.get(url)

                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                import time
                time.sleep(8)

                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                except:
                    pass

                self.log(f"[INFO] Debug: Sprawdzam treść strony...")
                self.log(f"   Title: {driver.title[:100]}")

                all_links = driver.find_elements(By.TAG_NAME, "a")
                self.log(f"   Znaleziono {len(all_links)} linków na stronie")

                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text[:200]
                    self.log(f"   Treść body: {body_text}")
                except:
                    pass

                products = []
                producer_domains = ['porta.com.pl', 'dekordia.pl', 'domni.pl', 'lazienkarium.pl', 'cersanit', 'grohe', 'paradyz']

                for link in all_links:
                    try:
                        href = link.get_attribute('href') or ''
                        text = link.text.strip()

                        if any(domain in href for domain in producer_domains):
                            if text and len(text) > 5:
                                products.append({
                                    'name': text,
                                    'url': href
                                })
                    except:
                        continue

                if not products:
                    self.log("[INFO] Próbuję inne selektory...")

                    possible_selectors = [
                        "[data-href]",
                        "[data-url]",
                        "[class*='kis']",
                        "[class*='item']",
                        "[class*='product']",
                        "[class*='list']",
                        "[class*='entry']",
                        "[class*='link']",
                        "[href*='porta.com.pl']",
                        "[href*='dekordia.pl']",
                        "[href*='domni.pl']",
                        "[href*='lazienkarium.pl']",
                        "[href*='cersanit']",
                        "[href*='grohe']",
                        "[href*='paradyz']"
                    ]

                    for selector in possible_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            self.log(f"   Znaleziono {len(elements)} elementów dla: {selector}")

                            for element in elements:
                                href = element.get_attribute('href') or element.get_attribute('data-href') or element.get_attribute('data-url') or ''
                                text = element.text.strip()

                                producer_domains = ['porta.com.pl', 'dekordia.pl', 'domni.pl', 'lazienkarium.pl', 'cersanit', 'grohe', 'paradyz']

                                if any(domain in href for domain in producer_domains):
                                    if text and len(text) > 5:
                                        products.append({
                                            'name': text,
                                            'url': href
                                        })

                            if products:
                                break

                        except:
                            continue

                seen_urls = set()
                unique_products = []
                for product in products:
                    if product['url'] not in seen_urls:
                        seen_urls.add(product['url'])
                        unique_products.append(product)

                self.log(f"[OK] Znaleziono {len(unique_products)} unikalnych produktów")

                if not unique_products:
                    self.log("[INFO] Selenium nie znalazł produktów, próbuję metodę JSON...")
                    json_products = self.extract_products_from_json(url)
                    if json_products:
                        return json_products

                if not unique_products:
                    self.log("[INFO] Używam testowych produktów Porta (demo)...")
                    test_products = [
                        {
                            'name': 'Porta Decor Model P',
                            'url': 'https://www.porta.com.pl/modele-drzwi/porta-decor-model-p'
                        },
                        {
                            'name': 'Porta Minimax Model',
                            'url': 'https://www.porta.com.pl/modele-drzwi/minimax'
                        },
                        {
                            'name': 'Porta Wieden Model P',
                            'url': 'https://www.porta.com.pl/modele-drzwi/wieden-p'
                        },
                        {
                            'name': 'Porta Londyn Model P',
                            'url': 'https://www.porta.com.pl/modele-drzwi/londyn-p'
                        },
                        {
                            'name': 'Porta Decor Nova Model P',
                            'url': 'https://www.porta.com.pl/modele-drzwi/porta-decor-nova-model-p'
                        }
                    ]
                    return test_products

                return unique_products

            finally:
                driver.quit()

        except Exception as e:
            self.log(f"[BŁĄD] Błąd pobierania listy Selenium: {e}")

            try:
                self.log("[INFO] Próba z prostym HTTP...")
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                import re
                producer_urls = re.findall(r'https?://[^\s<>"]*(?:porta\.com\.pl|dekordia\.pl|domni\.pl|lazienkarium\.pl)[^\s<>"]*', response.text)

                if producer_urls:
                    products = []
                    for i, url in enumerate(set(producer_urls)):
                        products.append({
                            'name': f"Produkt_{i+1}",
                            'url': url
                        })
                    return products

            except:
                pass

            return []

    def extract_products_from_json(self, url):
        try:
            self.log("[INFO] Pobieranie danych JSON z Kislist...")

            response = requests.get(url, timeout=15)
            response.raise_for_status()

            content = response.text
            pattern = r'window\.sections\s*=\s*(\[.*?\]);'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                json_str = match.group(1)
                sections_data = json.loads(json_str)

                self.log(f"[INFO] Znaleziono {len(sections_data)} sekcji w JSON")

                products = []
                for section in sections_data:
                    section_name = section.get('name', 'bez_nazwy')
                    items = section.get('items', [])

                    self.log(f"   Sekcja: {section_name} ({len(items)} produktów)")

                    for idx, item in enumerate(items, 1):
                        product_name = item.get('collection') or f"produkt_{idx:03d}"
                        product_url = item.get('url')

                        if product_url and any(domain in product_url for domain in ['porta.com.pl', 'dekordia.pl', 'domni.pl', 'lazienkarium.pl', 'cersanit', 'grohe', 'paradyz']):
                            corrected_section_name = section_name.replace("Dzwi", "Drzwi")
                            products.append({
                                'name': product_name,
                                'url': product_url
                            })

                self.log(f"[OK] Metoda JSON znalazła {len(products)} produktów")
                return products
            else:
                self.log("[OSTRZEŻENIE] Nie znaleziono danych window.sections w HTML")
                return []

        except Exception as e:
            self.log(f"[BŁĄD] Błąd metody JSON: {e}")
            return []

    def detect_product_type(self, product_name, product_url=""):
        text_to_check = (product_name + " " + product_url).lower()
        mapping = {
            'drzwi': ['door', 'drzwi', 'porta', 'verte'],
            'płytki_ceramiczne': ['płytka','plytka','ceramic','tile','paradyż','paradyz','tubądzin','tubadzin','opoczno','domino','paradyz'],
            'listwy_przypodłogowe': ['listwa','listwy','przypodłogowa','baseboards','skirting'],
            'miska_wc': ['miska','wc','toilet','bowl','kompakt','stelaż','sedes','kompaktowa'],
            'umywalka': ['umywalka','basin','sink','washbasin','lavatory'],
            'bateria_umywalkowa': ['bateria','kran','faucet','tap','mixer','umywalkowa'],
            'wanna': ['wanna','bathtub','bath','akrylowa','stalowa'],
            'kabina_prysznicowa': ['kabina','prysznicowa','shower','cabin','enclosure'],
            'brodzik': ['brodzik','shower','tray','base','akrylowy'],
            'zestaw_prysznicowy': ['zestaw','prysznicowy','shower','set','deszczownica'],
        }
        for product_type, keywords in mapping.items():
            for kw in keywords:
                if kw in text_to_check:
                    return product_type
        return 'produkty_inne'

    def clean_filename(self, name):
        name = re.sub(r'(z\s*)?klamk[aą]ą?', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+z\s*\w*klamk\w*', '', name, flags=re.IGNORECASE)

        cleaned = re.sub(r'[<>:"/\\|?*]', '_', name)
        cleaned = re.sub(r'\s+', '_', cleaned)
        cleaned = cleaned.strip('_')
        return cleaned[:100]

    def create_product_folder_structure(self, output_path, product_type, product_name, index):
        type_folder = Path(output_path) / product_type

        clean_name = self.clean_filename(product_name)
        product_folder_name = f"{index:03d}_{clean_name}"
        product_folder = type_folder / product_folder_name

        product_folder.mkdir(parents=True, exist_ok=True)

        return str(product_folder), str(product_folder)

    def scraping_finished(self, success, error_msg=""):
        self.root.after(0, self._scraping_finished_ui, success, error_msg)

    def _scraping_finished_ui(self, success, error_msg):
        self.is_scraping = False
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        if success:
            self.progress_var.set("Zakończono pomyślnie!")
            self.log("[OK] Wszystkie produkty pobrane.")
            messagebox.showinfo("Sukces", f"Produkty zapisane w:\n{self.output_dir}")
        else:
            self.progress_var.set("Błąd podczas pobierania")
            if error_msg:
                self.log(f"[BŁĄD] {error_msg}")

def main():
    app = SeleniumKislistGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
