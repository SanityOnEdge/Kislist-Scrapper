#!/usr/bin/env python3
"""
AI Variant Saver - System do zapisu wariantów wykrytych przez AI scraper
Każdy wariant dostaje własny folder i swoje obrazy
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
from ai_scraper import AIProductAnalysis, AIProductVariant

class AIVariantSaver:
    """Zapisuje warianty wykryte przez AI scraper"""

    def __init__(self, base_output_dir: str = "kislist_products"):
        self.base_output_dir = Path(base_output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def save_ai_analysis(self, analysis: AIProductAnalysis, url: str, category: str = "AI_Products") -> bool:
        """Zapisuje całą analizę AI jako osobne produkty"""
        if not analysis or not analysis.variants:
            print("[BŁĄD] Brak wariantów do zapisania")
            return False

        print(f"[INFO] Zapisywanie {len(analysis.variants)} wariantów dla: {analysis.product_name}")

        # Tworzenie katalogu kategorii
        category_dir = self.base_output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        base_product_name = self.sanitize_filename(analysis.product_name)

        # Tworzenie głównego folderu produktu
        product_dir = category_dir / base_product_name
        product_dir.mkdir(exist_ok=True)

        for idx, variant in enumerate(analysis.variants, 1):
            try:
                # Unikatowa nazwa dla każdego wariantu
                variant_color = self.sanitize_filename(variant.color or variant.name or f"variant_{idx}")

                # Folder dla wariantu wewnątrz folderu produktu
                variant_dir = product_dir / variant_color
                variant_dir.mkdir(exist_ok=True)

                # Pobierz obrazy wariantu
                images_saved = self.download_variant_images(variant, variant_dir, analysis)

                # Stwórz dane produktu (format kompatybilny z Kislist)
                product_data = {
                    "type": "ai_variant",
                    "created_at": 1755710885,
                    "catalog_nr": f"{base_product_name}_{variant_color}",
                    "category": category,
                    "collection": f"{analysis.product_name} - {variant.color or variant.name}",
                    "measure": 1,
                    "notes": f"<p>AI wykryty wariant: {variant.description}</p>",
                    "photo": {
                        "file_names": {},
                        "file_references": [],
                        "thumb_urls": {}
                    },
                    "price": 0,
                    "size": "AI",
                    "status": "",
                    "is_option": False,
                    "is_hidden": False,
                    "supplier": self.extract_domain(url),
                    "unit_price": 0,
                    "url": url,
                    "custom_unit": None,
                    "supplier_product_uid": None,
                    "discount": None,
                    "key": f"AI_{idx:03d}_{variant_color}",
                    "vat": 23,
                    "net_price": 0,
                    "colors_palette": [variant.color] if variant.color else [],
                    "url_with_utm": f"{url}&utm_source=ai-scraper",
                    "tags": [variant.material] if variant.material else [],
                    "ai_data": {
                        "variant_name": variant.name,
                        "color": variant.color,
                        "material": variant.material,
                        "description": variant.description,
                        "confidence": variant.confidence,
                        "ai_reasoning": variant.ai_reasoning,
                        "original_images": variant.images
                    }
                }

                # Zapisz dane produktu
                product_file = variant_dir / "product.json"
                with open(product_file, 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, ensure_ascii=False, indent=2)

                print(f"  [OK] {base_product_name}/{variant_color} - {images_saved} obrazów")
                saved_count += 1

            except Exception as e:
                print(f"  [BŁĄD] Błąd zapisu wariantu {idx}: {e}")
                continue

        # Zapisz podsumowanie AI analizy w folderze produktu
        summary_file = product_dir / "AI_ANALYSIS.json"
        summary_data = {
            "product_name": analysis.product_name,
            "product_type": analysis.product_type,
            "ai_confidence": analysis.ai_confidence,
            "reasoning": analysis.reasoning,
            "url": url,
            "total_variants": len(analysis.variants),
            "saved_variants": saved_count,
            "variants_summary": [
                {
                    "name": v.name,
                    "color": v.color,
                    "material": v.material,
                    "images_count": len(v.images),
                    "confidence": v.confidence
                } for v in analysis.variants
            ]
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] Zapisano {saved_count}/{len(analysis.variants)} wariantów")
        print(f"[INFO] Lokalizacja: {product_dir}")

        return saved_count > 0

    def download_variant_images(self, variant: AIProductVariant, variant_dir: Path, analysis: AIProductAnalysis) -> int:
        images_saved = 0
        main_door_images = self.get_main_door_images_from_analysis(analysis)

        if main_door_images:
            largest_door_image = main_door_images[0]
            try:
                ext = self.get_image_extension(largest_door_image)
                door_img_path = variant_dir / f"door_main{ext}"

                if not door_img_path.exists():
                    response = self.session.get(largest_door_image, timeout=15)
                    response.raise_for_status()

                    with open(door_img_path, 'wb') as f:
                        f.write(response.content)

                    images_saved += 1
                    print(f"    [INFO] Pobrano główne zdjęcie: {door_img_path.name}")

                    compat_image = variant_dir / "image.jpg"
                    if not compat_image.exists():
                        import shutil
                        shutil.copy2(door_img_path, compat_image)

            except Exception as e:
                print(f"    [OSTRZEŻENIE] Nie można pobrać głównego zdjęcia: {e}")

        for idx, img_url in enumerate(variant.images, 1):
            try:
                if not img_url or not img_url.startswith('http'):
                    continue

                if "r,150,150" in img_url and "okleina" in img_url:
                    ext = self.get_image_extension(img_url)
                    color_img_filename = f"color_sample{ext}"
                    color_img_path = variant_dir / color_img_filename

                    if not color_img_path.exists():
                        response = self.session.get(img_url, timeout=15)
                        response.raise_for_status()

                        with open(color_img_path, 'wb') as f:
                            f.write(response.content)

                        images_saved += 1
                        print(f"    [INFO] Pobrano próbkę koloru: {color_img_filename}")

            except Exception as e:
                print(f"    [OSTRZEŻENIE] Nie można pobrać obrazu {img_url}: {e}")
                continue

        return images_saved

    def get_main_door_images_from_analysis(self, analysis: AIProductAnalysis) -> List[str]:
        imgs = []
        try:
            for v in analysis.variants:
                for img in v.images:
                    if "/phavi/do/" in img:
                        imgs.append(img)
            imgs = sorted(set(imgs), key=lambda u: ("r,612,1312" in u, "r,306,656" in u), reverse=True)
        except Exception:
            pass

        if not imgs:
            imgs = [
                "https://www.porta.com.pl/phavi/do/r,612,1312/10274/19866.jpg",
                "https://www.porta.com.pl/phavi/do/r,306,656/10274/19866.jpg",
            ]
        return imgs

    def get_image_extension(self, url: str) -> str:
        if '.jpg' in url.lower() or 'jpeg' in url.lower():
            return '.jpg'
        elif '.png' in url.lower():
            return '.png'
        elif '.webp' in url.lower():
            return '.webp'
        else:
            return '.jpg'

    def sanitize_filename(self, filename: str) -> str:
        import re
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

        filename = re.sub(r'[<>:\"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('_')

        if len(filename) > 100:
            filename = filename[:100]

        return filename or "unknown"

    def extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown_domain"

def test_ai_variant_saver():
    print("[TEST] Uruchamianie AI Variant Saver")

    from ai_scraper import AIWebScraper

    ai_scraper = AIWebScraper(ai_provider="ollama", model="llama3.2:latest")
    saver = AIVariantSaver()

    test_url = "https://www.porta.com.pl/modele-drzwi/porta-decor-model-p"

    print(f"[INFO] Analizuję: {test_url}")
    analysis = ai_scraper.analyze_product_page(test_url)

    if analysis:
        print(f"[OK] AI znalazło {len(analysis.variants)} wariantów")
        success = saver.save_ai_analysis(analysis, test_url, "Drzwi_AI")

        if success:
            print("[OK] Test zakończony sukcesem!")
        else:
            print("[BŁĄD] Test nie powiódł się")
    else:
        print("[BŁĄD] AI nie wykryło żadnych wariantów")

if __name__ == "__main__":
    test_ai_variant_saver()
