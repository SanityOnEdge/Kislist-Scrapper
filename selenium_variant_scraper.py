#!/usr/bin/env python3
"""
Selenium Variant Scraper - pobiera rzeczywiste obrazy drzwi dla każdego koloru
poprzez symulację kliknięć w kolory na stronie
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import json
import re
from urllib.parse import urljoin
import base64
from datetime import datetime
try:
    from PIL import Image
except Exception:
    Image = None

try:
    from ai_dom_analyzer import analyze_dom
except Exception:
    analyze_dom = None

class SeleniumVariantScraper:
    def __init__(self, headless=True, ai_image_detection=True, debug_log_path: str = ""):
        self.headless = headless
        self.ai_image_detection = ai_image_detection
        self.session = requests.Session()

        from pathlib import Path as _Path
        if not debug_log_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_dir = _Path('/mnt/RZECZY/AgentMode_Archive/scraper_debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_log_path = str(debug_dir / f'log_{ts}.jsonl')
        self._debug_log_path = debug_log_path
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'keep-alive'
        })
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[429,500,502,503,504])
            adapter = HTTPAdapter(pool_connections=50, pool_maxsize=100, max_retries=retry)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        except Exception:
            pass

        self._config_cache = {}
        self._driver_cache = None

        self.site_configs = {
            'porta.com.pl': {
                'main_image_selectors': [
                    'img[src*="/phavi/do/r,612"]',
                    'img[src*="/phavi/do/r,306"]',
                    '.product-gallery img:first-child',
                    '.gallery-main img',
                    '.main-image img',
                    'picture img'
                ],
                'color_button_selectors': [
                    '.products-tree-colors button',
                    '.swiper-slide button',
                    'button[class*="swiper-slide"]'
                ],
                'handle_selectors': [
                    '.products-tree-handles button',
                    '.handle-variants button',
                    '.handle-options button',
                    '.accessories button',
                    'li[class*="klamka"] button',
                    'button[class*="klamka"]',
                    'button[class*="handle"]'
                ],
                'cookie_accept_xpaths': [
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ', 'abcdefghijklmnopqrstuvwxyząćęłńóśźż'), 'akcept')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ', 'abcdefghijklmnopqrstuvwxyząćęłńóśźż'), 'zgadzam')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Accept')]"
                ],
                'wait_after_click': 1.5
            },
            'dekordia.pl': {
                'main_image_selectors': [
                    '.product-image img',
                    '.main-product-image',
                    '.gallery img:first-child'
                ],
                'color_button_selectors': [
                    '.color-options button',
                    '.variant-options button',
                    '.swatch-color'
                ],
                'handle_selectors': [
                    'button[class*="uchwyt"]',
                    'button[class*="klamka"]',
                    '.handle-options button',
                    '.accessories button'
                ],
                'cookie_accept_xpaths': [
                    "//button[contains(., 'Akceptuj')]",
                    "//button[contains(., 'Zgadzam')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Accept')]"
                ],
                'wait_after_click': 1
            },
            'domni.pl': {
                'main_image_selectors': [
                    'img[src*="domino"]',
                    'img[src*=".jpg"]',
                    'img[src*="dover"]',
                    'img[src*="/uploads/"]',
                    'img[src*="thumbnail"]',
                    '.product-images img:first-child',
                    '.gallery-main img',
                    '.product-gallery img',
                    '.main-image img',
                    '#product-image img',
                    '.product-photo img',
                    'img[src*="product"]',
                    'img[src*="/photo/"]'
                ],
                'color_button_selectors': [
                    '.variant-selector button',
                    '.color-variants button',
                    '.product-variants button',
                    '.variant-options button',
                    'button[data-variant]'
                ],
                'handle_selectors': [
                    'button[class*="uchwyt"]',
                    'button[class*="klamka"]',
                    '.handle-options button',
                    '.accessories button'
                ],
                'cookie_accept_xpaths': [
                    "//button[contains(., 'Akceptuj')]",
                    "//button[contains(., 'Zgadzam')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Accept')]"
                ],
                'wait_after_click': 1
            },
            'lazienkarium.pl': {
                'main_image_selectors': [
                    '.product-gallery img:first-child',
                    '.main-product-image img',
                    '.gallery img:first-child',
                    '#product-image img',
                    'img[src*="product"]',
                    'img[itemprop="image"]',
                    '.product__gallery img',
                    '.gallery__image img',
                    '.product__gallery a img',
                    'a[data-fancybox] img',
                    '.swiper-slide img',
                    'main img'
                ],
                'color_button_selectors': [
                    '.variant-selector button',
                    '.color-selector button',
                    '.product-options button',
                    'button[data-color]'
                ],
                'handle_selectors': [
                    'button[class*="uchwyt"]',
                    'button[class*="klamka"]',
                    '.handle-options button',
                    '.accessories button'
                ],
                'cookie_accept_xpaths': [
                    "//button[contains(., 'Akceptuj')]",
                    "//button[contains(., 'Zgadzam')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Accept')]"
                ],
                'wait_after_click': 1
            },
            'cersanit.com': {
                'main_image_selectors': [
                    '.product-gallery img',
                    '.main-image img',
                    'img[data-zoom]'
                ],
                'color_button_selectors': [
                    '.color-selector button',
                    '.variant-button',
                    '.option-color'
                ],
                'wait_after_click': 1
            },
            'default': {
                'main_image_selectors': [
                    'img[src*=".jpg"]',
                    'img[src*=".png"]',
                    'img[src*=".webp"]',
                    'img[src*="/uploads/"]',
                    'img[src*="thumbnail"]',
                    'img[src*="product"]',
                    'img[src*="/photo/"]',
                    'img[src*="/image/"]',
                    '.product img:first-child',
                    '.gallery img:first-child',
                    '.main img:first-child',
                    '#product-image img',
                    '.product-photo img',
                    '.product-images img',
                    '.main-image img',
                    'img[width="500"]', 'img[width="600"]', 'img[width="700"]',
                    'img[height="500"]', 'img[height="600"]',
                    'main img', 'article img', 'section img'
                ],
                'color_button_selectors': [
                    'button[class*="color"]',
                    'button[class*="variant"]',
                    'button[data-color]',
                    'button[data-variant]',
                    '.color button',
                    '.variant button',
                    '.options button',
                    'a[class*="color"]',
                    'a[class*="variant"]',
                    'no-variants'
                ],
                'handle_selectors': [
                    'button[class*="klamka"]',
                    'button[class*="handle"]',
                    'button[class*="uchwyt"]',
                    '.handle-options button',
                    '.accessories button'
                ],
                'cookie_accept_xpaths': [
                    "//button[contains(., 'Akceptuj')]",
                    "//button[contains(., 'Zgadzam')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Accept')]"
                ],
                'wait_after_click': 1.5
            }
        }

    def _dbg(self, event: str, **data):
        try:
            payload = {"ts": datetime.now().isoformat(), "event": event}
            payload.update(data)
            with open(self._debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(payload, ensure_ascii=False) + '\n')
        except Exception:
            pass

    def _resolve_image_url(self, driver, img_element):
        try:
            url = None
            url = img_element.get_attribute('src') or None

            if not url:
                for attr in ['data-src', 'data-large', 'data-zoom-image', 'data-zoom', 'data-original']:
                    val = img_element.get_attribute(attr)
                    if val and isinstance(val, str) and len(val) > 4:
                        url = val
                        break

            if not url:
                val = img_element.get_attribute('currentSrc')
                if val:
                    url = val

            if not url:
                srcset = img_element.get_attribute('srcset')
                if srcset:
                    candidates = []
                    for part in srcset.split(','):
                        part = part.strip()
                        if ' ' in part:
                            u, w = part.rsplit(' ', 1)
                        else:
                            u, w = part, '0w'
                        try:
                            size = int(w.rstrip('w'))
                        except Exception:
                            size = 0
                        candidates.append((size, u))
                    if candidates:
                        candidates.sort(reverse=True)
                        url = candidates[0][1]

            if not url:
                bg = driver.execute_script(
                    'return window.getComputedStyle(arguments[0]).getPropertyValue("background-image")',
                    img_element
                )
                if bg and 'url(' in bg:
                    start = bg.find('url(') + 4
                    end = bg.find(')', start)
                    candidate = bg[start:end].strip('"\'')
                    if candidate:
                        url = candidate

            if not url:
                return None

            if isinstance(url, str) and not (url.startswith('http') or url.startswith('data:') or url.startswith('blob:')):
                try:
                    url = urljoin(driver.current_url, url)
                except Exception:
                    pass

            return url
        except Exception:
            return None

    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        gpu_available = self.detect_gpu_support()
        if gpu_available and not self.headless:
            print("[INFO] GPU akceleracja włączona")
            options.add_argument('--enable-gpu')
            options.add_argument('--enable-accelerated-2d-canvas')
            options.add_argument('--enable-accelerated-video-decode')
            options.add_argument('--disable-gpu-sandbox')
        else:
            options.add_argument('--disable-gpu')

        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max-http-cache-size=67108864')
        options.add_argument('--renderer-process-limit=12')
        options.add_argument('--enable-aggressive-domstorage-flushing')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-web-security')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--page-load-strategy=eager')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')

        if gpu_available:
            options.add_argument('--window-size=1920,1080')
        else:
            options.add_argument('--window-size=1280,720')

        from selenium.webdriver.chrome.service import Service
        chrome_paths = ['/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/chrome']
        chrome_binary = None
        for path in chrome_paths:
            if Path(path).exists():
                chrome_binary = path
                break

        if chrome_binary:
            options.binary_location = chrome_binary
            print(f"[INFO] Używam przeglądarki: {chrome_binary}")

        try:
            return webdriver.Chrome(options=options)
        except Exception:
            service = Service('/usr/bin/chromedriver')
            return webdriver.Chrome(service=service, options=options)

    def detect_gpu_support(self):
        try:
            import subprocess
            import platform
            system = platform.system()

            if system == "Linux":
                try:
                    result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=3)
                    if 'VGA' in result.stdout or 'Display' in result.stdout:
                        gpu_info = subprocess.run(['lspci', '-v'], capture_output=True, text=True, timeout=3)
                        return 'Kernel driver in use' in gpu_info.stdout
                except:
                    pass
            elif system == "Windows":
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                         capture_output=True, text=True, timeout=3)
                    return result.returncode == 0 and len(result.stdout.strip()) > 20
                except:
                    pass
            elif system == "Darwin":
                try:
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'],
                                         capture_output=True, text=True, timeout=3)
                    return 'Graphics/Displays' in result.stdout
                except:
                    pass
            return False
        except:
            return False

    def get_site_config(self, url: str) -> dict:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()

        if domain in self._config_cache:
            return self._config_cache[domain]

        config = None
        for site_domain, site_config in self.site_configs.items():
            if site_domain in domain:
                print(f"[INFO] Używam konfiguracji dla: {site_domain}")
                config = site_config
                break

        if not config:
            print(f"[INFO] Używam uniwersalnej konfiguracji dla: {domain}")
            config = self.site_configs['default']

        self._config_cache[domain] = config
        return config

    def scrape_universal_variants(self, url: str, product_name: str, product_folder: str, product_type: str = "unknown"):
        print(f"[INFO] Selenium scraping: {url}")
        config = self.get_site_config(url)
        driver = self.setup_driver()
        output_path = Path(product_folder)

        try:
            driver.get(url)
            self._dbg('page_loaded', url=url, product_name=product_name, product_type=product_type, folder=str(output_path))
            print("[OK] Strona załadowana")

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)

            try:
                accepted = self.accept_cookies(driver, config)
                self._dbg('cookies_handled', accepted=bool(accepted))
            except Exception as e:
                self._dbg('cookies_error', error=str(e))

            main_img = None
            for selector in config['main_image_selectors']:
                try:
                    candidate = driver.find_element(By.CSS_SELECTOR, selector)
                    if candidate:
                        resolved = self._resolve_image_url(driver, candidate)
                        if resolved:
                            main_img = candidate
                            print(f"[OK] Znaleziono główny obraz: {selector}")
                            break
                except:
                    continue

            if not main_img:
                self._dbg('main_image_not_found')
                print("[BŁĄD] Nie znaleziono głównego obrazu produktu")
                return

            self._dbg('main_image_found', selector_used=selector)
            color_buttons = []
            for selector in config['color_button_selectors']:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons:
                        color_buttons = buttons
                        print(f"[OK] Znaleziono {len(buttons)} przycisków kolorów ({selector})")
                        break
                except:
                    continue

            if not color_buttons:
                self._dbg('no_color_buttons')
                print("[OSTRZEŻENIE] Nie znaleziono przycisków kolorów - próbuję zapisać główny obraz")
                return self.save_single_variant(driver, main_img, url, "Domyslny", output_path)

            output_path.mkdir(parents=True, exist_ok=True)
            variants_saved = 0

            for i in range(len(color_buttons)):
                try:
                    fresh_buttons = driver.find_elements(By.CSS_SELECTOR, config['color_button_selectors'][0])
                    if i >= len(fresh_buttons):
                        print(f"   [OSTRZEŻENIE] Przycisk {i+1} już nie istnieje")
                        continue

                    button = fresh_buttons[i]
                    color_name = self.extract_color_name(button)
                    if not color_name:
                        color_name = f"Wariant_{i+1:02d}"

                    print(f"[INFO] {i+1:02d}. Kliknięcie w kolor: {color_name}")

                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(config['wait_after_click'])

                    fresh_main_img = None
                    for selector in config['main_image_selectors']:
                        try:
                            candidate = driver.find_element(By.CSS_SELECTOR, selector)
                            if candidate and self._resolve_image_url(driver, candidate):
                                fresh_main_img = candidate
                                break
                        except:
                            continue

                    if not fresh_main_img:
                        print(f"   [OSTRZEŻENIE] Nie można znaleźć głównego obrazu po kliknięciu")
                        continue

                    variant_images = self.collect_variant_images(driver, config)
                    self._dbg('variant_images_collected', color=color_name, count=len(variant_images))

                    if variant_images:
                        variant_dir = output_path / color_name
                        variant_dir.mkdir(exist_ok=True)

                        success = self.download_variant_images(
                            variant_images,
                            variant_dir,
                            driver=driver,
                            main_element=fresh_main_img,
                            config=config,
                            color_name=color_name
                        )
                        if success:
                            print(f"   [OK] Zapisano wariant: {color_name} ({len(variant_images)} obrazów)")
                            variants_saved += 1
                        else:
                            print(f"   [BŁĄD] Nie udało się zapisać obrazów dla: {color_name}")
                    else:
                        print(f"   [BŁĄD] Brak obrazów dla wariantu: {color_name}")

                except Exception as e:
                    print(f"   [BŁĄD] Błąd dla wariantu {i}: {e}")
                    continue

            print(f"[OK] Zakończono! Zapisano {variants_saved} wariantów w {output_path}")

        except Exception as e:
            print(f"[BŁĄD] Błąd scraping Selenium: {e}")

        finally:
            driver.quit()

    def accept_cookies(self, driver, config) -> bool:
        try:
            tried = 0
            xpaths = config.get('cookie_accept_xpaths', []) or self.site_configs.get('default', {}).get('cookie_accept_xpaths', [])
            for xp in xpaths:
                try:
                    elems = driver.find_elements(By.XPATH, xp)
                    if elems:
                        driver.execute_script("arguments[0].click();", elems[0])
                        time.sleep(0.3)
                        tried += 1
                        break
                except Exception:
                    continue
            generic = [
                "//button[contains(., 'Akceptuj')]",
                "//button[contains(., 'Zgadzam')]",
                "//button[contains(., 'Zamknij')]",
                "//button[contains(., 'OK')]",
                "//button[contains(., 'Accept')]",
                "//a[contains(., 'Akceptuj')]",
                "//a[contains(., 'Zamknij')]",
            ]
            for xp in generic:
                try:
                    elems = driver.find_elements(By.XPATH, xp)
                    if elems:
                        driver.execute_script("arguments[0].click();", elems[0])
                        time.sleep(0.3)
                        tried += 1
                        break
                except Exception:
                    continue
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except Exception:
                pass
            try:
                self.hide_overlays(driver)
            except Exception:
                pass
            return tried > 0
        except Exception:
            return False

    def hide_overlays(self, driver):
        try:
            js = """
                const selectors = [
                  '[id*="cookie"i]','[class*="cookie"i]','[id*="consent"i]','[class*="consent"i]',
                  '[id*="rodo"i]','[class*="rodo"i]','[id*="gdpr"i]','[class*="gdpr"i]',
                  '.cc-window','.cky-consent-container','.cookie-consent','.cookie-banner','.didomi-popup'
                ];
                for (const sel of selectors){
                  document.querySelectorAll(sel).forEach(el=>{try{el.style.setProperty('display','none','important'); el.style.setProperty('visibility','hidden','important'); el.style.setProperty('opacity','0','important'); el.removeAttribute('aria-modal');}catch(e){}});
                }
            """
            driver.execute_script(js)
        except Exception:
            pass

    def save_single_variant(self, driver, main_img, url, variant_name, output_path):
        try:
            variant_dir = output_path / variant_name
            variant_dir.mkdir(parents=True, exist_ok=True)

            current_image_src = None
            try:
                current_image_src = self._resolve_image_url(driver, main_img)
            except Exception:
                current_image_src = None
            if not current_image_src:
                og = self._get_og_image_url(driver)
                if og:
                    current_image_src = og
            if current_image_src:
                final_path = self.download_image(current_image_src, variant_dir / "image.jpg")
                if final_path:
                    print(f"[OK] Zapisano pojedynczy wariant (HTTP): {variant_name}")

            try:
                config = self.get_site_config(url)
                imgs = self.collect_variant_images(driver, config)
                seen = set()
                if current_image_src:
                    seen.add(current_image_src)
                idx = 1
                for it in imgs:
                    if it.get('type') != 'main':
                        continue
                    u = it.get('url')
                    if not u or u in seen:
                        continue
                    ext = '.jpg'
                    low = u.lower()
                    if '.png' in low:
                        ext = '.png'
                    elif '.webp' in low:
                        ext = '.webp'
                    self.download_image(u, variant_dir / f"main_{idx:02d}{ext}")
                    seen.add(u)
                    idx += 1
                    if idx > 3:
                        break
            except Exception:
                pass

            try:
                if not any(variant_dir.iterdir()):
                    image_path = variant_dir / "image.png"
                    if self.capture_element_screenshot(main_img, image_path):
                        print(f"[OK] Zapisano pojedynczy wariant (screenshot): {variant_name}")
                        print(f"[OK] Zakończono! Zapisano 1 wariant w {output_path}")
                        return True
            except Exception:
                pass

            for _ in variant_dir.iterdir():
                return True

            print(f"[BŁĄD] Nie udało się zapisać pojedynczego wariantu")
        except Exception as e:
            print(f"[BŁĄD] Błąd zapisywania pojedynczego wariantu: {e}")
        return False

    def extract_color_name(self, button):
        try:
            text = button.text.strip()
            if text:
                return self.sanitize_filename(text)

            color_attr = button.get_attribute("data-color")
            if color_attr:
                return self.sanitize_filename(color_attr)

            alt = button.get_attribute("alt") or button.get_attribute("title")
            if alt:
                return self.sanitize_filename(alt)

            imgs = button.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                alt = img.get_attribute("alt")
                if alt:
                    return self.sanitize_filename(alt)

                src = img.get_attribute("src")
                if src and 'okleina' in src:
                    parts = src.split('-')
                    if len(parts) > 2:
                        color_part = parts[-1].split('.')[0]
                        color_part = color_part.split('?')[0]
                        if color_part and len(color_part) > 3:
                            color_name = self.format_color_name(color_part)
                            return self.sanitize_filename(color_name)

        except Exception as e:
            print(f"   [OSTRZEŻENIE] Błąd wyciągania nazwy koloru: {e}")

        return None

    def format_color_name(self, raw_name: str) -> str:
        mappings = {
            'dabmauvella': 'Dab_Mauvella',
            'dabskandynawski': 'Dab_Skandynawski',
            'dabsyberyjski': 'Dab_Syberyjski',
            'bukskandynawski': 'Buk_Skandynawski',
            'matowy': 'Matowy',
            'dabklasyczny': 'Dab_Klasyczny',
            'dabnaturalny': 'Dab_Naturalny',
            'dabcraftzloty': 'Dab_Craft_Zloty',
            'dabkalifornia': 'Dab_Kalifornia',
            'dabhawana': 'Dab_Hawana',
            'bialy': 'Bialy',
            'szary': 'Szary',
            'fiord': 'Fiord',
            'kaszmir': 'Kaszmir',
            'oliwka': 'Oliwka',
            'orzechverona': 'Orzech_Verona',
            'orzech': 'Orzech',
            'verona': 'Verona',
            'hamilton': 'Hamilton',
            'catania': 'Catania',
            'wengewhite': 'Wenge_White',
            'sosnanorweska': 'Sosna_Norweska',
            'sosnaandersen': 'Sosna_Andersen',
            'akacjasrebrna': 'Akacja_Srebrna',
            'akacjamiodowa': 'Akacja_Miodowa',
            'dabszkarlatny': 'Dab_Szkarlatny',
            'dabciemny': 'Dab_Ciemny',
            'bielony': 'Bielony',
            'srebrny': 'Srebrny',
            'srebrzysty': 'Srebrzysty'
        }
        return mappings.get(raw_name.lower(), raw_name.title())

    def _is_element_ad_like(self, driver, element) -> bool:
        try:
            js = """
                const el = arguments[0];
                function bad(e){
                  if(!e) return false;
                  const id=(e.id||'').toLowerCase();
                  const cl=(e.className||'').toString().toLowerCase();
                  const bad=['banner','ads','ad-','promo','marketing','newsletter','social','cookie','consent','rodo','gdpr','logo','header','footer','nav','menu','popup','modal'];
                  return bad.some(k=>id.includes(k)||cl.includes(k));
                }
                let cur=el, d=0;
                while(cur && d<6){ if(bad(cur)) return true; cur=cur.parentElement; d++; }
                return false;
            """
            return bool(driver.execute_script(js, element))
        except Exception:
            return False

    def _is_image_visible_large(self, driver, element) -> bool:
        try:
            js = """
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                const visible = rect.width>50 && rect.height>50 && rect.bottom>0 && rect.right>0;
                const nw = el.naturalWidth||0; const nh = el.naturalHeight||0;
                return visible && (nw>=200 || nh>=200);
            """
            return bool(driver.execute_script(js, element))
        except Exception:
            return True

    def _get_og_image_url(self, driver) -> str:
        try:
            return driver.execute_script("""
                const m=document.querySelector('meta[property="og:image"],meta[name="og:image"]');
                return m?m.content:'';
            """) or ''
        except Exception:
            return ''

    def collect_variant_images(self, driver, config) -> list:
        images = []
        try:
            try:
                if analyze_dom is not None:
                    ai = analyze_dom(driver, driver.current_url)
                else:
                    ai = None
            except Exception:
                ai = None
            if ai:
                for u in ai.get('product_main', []) or []:
                    images.append({'url': u, 'type': 'main', 'filename': f"main_{len(images)+1}.jpg"})
                for u in ai.get('handles', []) or []:
                    images.append({'url': u, 'type': 'klamka', 'filename': f"klamka_{len(images)+1}.jpg"})

            gallery_selectors = [
                '.product-gallery img',
                '.gallery-main img',
                '.main-image img',
                '.product-images img',
                'picture img',
                'img[data-src]',
                'source[srcset]',
                'img[src*="/phavi/do/r,612"]',
                'img[src*="/phavi/do/r,306"]',
                '.swiper-slide img',
                '[data-gallery] img',
                '.product__gallery img',
                'a[data-fancybox] img'
            ]

            for selector in gallery_selectors:
                try:
                    gallery_imgs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in gallery_imgs:
                        if self._is_element_ad_like(driver, img):
                            continue
                        if not self._is_image_visible_large(driver, img):
                            continue
                        src = self._resolve_image_url(driver, img)
                        if src and src.startswith('http'):
                            if not any(src == existing['url'] for existing in images):
                                img_type = self.classify_image_type(src)
                                images.append({
                                    'url': src,
                                    'type': img_type,
                                    'filename': f"{img_type}_{len(images)+1}.jpg"
                                })

                    if images:
                        break
                except Exception:
                    continue

            anchor_selectors = [
                '.product-gallery a',
                '.product__gallery a',
                'a[data-fancybox]',
                'a[href$=".jpg"], a[href$=".png"], a[href$=".webp"]'
            ]
            for a_sel in anchor_selectors:
                try:
                    anchors = driver.find_elements(By.CSS_SELECTOR, a_sel)
                    for a in anchors:
                        if self._is_element_ad_like(driver, a):
                            continue
                        href = a.get_attribute('href') or ''
                        if href and (href.endswith('.jpg') or href.endswith('.png') or href.endswith('.webp')):
                            if not (href.startswith('http') or href.startswith('data:')):
                                try:
                                    href = urljoin(driver.current_url, href)
                                except Exception:
                                    pass
                            if not any(href == e['url'] for e in images):
                                images.append({'url': href, 'type': 'main', 'filename': f"main_{len(images)+1}.jpg"})
                    if anchors and len(images) > 0:
                        break
                except Exception:
                    continue

            if not images:
                for selector in config['main_image_selectors']:
                    try:
                        main_img = driver.find_element(By.CSS_SELECTOR, selector)
                        if main_img and not self._is_element_ad_like(driver, main_img):
                            src = self._resolve_image_url(driver, main_img)
                            if src:
                                images.append({
                                    'url': src,
                                    'type': 'main',
                                    'filename': 'door_variant.jpg'
                                })
                                break
                    except:
                        continue
                if not images:
                    og = self._get_og_image_url(driver)
                    if og:
                        images.append({'url': og, 'type': 'main', 'filename': 'door_variant.jpg'})

            try:
                from urllib.parse import urlparse
                domain = urlparse(driver.current_url).netloc.lower()
            except Exception:
                domain = ''

            if domain.endswith('porta.com.pl') or domain.endswith('dekordia.pl') or domain.endswith('domni.pl') or domain.endswith('lazienkarium.pl'):
                try:
                    all_imgs = driver.find_elements(By.TAG_NAME, 'img')
                    for img in all_imgs:
                        if self._is_element_ad_like(driver, img):
                            continue
                        if not self._is_image_visible_large(driver, img):
                            continue
                        resolved = self._resolve_image_url(driver, img)
                        if not resolved or not resolved.startswith('http'):
                            continue
                        if any(resolved == e['url'] for e in images):
                            continue
                        img_type = self.classify_image_type(resolved)
                        if img_type in ['drzwi','klamka','main','detail']:
                            images.append({
                                'url': resolved,
                                'type': img_type,
                                'filename': f"{img_type}_{len(images)+1}.jpg"
                            })
                except Exception:
                    pass

            if images and self.ai_image_detection:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(driver.current_url).netloc.lower()
                    if 'porta.com.pl' in domain:
                        pass
                    else:
                        images = self.ai_filter_product_images(driver, images)
                except Exception:
                    images = self.ai_filter_product_images(driver, images)

            print(f"   [INFO] Znaleziono {len(images)} obrazów wariantu")
            return images

        except Exception as e:
            print(f"   [OSTRZEŻENIE] Błąd zbierania obrazów: {e}")
            return []

    def classify_image_type(self, url: str) -> str:
        url_lower = url.lower()
        if 'klamka' in url_lower or 'handle' in url_lower or any(k in url_lower for k in [
            'doro','simplo','euforia','fioro','segura','unico','eleganto','azura','lago','moderno','organic','lungo','fiumo'
        ]):
            return 'klamka'
        elif 'osciez' in url_lower or 'frame' in url_lower:
            return 'osciez'
        elif 'door' in url_lower or 'drzwi' in url_lower or '/do/' in url_lower or 'phavi/do/' in url_lower:
            return 'drzwi'
        elif 'detail' in url_lower or 'close' in url_lower:
            return 'detail'
        else:
            return 'main'

    def ai_filter_product_images(self, driver, images):
        if not self.ai_image_detection:
            return images

        try:
            filtered_images = []
            for img_data in images:
                url = img_data['url'].lower()
                is_product = True

                promotion_keywords = [
                    'banner', 'promo', 'sale', 'discount', 'popup', 'modal',
                    'advertisement', 'ad_', 'marketing', 'newsletter', 'social',
                    'facebook', 'instagram', 'youtube', 'logo', 'header',
                    'footer', 'menu', 'nav', 'sidebar', 'widget'
                ]

                for keyword in promotion_keywords:
                    if keyword in url:
                        print(f"   [INFO] AI odrzuciło: {keyword} w {url[:50]}...")
                        is_product = False
                        break

                product_keywords = [
                    'product', 'item', 'photo', 'image', 'gallery', 'main',
                    'thumbnail', 'detail', '.jpg', '.png', '.webp'
                ]

                if is_product:
                    product_score = sum(1 for kw in product_keywords if kw in url)
                    if 'domni.pl' in url:
                        if any(size in url for size in ['800', '1000', '1200', 'large', 'big']):
                            product_score += 2
                        elif any(size in url for size in ['thumb', 'small', '100', '150']):
                            product_score -= 1
                    img_data['ai_score'] = product_score
                    filtered_images.append(img_data)

            filtered_images.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
            if len(filtered_images) != len(images):
                print(f"   [INFO] AI przefiltrowało {len(images)} -> {len(filtered_images)} obrazów")
            return filtered_images[:10]

        except Exception as e:
            print(f"   [OSTRZEŻENIE] Błąd AI filtrowania: {e}")
            return images

    def list_handle_options(self, driver, config):
        options = []
        try:
            selectors = config.get('handle_selectors', [])
            for sel in selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elems:
                        label = (el.text or el.get_attribute('title') or el.get_attribute('aria-label') or '').strip()
                        img_url = None
                        imgs = el.find_elements(By.TAG_NAME, 'img')
                        for img in imgs:
                            if not label:
                                alt = (img.get_attribute('alt') or '').strip()
                                if alt:
                                    label = alt
                            resolved = self._resolve_image_url(driver, img)
                            if resolved and resolved.startswith('http'):
                                img_url = resolved
                                break
                        if label:
                            options.append({'name': self.sanitize_filename(label), 'elem': el, 'img_url': img_url})
                except Exception:
                    continue
        except Exception:
            pass
        dedup = {}
        for opt in options:
            dedup[opt['name']] = opt
        return list(dedup.values())

    def download_variant_images(self, images: list, variant_dir: Path, driver=None, main_element=None, config=None, color_name: str = None) -> bool:
        success_count = 0
        if driver is None or main_element is None:
            print("     [OSTRZEŻENIE] Brak driver/main_element do screenshotów, pomijam")
            return False

        try:
            variant_dir.mkdir(parents=True, exist_ok=True)
            saved_http = None
            try:
                main_src = self._resolve_image_url(driver, main_element)
            except Exception:
                main_src = None
            if main_src:
                http_target = variant_dir / "image.jpg"
                saved_http = self.download_image(main_src, http_target)
                if saved_http:
                    success_count += 1
                    print(f"     [OK] drzwi (HTTP): {saved_http.name}")
            if not saved_http:
                try:
                    door_png = variant_dir / "image.png"
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", main_element)
                    self.hide_overlays(driver)
                    if self.capture_element_screenshot(main_element, door_png):
                        success_count += 1
                        print(f"     [OK] drzwi (screenshot): {door_png.name}")
                except Exception as se:
                    print(f"     [BŁĄD] Screenshot drzwi nieudany: {se}")
        except Exception as e:
            print(f"     [OSTRZEŻENIE] Błąd zapisu drzwi: {e}")

        saved_handle_paths = []
        handle_options = self.list_handle_options(driver, (config or {}))
        if handle_options and len(handle_options) < 2:
            img_candidates = [img for img in images if img.get('type') == 'klamka']
            for cand in img_candidates:
                name_guess = Path(cand.get('url','')).stem or 'Klamka'
                name_guess = self.sanitize_filename(name_guess)
                if not any(o['name'] == name_guess for o in handle_options):
                    handle_options.append({'name': name_guess, 'elem': None, 'img_url': cand.get('url')})
        if handle_options:
            for h_idx, opt in enumerate(handle_options, 1):
                try:
                    if opt.get('img_url'):
                        handle_url = opt['img_url']
                        ext = '.jpg'
                        low = handle_url.lower()
                        if '.png' in low:
                            ext = '.png'
                        elif '.webp' in low:
                            ext = '.webp'
                        handle_path = variant_dir / f"klamka_{h_idx:02d}{ext}"
                        final_handle = self.download_image(handle_url, handle_path)
                        if final_handle:
                            saved_handle_paths.append({'path': final_handle, 'name': opt['name']})
                            success_count += 1
                            print(f"     [OK] klamka: {final_handle.name}")
                except Exception as e:
                    print(f"     [OSTRZEŻENIE] Błąd klamki {h_idx}: {e}")

        try:
            if handle_options:
                produced = 0
                for opt in handle_options:
                    try:
                        if opt.get('elem') is not None:
                            driver.execute_script("arguments[0].click();", opt['elem'])
                            time.sleep((config or {}).get('wait_after_click', 1.0))
                        handle_name = opt['name'] or 'Klamka'
                        composed_jpg = variant_dir / f"{color_name or variant_dir.name}_{handle_name}.jpg"
                        used_http = False
                        try:
                            current_src = self._resolve_image_url(driver, main_element)
                            if current_src:
                                saved_http2 = self.download_image(current_src, composed_jpg)
                                if saved_http2:
                                    print(f"     [INFO] kompozyt (HTTP): {composed_jpg.name}")
                                    success_count += 1
                                    produced += 1
                                    used_http = True
                        except Exception:
                            used_http = False
                        if not used_http:
                            tmp_png = composed_jpg.with_suffix('.png')
                            self.hide_overlays(driver)
                            if self.capture_element_screenshot(main_element, tmp_png):
                                if self._png_to_jpg(tmp_png, composed_jpg):
                                    try:
                                        tmp_png.unlink(missing_ok=True)
                                    except Exception:
                                        pass
                                    print(f"     [INFO] kompozyt: {composed_jpg.name}")
                                    success_count += 1
                                    produced += 1
                                else:
                                    try:
                                        tmp_png.rename(composed_jpg)
                                        print(f"     [INFO] kompozyt (bez konwersji): {composed_jpg.name}")
                                        success_count += 1
                                        produced += 1
                                    except Exception as ce:
                                        print(f"     [OSTRZEŻENIE] Kompozyt błąd zapisu JPG: {ce}")
                    except Exception as ce:
                        print(f"     [OSTRZEŻENIE] Kompozyt UI błąd: {ce}")
                if produced < 2 and len(handle_options) >= 2:
                    try:
                        for opt in handle_options[:2]:
                            if opt.get('elem') is not None:
                                driver.execute_script("arguments[0].click();", opt['elem'])
                                time.sleep((config or {}).get('wait_after_click', 1.0))
                            handle_name = opt['name'] or 'Klamka'
                            composed_jpg = variant_dir / f"{color_name or variant_dir.name}_{handle_name}_alt.jpg"
                            tmp_png = composed_jpg.with_suffix('.png')
                            self.hide_overlays(driver)
                            if self.capture_element_screenshot(main_element, tmp_png):
                                if self._png_to_jpg(tmp_png, composed_jpg):
                                    try:
                                        tmp_png.unlink(missing_ok=True)
                                    except Exception:
                                        pass
                                    print(f"     [INFO] kompozyt ALT: {composed_jpg.name}")
                                    success_count += 1
                    except Exception:
                        pass
        except Exception as e:
            print(f"     [OSTRZEŻENIE] Błąd kompozytu (UI/screenshot): {e}")

        try:
            main_urls = []
            base_dir = ''
            try:
                cur = self._resolve_image_url(driver, main_element)
                if cur:
                    from urllib.parse import urlparse
                    p = urlparse(cur)
                    base_dir = p.scheme + '://' + p.netloc + p.path.rsplit('/',1)[0]
            except Exception:
                pass
            for img in images:
                if img.get('type') in ['main', 'drzwi']:
                    u = img.get('url')
                    if not u:
                        continue
                    if base_dir and not u.startswith(base_dir):
                        continue
                    if u not in main_urls:
                        main_urls.append(u)
                if len(main_urls) >= 3:
                    break
            for i, u in enumerate(main_urls, 1):
                try:
                    ext = '.jpg'
                    low = u.lower()
                    if '.png' in low:
                        ext = '.png'
                    elif '.webp' in low:
                        ext = '.webp'
                    self.download_image(u, (variant_dir / f"main_{i:02d}{ext}"))
                except Exception:
                    pass
        except Exception:
            pass

        return success_count > 0

    def click_handle_option(self, driver, handle_name: str, wait_after_click: float = 1.0) -> bool:
        try:
            from selenium.webdriver.common.by import By
            import time
            name_low = handle_name.lower()
            xpath = f"//*[self::button or self::a or self::div][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ', 'abcdefghijklmnopqrstuvwxyząćęłńóśźż'), '{name_low}')]"
            elems = driver.find_elements(By.XPATH, xpath)
            if elems:
                driver.execute_script("arguments[0].click();", elems[0])
                time.sleep(wait_after_click)
                return True
        except Exception:
            pass
        return False

    def capture_element_screenshot(self, element, save_path: Path) -> bool:
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            return element.screenshot(str(save_path))
        except Exception:
            return False

    def _png_to_jpg(self, png_path: Path, jpg_path: Path) -> bool:
        try:
            if Image is None:
                return False
            with Image.open(png_path) as im:
                rgb = im.convert('RGB')
                jpg_path.parent.mkdir(parents=True, exist_ok=True)
                rgb.save(jpg_path, format='JPEG', quality=92, optimize=True)
            return True
        except Exception:
            return False

    def _ext_from_magic(self, content: bytes) -> str:
        try:
            if len(content) >= 12:
                if content[:2] == b'\xff\xd8':
                    return '.jpg'
                if content[:8] == b'\x89PNG\r\n\x1a\n':
                    return '.png'
                if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
                    return '.webp'
        except Exception:
            pass
        return ''

    def download_image(self, url: str, filepath: Path):
        try:
            if isinstance(url, str) and url.startswith('data:image'):
                try:
                    header, data = url.split(',', 1)
                    ext = '.png'
                    if 'jpeg' in header or 'jpg' in header:
                        ext = '.jpg'
                    elif 'webp' in header:
                        ext = '.webp'
                    if filepath.suffix.lower() == '':
                        filepath = filepath.with_suffix(ext)
                    binary = base64.b64decode(data)
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, 'wb') as f:
                        f.write(binary)
                    return filepath
                except Exception as e:
                    print(f"   [OSTRZEŻENIE] Błąd dekodowania data:image: {e}")
                    return False

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            ctype = (response.headers.get('Content-Type') or '').lower()
            if 'image/' not in ctype:
                return None

            try:
                ext = None
                if 'image/jpeg' in ctype or 'image/jpg' in ctype:
                    ext = '.jpg'
                elif 'image/png' in ctype:
                    ext = '.png'
                elif 'image/webp' in ctype:
                    ext = '.webp'
                if not ext:
                    ext = self._ext_from_magic(response.content)
                if ext and filepath.suffix.lower() != ext:
                    filepath = filepath.with_suffix(ext)
            except Exception:
                pass

            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filepath
        except Exception as e:
            print(f"   [OSTRZEŻENIE] Błąd pobierania {url}: {e}")
            return None

    def sanitize_filename(self, filename: str) -> str:
        if not filename:
            return "unknown"

        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
            'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
        }

        for pl, en in replacements.items():
            filename = filename.replace(pl, en)

        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('_')

        return filename[:100] if len(filename) > 100 else filename

def test_selenium_scraper():
    print("[INFO] Test Selenium Variant Scraper")
    scraper = SeleniumVariantScraper(headless=False)
    url = "https://www.porta.com.pl/modele-drzwi/porta-decor-model-p"
    product_name = "001_PORTA_DECOR_MODEL_P"
    scraper.scrape_universal_variants(url, product_name)

if __name__ == "__main__":
    test_selenium_scraper()
