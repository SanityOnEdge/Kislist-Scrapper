#!/usr/bin/env python3
"""
AI-Powered Web Scraper - Bardeen Style
Używa AI do inteligentnego rozpoznawania zawartości stron zamiast twardej logiki
"""

import requests
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass
class AIProductVariant:
    name: str
    color: str
    material: str
    description: str
    images: List[str]
    confidence: float
    ai_reasoning: str

@dataclass
class AIProductAnalysis:
    product_name: str
    variants: List[AIProductVariant]
    main_images: List[str]
    product_type: str
    ai_confidence: float
    reasoning: str

class AIWebScraper:
    def __init__(self, ai_provider="ollama", model="llama3.2:latest", api_key=None):
        self.ai_provider = ai_provider
        self.model = model
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def analyze_product_page(self, url: str) -> Optional[AIProductAnalysis]:
        print(f"[INFO] AI analizuje stronę: {url}")

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            page_data = self._extract_page_data(response.text, url)
            ai_analysis = self._ask_ai_to_analyze(page_data, url)

            if ai_analysis:
                print(f"[OK] AI wykryło: {ai_analysis.product_name} z {len(ai_analysis.variants)} wariantami")
                return ai_analysis
            else:
                print("[BŁĄD] AI nie mogło przeanalizować strony")
                return None

        except Exception as e:
            print(f"[BŁĄD] Błąd analizy AI: {e}")
            return None

    def _extract_page_data(self, html_content: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        title = soup.find('title')
        h1_tags = soup.find_all('h1')
        img_tags = soup.find_all('img')

        product_images = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and any(keyword in src.lower() for keyword in ['product', 'phavi', 'upload', 'media']):
                if src.startswith('http') or src.startswith('//'):
                    product_images.append(src)
                elif src.startswith('/'):
                    product_images.append(f"{url.split('/')[0]}//{url.split('/')[2]}{src}")

        main_content = []
        for div in soup.find_all(['div', 'section', 'article']):
            text = div.get_text(strip=True)
            if 50 < len(text) < 500:
                main_content.append(text)

        variant_elements = []
        for elem in soup.find_all(['button', 'a', 'span', 'div']):
            classes = ' '.join(elem.get('class', []))
            text = elem.get_text(strip=True)

            if any(keyword in classes.lower() for keyword in ['color', 'variant', 'option', 'swatch']) or \
               any(keyword in text.lower() for keyword in ['biały', 'czarny', 'brązowy', 'szary', 'naturalne', 'laminat', 'okleina']):
                variant_elements.append({
                    'text': text,
                    'classes': classes,
                    'tag': elem.name
                })

        return {
            'url': url,
            'title': title.get_text() if title else '',
            'headings': [h.get_text(strip=True) for h in h1_tags],
            'images': product_images[:15],
            'content_snippets': main_content[:10],
            'variant_elements': variant_elements[:20],
            'domain': url.split('/')[2]
        }

    def _ask_ai_to_analyze(self, page_data: Dict[str, Any], url: str) -> Optional[AIProductAnalysis]:
        prompt = self._create_analysis_prompt(page_data)

        try:
            if self.ai_provider == "ollama":
                return self._query_ollama(prompt, page_data)
            elif self.ai_provider == "openai":
                return self._query_openai(prompt, page_data)
            else:
                print(f"[BŁĄD] Nieobsługiwany provider AI: {self.ai_provider}")
                return None
        except Exception as e:
            print(f"[BŁĄD] Błąd komunikacji z AI: {e}")
            return None

    def _create_analysis_prompt(self, page_data: Dict[str, Any]) -> str:
        return f"""Analizuj stronę drzwi PORTA DECOR i znajdź WSZYSTKIE warianty kolorów.

TREŚĆ STRONY ZAWIERA:
{chr(10).join(page_data['content_snippets'][:8])}

OBRAZY Z KOLORAMI:
{chr(10).join([f"- {img}" for img in page_data['images'] if 'okleina' in img.lower() or 'dab' in img.lower() or 'buk' in img.lower()])}

Szukaj kolorów takich jak: Dąb Mauvella, Dąb Skandynawski, Dąb Syberyjski, Buk Skandynawski, Dąb Matowy, Dąb Klasyczny, Dąb Naturalny, Dąb Craft Złoty, Dąb Kalifornia, Dąb Hawana, Biały, Szary, Orzech, Wenge White, Sosna Norweska, Akacja Srebrna, Akacja Miodowa, Dąb Szkarłatny, Dąb Ciemny, Fiord, Kaszmir, Oliwka.

Zwróć JSON:
{{
    "product_name": "PORTA DECOR MODEL P",
    "product_type": "drzwi",
    "ai_confidence": 85,
    "reasoning": "Analiza treści i obrazów",
    "variants": [
        {{
            "name": "nazwa_koloru",
            "color": "nazwa_koloru",
            "material": "typ_okleiny",
            "description": "opis",
            "images": ["url_obrazu"],
            "confidence": 90,
            "ai_reasoning": "dlaczego ten obraz pasuje"
        }}
    ]
}}

Znajdź jak najwięcej wariantów z treści."""

    def _query_ollama(self, prompt: str, page_data: Dict[str, Any]) -> Optional[AIProductAnalysis]:
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_ctx": 8192
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                ai_text = result.get('response', '')
                return self._parse_ai_response(ai_text, page_data['url'])
            else:
                print(f"[BŁĄD] Ollama error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print("[BŁĄD] Nie można połączyć z Ollama. Sprawdź czy daemon działa.")
            return None
        except Exception as e:
            print(f"[BŁĄD] Błąd Ollama: {e}")
            return None

    def _query_openai(self, prompt: str, page_data: Dict[str, Any]) -> Optional[AIProductAnalysis]:
        if not self.api_key:
            print("[BŁĄD] Brak klucza API dla OpenAI")
            return None

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model or "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "Jesteś ekspertem od analizy stron produktów budowlanych."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                ai_text = result['choices'][0]['message']['content']
                return self._parse_ai_response(ai_text, page_data['url'])
            else:
                print(f"[BŁĄD] OpenAI error: {response.status_code}")
                return None

        except Exception as e:
            print(f"[BŁĄD] Błąd OpenAI: {e}")
            return None

    def _parse_ai_response(self, ai_text: str, url: str) -> Optional[AIProductAnalysis]:
        try:
            json_start = ai_text.find('{')
            json_end = ai_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                print("[BŁĄD] AI nie zwróciło poprawnego JSON")
                return None

            json_str = ai_text[json_start:json_end]
            data = json.loads(json_str)

            variants = []
            for v_data in data.get('variants', []):
                variant = AIProductVariant(
                    name=v_data.get('name', ''),
                    color=v_data.get('color', ''),
                    material=v_data.get('material', ''),
                    description=v_data.get('description', ''),
                    images=v_data.get('images', []),
                    confidence=float(v_data.get('confidence', 0)),
                    ai_reasoning=v_data.get('ai_reasoning', '')
                )
                variants.append(variant)

            analysis = AIProductAnalysis(
                product_name=data.get('product_name', ''),
                variants=variants,
                main_images=data.get('main_images', []),
                product_type=data.get('product_type', 'inne'),
                ai_confidence=float(data.get('ai_confidence', 0)),
                reasoning=data.get('reasoning', '')
            )

            return analysis

        except json.JSONDecodeError as e:
            print(f"[BŁĄD] Błąd parsowania JSON od AI: {e}")
            return None
        except Exception as e:
            print(f"[BŁĄD] Błąd przetwarzania odpowiedzi AI: {e}")
            return None

if __name__ == "__main__":
    print("[INFO] Test AI Web Scraper")
    ai_scraper = AIWebScraper(ai_provider="ollama", model="llama3.2:latest")
    test_url = "https://www.porta.com.pl/modele-drzwi/minimax"
    result = ai_scraper.analyze_product_page(test_url)
