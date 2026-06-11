#!/usr/bin/env python3
"""
Specjalizowane moduły scrapingu dla konkretnych dostawców
"""

import re
import json
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from variant_detector_simple import ProductVariant, UniversalVariantDetector

class DekordiaScraper:
    """Specjalizowany scraper dla dekordia.pl"""
    
    def __init__(self, session):
        self.session = session
        self.base_detector = UniversalVariantDetector()
    
    def scrape_product(self, url: str) -> List[ProductVariant]:
        """Scrappuje produkt z dekordia.pl - focus na rzeczywiste warianty"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            page_content = response.text
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            variants = []
            
            # 1. PRIORYTET: Szukaj RZECZYWISTYCH opcji kolorów w selektorach produktu
            color_selector_patterns = [
                r'<select[^>]*(?:name|id)=[\'"][^\'"]*(color|kolor|variant)[^\'"]* [^>]*>.*?</select>',
                r'<div[^>]*class=[\'"][^\'"]*(color|variant)[^\'"]* [^>]*>.*?</div>'
            ]
            
            found_real_variants = False
            for pattern in color_selector_patterns:
                matches = re.findall(pattern, page_content, re.DOTALL | re.IGNORECASE)
                for match_content in matches:
                    options = re.findall(r'<option[^>]*value=[\'"]([^\'"]+)[\'"][^>]*>([^<]+)</option>', match_content)
                    if len(options) > 1:  # Rzeczywiste warianty (więcej niż 1 opcja)
                        found_real_variants = True
                        for value, text in options:  # Wszystkie warianty
                            color = self._normalize_color_dekordia(text)
                            if color != "default":
                                images = self._find_product_images_dekordia(page_content, base_url)
                                variants.append(ProductVariant(
                                    color=color,
                                    images=images[:2],
                                    url=url
                                ))
            
            # 2. FALLBACK: Jeśli nie ma rzeczywistych wariantów, użyj głównego koloru produktu
            if not found_real_variants:
                title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page_content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1)
                    main_color = self.base_detector._normalize_color(title)
                    if main_color != "default":
                        images = self._find_product_images_dekordia(page_content, base_url)
                        variants.append(ProductVariant(
                            color=main_color,
                            images=images[:3],
                            url=url
                        ))
            
            return self._remove_duplicates(variants)
            
        except Exception as e:
            print(f"   ❌ Błąd dekordia.pl: {str(e)[:30]}...")
            return []
    
    def _normalize_color_dekordia(self, color_text: str) -> str:
        """Normalizuje kolory specyficzne dla dekordia.pl"""
        color_lower = color_text.lower()
        
        # Mapowanie specyficzne dla dekordia
        dekordia_colors = {
            'biała': 'white', 'białe': 'white', 'biały': 'white',
            'dąb': 'oak', 'dąb sonoma': 'oak_sonoma',
            'sosna': 'pine', 'sosna bielona': 'pine_whitened'
        }
        
        for polish, english in dekordia_colors.items():
            if polish in color_lower:
                return english
        
        return self.base_detector._normalize_color(color_text)
    
    def _find_product_images_dekordia(self, page_content: str, base_url: str) -> List[str]:
        """Znajduje obrazy produktu na dekordia.pl"""
        images = []
        
        # Wzorce specyficzne dla dekordia
        patterns = [
            r'<img[^>]+src=[\'"]([^\'\"]*product[^\'"]*)[\'"][^>]*>',
            r'data-zoom-image=[\'"]([^\'"]+)[\'"]',
            r'<img[^>]+class=[\'"][^\'\"]*product[^\'\"]*[\'"][^>]*src=[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for src in matches:
                if self.base_detector._is_valid_product_image(src):
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images[:5]
    
    def _remove_duplicates(self, variants: List[ProductVariant]) -> List[ProductVariant]:
        """Usuwa duplikaty wariantów"""
        seen = set()
        unique = []
        for variant in variants:
            if variant.color not in seen:
                seen.add(variant.color)
                unique.append(variant)
        return unique

class DomniScraper:
    """Specjalizowany scraper dla domni.pl"""
    
    def __init__(self, session):
        self.session = session
        self.base_detector = UniversalVariantDetector()
    
    def scrape_product(self, url: str) -> List[ProductVariant]:
        """Scrappuje produkt z domni.pl"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            page_content = response.text
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            variants = []
            
            # 1. Szukaj wariantów w JavaScript
            js_patterns = [
                r'productVariants\s*:\s*(\[.*?\])',
                r'colors\s*:\s*(\[.*?\])',
                r'window\.product\s*=\s*(\{.*?variants.*?\})'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, page_content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        data = json.loads(match)
                        variants.extend(self._parse_domni_variants(data, base_url))
                    except json.JSONDecodeError:
                        continue
            
            # 2. Szukaj w nazwie produktu
            title_pattern = r'<h1[^>]*class=[\'"][^\'\"]*product[^\'\"]*[\'"][^>]*>([^<]+)</h1>'
            title_match = re.search(title_pattern, page_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
                color = self.base_detector._normalize_color(title)
                if color != "default":
                    images = self._find_product_images_domni(page_content, base_url)
                    variants.append(ProductVariant(
                        color=color,
                        images=images[:3]
                    ))
            
            # 3. Szukaj w galerii obrazów
            gallery_variants = self._extract_gallery_variants(page_content, base_url)
            variants.extend(gallery_variants)
            
            return self._remove_duplicates(variants)
            
        except Exception as e:
            print(f"   ❌ Błąd domni.pl: {str(e)[:30]}...")
            return []
    
    def _parse_domni_variants(self, data, base_url: str) -> List[ProductVariant]:
        """Parsuje warianty z JSON domni.pl"""
        variants = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get('name') or item.get('color') or item.get('title')
                    if name:
                        color = self.base_detector._normalize_color(name)
                        images = []
                        
                        # Szukaj obrazów w różnych polach
                        for field in ['image', 'images', 'src', 'photo']:
                            if field in item:
                                img_data = item[field]
                                if isinstance(img_data, str):
                                    images.append(urljoin(base_url, img_data))
                                elif isinstance(img_data, list):
                                    images.extend([urljoin(base_url, img) for img in img_data if isinstance(img, str)])
                        
                        if color != "default":
                            variants.append(ProductVariant(color=color, images=images))
        
        return variants
    
    def _extract_gallery_variants(self, page_content: str, base_url: str) -> List[ProductVariant]:
        """Ekstraktuje warianty z galerii obrazów"""
        variants = []
        
        # Szukaj obrazów z nazwami kolorów w alt lub title
        img_pattern = r'<img[^>]+(?:alt|title)=[\'"]([^\'\"]*(?:biały|czarny|szary|brązowy|beżowy|graphite)[^\'"]*)[\'"][^>]*src=[\'"]([^\'"]+)[\'"]'
        matches = re.findall(img_pattern, page_content, re.IGNORECASE)
        
        for alt_text, src in matches:
            color = self.base_detector._normalize_color(alt_text)
            if color != "default" and self.base_detector._is_valid_product_image(src):
                full_url = urljoin(base_url, src)
                variants.append(ProductVariant(
                    color=color,
                    images=[full_url]
                ))
        
        return variants
    
    def _find_product_images_domni(self, page_content: str, base_url: str) -> List[str]:
        """Znajduje obrazy produktu na domni.pl"""
        images = []
        
        # Wzorce specyficzne dla domni
        patterns = [
            r'data-zoom=[\'"]([^\'"]+)[\'"]',
            r'<img[^>]+class=[\'"][^\'\"]*gallery[^\'\"]*[\'"][^>]*src=[\'"]([^\'"]+)[\'"]',
            r'media\.domni\.pl/[^\'\"]+\.(?:jpg|jpeg|png|webp)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for src in matches:
                if self.base_detector._is_valid_product_image(src):
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images[:5]
    
    def _remove_duplicates(self, variants: List[ProductVariant]) -> List[ProductVariant]:
        """Usuwa duplikaty wariantów"""
        seen = set()
        unique = []
        for variant in variants:
            if variant.color not in seen:
                seen.add(variant.color)
                unique.append(variant)
        return unique

class LazienkariumpScraper:
    """Specjalizowany scraper dla lazienkarium.pl"""
    
    def __init__(self, session):
        self.session = session
        self.base_detector = UniversalVariantDetector()
    
    def scrape_product(self, url: str) -> List[ProductVariant]:
        """Scrappuje produkt z lazienkarium.pl"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            page_content = response.text
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            variants = []
            
            # 1. Szukaj w selektorach kolorów
            color_selector_pattern = r'<select[^>]*name=[\'"][^\'\"]*color[^\'\"]*[\'"][^>]*>.*?</select>'
            selector_match = re.search(color_selector_pattern, page_content, re.DOTALL | re.IGNORECASE)
            
            if selector_match:
                options = re.findall(r'<option[^>]*value=[\'"]([^\'"]+)[\'"][^>]*>([^<]+)</option>', selector_match.group(0))
                for value, text in options:
                    color = self.base_detector._normalize_color(text)
                    if color != "default":
                        images = self._find_product_images_lazienkarium(page_content, base_url)
                        variants.append(ProductVariant(
                            color=color,
                            images=images[:2]
                        ))
            
            # 2. Szukaj w głównym opisie
            title_pattern = r'<h1[^>]*>([^<]+)</h1>'
            title_match = re.search(title_pattern, page_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
                color = self.base_detector._normalize_color(title)
                if color != "default":
                    images = self._find_product_images_lazienkarium(page_content, base_url)
                    variants.append(ProductVariant(
                        color=color,
                        images=images[:3]
                    ))
            
            # 3. Fallback - wykryj z tekstu strony
            if not variants:
                text_content = re.sub(r'<[^>]+>', ' ', page_content).lower()
                for polish_color, english_color in self.base_detector.color_mapping.items():
                    if polish_color in text_content:
                        images = self._find_product_images_lazienkarium(page_content, base_url)
                        variants.append(ProductVariant(
                            color=english_color,
                            images=images[:2]
                        ))
                        break  # Tylko pierwszy znaleziony kolor
            
            return self._remove_duplicates(variants)
            
        except Exception as e:
            print(f"   ❌ Błąd lazienkarium.pl: {str(e)[:30]}...")
            return []
    
    def _find_product_images_lazienkarium(self, page_content: str, base_url: str) -> List[str]:
        """Znajduje obrazy produktu na lazienkarium.pl"""
        images = []
        
        # Wzorce specyficzne dla lazienkarium
        patterns = [
            r'cdn\.lazienkarium\.pl/[^\'\"]+\.(?:jpg|jpeg|png|webp)',
            r'<img[^>]+class=[\'"][^\'\"]*product[^\'\"]*[\'"][^>]*src=[\'"]([^\'"]+)[\'"]',
            r'data-large=[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for src in matches:
                if self.base_detector._is_valid_product_image(src) and 'thumbnail' not in src.lower():
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images[:5]
    
    def _remove_duplicates(self, variants: List[ProductVariant]) -> List[ProductVariant]:
        """Usuwa duplikaty wariantów"""
        seen = set()
        unique = []
        for variant in variants:
            if variant.color not in seen:
                seen.add(variant.color)
                unique.append(variant)
        return unique

class PortaScraper:
    """Specjalizowany scraper dla porta.com.pl - radzi sobie z JS-dependent wariantami"""
    
    def __init__(self, session):
        self.session = session
        self.base_detector = UniversalVariantDetector()
    
    def scrape_product(self, url: str) -> List[ProductVariant]:
        """Scrappuje produkt z porta.com.pl - wykrywa rzeczywiste warianty wykończenia"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            page_content = response.text
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            variants = []
            
            # STRATEGIA 1: Szukaj rzeczywistych wariantów wykończenia (okleina, laminat, etc.)
            variants.extend(self._find_finish_variants(page_content, base_url, url))
            
            # STRATEGIA 2: Szukaj w selektorach/przyciskach wariantów
            if not variants:
                variants.extend(self._find_variant_selectors(page_content, base_url, url))
            
            # STRATEGIA 3: Szukaj w galerii z opisami
            if not variants:
                variants.extend(self._find_gallery_variants(page_content, base_url, url))
            
            # STRATEGIA 4: Fallback - jeden wariant z modelem produktu
            if not variants:
                variants.extend(self._find_single_model_variant(page_content, base_url, url))
            
            # Usuń duplikaty
            unique_variants = self._remove_duplicates(variants)
            return unique_variants  # Wszystkie warianty bez limitu
                
        except Exception as e:
            print(f"   ❌ Błąd porta.com.pl: {str(e)[:30]}...")
            return []
    
    def _find_main_product_image(self, page_content: str, base_url: str) -> Optional[str]:
        """Znajduje najlepszy obraz głównego produktu (nie dodatków)"""
        
        # Znajdź wszystkie obrazy
        img_patterns = [
            r'<img[^>]+src=[\'"]([^\'"]+)[\'"][^>]*>',
            r'data-src=[\'"]([^\'"]+)[\'"]'
        ]
        
        all_images = []
        for pattern in img_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for src in matches:
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    full_url = urljoin(base_url, src)
                    all_images.append(full_url)
        
        # INTELIGENTNE FILTROWANIE: Znajdź główny produkt
        
        # 1. Odfiltruj oczywiste nie-produkty
        exclude_keywords = [
            'logo', 'icon', 'banner', 'menu', 'footer', 'social', 'header',
            'klamka', 'klamki', 'handle', 'akcesori', 'dodatki', 'accessory'
        ]
        
        product_candidates = []
        for img in all_images:
            is_main_product = True
            for keyword in exclude_keywords:
                if keyword in img.lower():
                    is_main_product = False
                    break
            if is_main_product:
                product_candidates.append(img)
        
        # 2. Preferuj większe obrazy (zawierają wymiary w URL)
        size_priority = []
        for img in product_candidates:
            # Szukaj wymiarów w URL (np. r,612,1312)
            size_match = re.search(r'r,(\d+),(\d+)', img)
            if size_match:
                width, height = int(size_match.group(1)), int(size_match.group(2))
                size_score = width * height
                size_priority.append((size_score, img))
            else:
                size_priority.append((0, img))
        
        # 3. Sortuj wedlug rozmiaru (największe pierwsze)
        size_priority.sort(reverse=True)
        
        # 4. Zwróć najlepszy (największy) obraz produktu
        if size_priority:
            return size_priority[0][1]
        
        return None
    
    def _find_finish_variants(self, page_content: str, base_url: str, url: str) -> List[ProductVariant]:
        """Szuka rzeczywistych wariantów na podstawie analizy nazw obrazów"""
        variants = []
        
        # Pobierz wszystkie obrazy
        all_images = self._find_product_images_porta(page_content, base_url)
        
        if not all_images:
            return variants
        
        # Analiza nazw obrazów żeby wykryć warianty kolorystyczne
        color_variants = self._analyze_image_names_for_colors(all_images)
        
        if color_variants:
            print(f"   🎨 Wykryto warianty z nazw obrazów: {list(color_variants.keys())}")
            
            for color, images in color_variants.items():
                if len(images) > 0:
                    variants.append(ProductVariant(
                        color=color,
                        images=images[:15],  # Do 15 obrazów na wariant
                        url=url
                    ))
        
        return variants
    
    def _find_variant_selectors(self, page_content: str, base_url: str, url: str) -> List[ProductVariant]:
        """Szuka w selektorach/przyciskach wariantów"""
        variants = []
        
        # Szukaj selektorów z opcjami
        selector_patterns = [
            r'<select[^>]*(?:name|id)=[\'"][^\'"]*(?:variant|finish|color|material)[^\'"]*[\'"][^>]*>(.*?)</select>',
            r'<div[^>]*class=[\'"][^\'"]*(?:variant|finish|selector)[^\'"]*[\'"][^>]*>(.*?)</div>'
        ]
        
        for pattern in selector_patterns:
            selector_matches = re.findall(pattern, page_content, re.DOTALL | re.IGNORECASE)
            for selector_content in selector_matches:
                # Wyciągnij opcje z selektora
                option_matches = re.findall(r'<option[^>]*value=[\'"]([^\'"]+)[\'"][^>]*>([^<]+)</option>', selector_content)
                for value, text in option_matches:
                    if len(text.strip()) > 2 and 'wybierz' not in text.lower():
                        finish_name = self._clean_finish_name(text)
                        if finish_name:
                            images = self._find_product_images_porta(page_content, base_url)
                            if images:
                                variants.append(ProductVariant(
                                    color=finish_name,
                                    images=images[:10],  # Zwiększ limit
                                    url=url
                                ))
        
        return variants
    
    def _find_gallery_variants(self, page_content: str, base_url: str, url: str) -> List[ProductVariant]:
        """Szuka wariantów w galerii obrazów z opisami"""
        variants = []
        
        # Szukaj obrazów z alt/title zawierającymi nazwy wykończeń
        img_patterns = [
            r'<img[^>]+(?:alt|title)=[\'"]([^\'"]*(?:okleina|laminat|lakier|portaperfect|3D|dąb|orzech)[^\'"]*)[\'"][^>]*src=[\'"]([^\'"]+)[\'"]',
            r'<img[^>]*src=[\'"]([^\'"]+)[\'"][^>]*(?:alt|title)=[\'"]([^\'"]*(?:okleina|laminat|lakier)[^\'"]*)[\'"]'
        ]
        
        for pattern in img_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for match in matches:
                alt_text = match[0] if 'alt' in pattern else match[1]
                src = match[1] if 'alt' in pattern else match[0]
                
                finish_name = self._clean_finish_name(alt_text)
                if finish_name and self.base_detector._is_valid_product_image(src):
                    full_url = urljoin(base_url, src)
                    variants.append(ProductVariant(
                        color=finish_name,
                        images=[full_url],
                        url=url
                    ))
        
        return variants
    
    def _find_single_model_variant(self, page_content: str, base_url: str, url: str) -> List[ProductVariant]:
        """Fallback - wykryj jeden wariant z modelem produktu"""
        # Wykryj model z URL (np. minimax, londyn-p, decor)
        url_path = url.split('/')[-1].split('?')[0]
        model_name = self._extract_model_name(url_path)
        
        # Spróbuj też z tytułu HTML
        if not model_name or model_name == "default":
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page_content, re.IGNORECASE)
            if title_match:
                model_name = self._clean_finish_name(title_match.group(1))
        
        # Ostatni fallback - użyj nazwy z URL
        if not model_name or model_name == "default":
            model_name = url_path.replace('-', '_').replace('_p', '').title()
        
        # Znajdź obrazy produktu
        images = self._find_product_images_porta(page_content, base_url)
        
        if images and model_name:
            return [ProductVariant(
                color=model_name,
                images=images[:15],  # Zwiększ dla fallback
                url=url
            )]
        
        return []
        
        # Znajdź najlepsze obrazy produktu
        images = self._find_product_images_porta(page_content, base_url)
        
        if images:
            return [ProductVariant(
                color=main_color,
                images=images[:3],
                url=url
            )]
        
        return []
    
    def _find_product_images_porta(self, page_content: str, base_url: str) -> List[str]:
        """Znajduje WSZYSTKIE wysokiej jakości obrazy produktu na porta.com.pl"""
        images = set()  # Użyj set żeby unikać duplikatów
        
        # ROZSZERZONE wzorce dla obrazów na Porta - szukaj WSZEDZIE!
        patterns = [
            # Główne obrazy phavi (różne rozmiary)
            r'https://www\.porta\.com\.pl/phavi/[^\s\'">]+\.(?:jpg|jpeg|png|webp)',
            # Obrazy z wymiarami w URL
            r'https://www\.porta\.com\.pl/phavi/ph/r,\d+,\d+/[^\s\'">]+\.(?:jpg|jpeg|png|webp)',
            # Wszystkie obrazy w src
            r'<img[^>]+src=[\'"]([^\'">]*(?:phavi|upload|media|images)[^\'">]*\.(?:jpg|jpeg|png|webp))[\'"]',
            # Data-src (lazy loading)
            r'data-src=[\'"]([^\'">]*(?:phavi|upload)[^\'">]*\.(?:jpg|jpeg|png|webp))[\'"]',
            # Data-zoom (duże obrazy)
            r'data-zoom=[\'"]([^\'">]*\.(?:jpg|jpeg|png|webp))[\'"]',
            # Obrazy w JSON/JavaScript
            r'[\'"]https://www\.porta\.com\.pl/[^\'">]*(?:phavi|upl)[^\'">]*\.(?:jpg|jpeg|png|webp)[\'"]',
            # Ogólne obrazy produktowe
            r'<img[^>]*class=[\'"][^\'"]*(?:product|gallery|thumb)[^\'"]*[\'"][^>]*src=[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for match in matches:
                src = match.strip().strip('"').strip("'")
                
                # Sprawdź czy to prawdziwy obraz produktu
                if (self.base_detector._is_valid_product_image(src) and 
                    'logo' not in src.lower() and 
                    'icon' not in src.lower() and
                    'banner' not in src.lower() and
                    len(src) > 10):
                    
                    full_url = urljoin(base_url, src) if not src.startswith('http') else src
                    images.add(full_url)
        
        # Konwertuj z powrotem na listę
        images_list = list(images)
        
        # Sortuj obrazy według jakości (preferuj większe rozmiary)
        sorted_images = []
        for img in images_list:
            # Szukaj wymiarów w URL (np. r,1400,1400)
            size_match = re.search(r'r,(\d+),(\d+)', img)
            if size_match:
                width, height = int(size_match.group(1)), int(size_match.group(2))
                size_score = width * height
                sorted_images.append((size_score, img))
            elif 'phavi' in img:  # Obrazy phavi mają wysoką jakość
                sorted_images.append((100000, img))
            else:
                sorted_images.append((1, img))
        
        # Sortuj według rozmiaru (największe pierwsze)
        sorted_images.sort(reverse=True)
        
        # Zwracaj maksymalnie 15 najlepszych obrazów
        return [img for _, img in sorted_images[:15]]
    
    def _extract_color_from_porta_name(self, product_name: str) -> str:
        """Wykryj kolor z nazwy produktu Porta (minimax, londyn, wieden, itp.)"""
        name_lower = product_name.lower()
        
        # Mapowanie nazw modelów Porta na kolory (na podstawie znajomości branziy)
        porta_model_colors = {
            'minimax': 'white',      # Minimax to zazwyczaj biały
            'londyn': 'brown',       # Londyn to zazwyczaj brązowy/orzech
            'wieden': 'grey',        # Wieden to zazwyczaj szary
            'decor': 'brown',        # Decor to zazwyczaj brązowy/drewno
            'classic': 'brown',      # Classic to zazwyczaj brązowy
            'modern': 'white',       # Modern to zazwyczaj biały/szary
        }
        
        for model, color in porta_model_colors.items():
            if model in name_lower:
                return color
        
        return "default"
    
    def _clean_finish_name(self, raw_name: str) -> str:
        """Czyści nazwę wykończenia do użycia jako nazwa folderu"""
        if not raw_name or len(raw_name.strip()) < 2:
            return None
            
        # Usuń HTML tagi
        clean = re.sub(r'<[^>]+>', '', raw_name)
        
        # Usuń niepotrzebne znaki i whitespace
        clean = re.sub(r'[^\w\sąćęłńóśźżĄĆĘŁŃÓŚŻŹ-]', '', clean)
        clean = re.sub(r'\s+', '_', clean.strip())
        
        # Usuń popularne "noise words"
        noise_words = ['wybierz', 'select', 'opcja', 'option', 'default', 'podstawowy']
        clean_lower = clean.lower()
        for noise in noise_words:
            if noise in clean_lower:
                return None
        
        # Jeśli za krótka nazwa, odrzuć
        if len(clean) < 3:
            return None
            
        return clean.title()  # Pierwsza litera wielka
    
    def _extract_model_name(self, url_path: str) -> str:
        """Wyciąga nazwę modelu z URL"""
        # Usuń sufiks -p, modele-, itp.
        clean_path = url_path.replace('-p', '').replace('modele-drzwi/', '').replace('model-', '')
        
        # Mapowanie popularnych modeli Porta na lepsze nazwy
        model_names = {
            'minimax': 'MINIMAX_Model_P',
            'londyn': 'LONDYN_Model_P', 
            'wieden': 'WIEDEN_Model_P',
            'decor': 'DECOR_Model_P',
            'classic': 'CLASSIC_Model_P'
        }
        
        clean_lower = clean_path.lower()
        for key, nice_name in model_names.items():
            if key in clean_lower:
                return nice_name
                
        # Fallback - po prostu oczyść nazwę
        return clean_path.replace('-', '_').title()
    
    def _find_variant_images_porta(self, page_content: str, base_url: str, variant_name: str) -> List[str]:
        """Szuka obrazów specyficznych dla danego wariantu"""
        images = []
        
        # Szukaj obrazów z nazwami związanymi z wariantem
        variant_keywords = variant_name.lower().split()
        
        for keyword in variant_keywords:
            if len(keyword) > 2:  # Pomijaj krótkie słowa
                # Szukaj obrazów z keyword w URL lub alt
                pattern = f'<img[^>]*(?:src|alt|title)=[\'"]([^\'"]*{keyword}[^\'"]*)[\'"][^>]*>'
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                
                for match in matches:
                    if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        full_url = urljoin(base_url, match)
                        if full_url not in images and self.base_detector._is_valid_product_image(match):
                            images.append(full_url)
        
        return images[:3]
    
    def _analyze_image_names_for_colors(self, images: List[str]) -> dict:
        """Analizuje nazwy obrazów żeby wykryć warianty kolorystyczne"""
        color_variants = {}
        
        # Mapowanie słów kluczowych na kolory
        color_keywords = {
            'Bialy': ['bialy', 'white', 'bianca', 'blanc', 'weiß'],
            'Czarny': ['czarny', 'black', 'nero', 'schwarz', 'graphite', 'grafit'],
            'Szary': ['szary', 'grey', 'gray', 'grau', 'grigio'],
            'Brazowy': ['brazowy', 'brown', 'braun', 'marrone', 'orzech', 'walnut'],
            'Bezowy': ['bezowy', 'beige', 'beż', 'cream', 'creme'],
            'Jablon': ['jablon', 'apple', 'mela', 'apfel', 'light'],
            'Wenge': ['wenge', 'dark', 'ciemny'],
            'Dab': ['dab', 'oak', 'quercia', 'eiche', 'natural'],
            'Sosna': ['sosna', 'pine', 'pino', 'kiefer']
        }
        
        # Analizuj każdy obraz
        for img_url in images:
            img_name = img_url.lower()
            assigned = False
            
            # Sprawdź każdą kategorię koloru
            for color_name, keywords in color_keywords.items():
                for keyword in keywords:
                    if keyword in img_name:
                        if color_name not in color_variants:
                            color_variants[color_name] = []
                        color_variants[color_name].append(img_url)
                        assigned = True
                        break
                if assigned:
                    break
            
            # Jeśli nie przypisano do żadnego koloru, dodaj do "Rozne"
            if not assigned:
                if 'Rozne' not in color_variants:
                    color_variants['Rozne'] = []
                color_variants['Rozne'].append(img_url)
        
        # Usuń duplikaty w każdej kategorii
        for color in color_variants:
            color_variants[color] = list(set(color_variants[color]))
        
        # Usuń kategorie z małą liczbą obrazów (prawdopodobnie fałszywe)
        filtered_variants = {}
        for color, imgs in color_variants.items():
            if len(imgs) >= 1:  # Minimum 1 obraz na wariant
                filtered_variants[color] = imgs
        
        return filtered_variants
    
    def _extract_color_from_json(self, page_content: str) -> str:
        """Szuka kolorów w danych JSON na stronie"""
        # Wzorce dla JSON z danymi o kolorach
        json_patterns = [
            r'"color"\s*:\s*"([^"]+)"',
            r'"colour"\s*:\s*"([^"]+)"',
            r'"kolor"\s*:\s*"([^"]+)"',
            r'"variant"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            for match in matches:
                color = self.base_detector._normalize_color(match)
                if color != "default":
                    return color
        
        return "default"
    
    def _remove_duplicates(self, variants: List[ProductVariant]) -> List[ProductVariant]:
        """Usuwa duplikaty wariantów"""
        seen = set()
        unique = []
        for variant in variants:
            if variant.color not in seen:
                seen.add(variant.color)
                unique.append(variant)
        return unique

class SupplierScraperFactory:
    """Factory do tworzenia odpowiednich scraperów dla różnych dostawców"""
    
    @staticmethod
    def get_scraper(url: str, session):
        """Zwraca odpowiedni scraper na podstawie URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'dekordia.pl' in domain:
            return DekordiaScraper(session)
        elif 'domni.pl' in domain:
            return DomniScraper(session)
        elif 'lazienkarium.pl' in domain:
            return LazienkariumpScraper(session)
        elif 'porta.com.pl' in domain:
            return PortaScraper(session)
        else:
            # Fallback - uniwersalny detektor
            return UniversalVariantDetector()
    
    @staticmethod
    def scrape_product_url(url: str, session, use_ai_scraper=False) -> List[ProductVariant]:
        """Scrappuje produkt używając odpowiedniego scrapera
        
        Args:
            url: URL produktu do scrapowania
            session: Sesja HTTP
            use_ai_scraper: Czy użyć AI do scrapowania (True) czy tradycyjne metody (False)
        """
        if use_ai_scraper:
            # Użyj AI scrapera
            try:
                from ai_supplier_scrapers import AISupplierScraperFactory
                print(f"🧠 Używam AI scrapera dla: {url}")
                ai_results = AISupplierScraperFactory.scrape_product_url(url, session)
                if ai_results:  # Jeśli AI zwróciło wyniki, użyj ich
                    return ai_results
                else:
                    print("⚠️ AI nie znalazł wariantów, przełączam na tradycyjny scraper")
            except Exception as e:
                print(f"❌ Błąd AI scrapera: {e}")
                print("⚠️ Przełączam na tradycyjny scraper jako fallback")
        
        # Tradycyjny scraper
        scraper = SupplierScraperFactory.get_scraper(url, session)
        
        if hasattr(scraper, 'scrape_product'):
            return scraper.scrape_product(url)
        else:
            # Fallback dla uniwersalnego detektora
            return scraper.detect_variants(url)
