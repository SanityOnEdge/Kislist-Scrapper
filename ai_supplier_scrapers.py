#!/usr/bin/env python3
"""
AI Supplier Scrapers - integracja AI scrapera z systemem KislistScraper
Zastępuje twardą logikę regex-ową inteligentnym AI
"""

from typing import List
from variant_detector_simple import ProductVariant
from ai_scraper import AIWebScraper, AIProductAnalysis
import os

class AIPortaScraper:
    def __init__(self, session, ai_provider="ollama", model="llama3.2:latest", api_key=None):
        self.session = session
        self.ai_scraper = AIWebScraper(
            ai_provider=ai_provider,
            model=model,
            api_key=api_key
        )

    def scrape_product(self, url: str) -> List[ProductVariant]:
        print(f"[INFO] AI Porta Scraper analizuje: {url}")

        try:
            ai_analysis = self.ai_scraper.analyze_product_page(url)

            if not ai_analysis:
                print(f"   [BŁĄD] AI nie mogło przeanalizować strony")
                return []

            variants = []
            for ai_variant in ai_analysis.variants:
                folder_name = ai_variant.color if ai_variant.color else ai_variant.name
                folder_name = self._clean_folder_name(folder_name)

                if folder_name and ai_variant.images:
                    variant = ProductVariant(
                        color=folder_name,
                        images=ai_variant.images,
                        url=url
                    )
                    variants.append(variant)
                    print(f"   [OK] AI wykryło wariant: {folder_name} ({len(ai_variant.images)} obrazów)")

            if variants:
                print(f"   [OK] AI znalazło {len(variants)} wariantów")

            return variants

        except Exception as e:
            print(f"   [BŁĄD] Błąd AI Porta Scraper: {e}")
            return []

    def _clean_folder_name(self, name: str) -> str:
        if not name:
            return None

        import re
        clean = re.sub(r'[<>:"/\\|?*]', '_', name)
        clean = re.sub(r'\s+', '_', clean)
        clean = clean.strip('_')

        if len(clean) < 2 or clean.lower() in ['default', 'none', 'null', 'undefined']:
            return None

        return clean.title()

class AIUniversalScraper:
    def __init__(self, session, ai_provider="ollama", model="llama3.2:latest", api_key=None):
        self.session = session
        self.ai_scraper = AIWebScraper(
            ai_provider=ai_provider,
            model=model,
            api_key=api_key
        )

    def scrape_product(self, url: str) -> List[ProductVariant]:
        print(f"[INFO] AI Universal Scraper analizuje: {url}")

        try:
            ai_analysis = self.ai_scraper.analyze_product_page(url)

            if not ai_analysis:
                print(f"   [BŁĄD] AI nie mogło przeanalizować strony")
                return []

            variants = []
            for ai_variant in ai_analysis.variants:
                folder_name = ai_variant.color or ai_variant.material or ai_variant.name
                folder_name = self._clean_folder_name(folder_name)

                if folder_name and ai_variant.images:
                    variant = ProductVariant(
                        color=folder_name,
                        images=ai_variant.images,
                        url=url
                    )
                    variants.append(variant)
                    print(f"   [OK] AI wykryło: {folder_name} ({len(ai_variant.images)} obrazów)")

            if variants:
                print(f"   [OK] AI przeanalizowało domenę {url.split('/')[2]}")

            return variants

        except Exception as e:
            print(f"   [BŁĄD] Błąd AI Universal Scraper: {e}")
            return []

    def _clean_folder_name(self, name: str) -> str:
        if not name:
            return None

        import re
        clean = re.sub(r'[<>:"/\\|?*]', '_', name)
        clean = re.sub(r'\s+', '_', clean)
        clean = clean.strip('_')

        if len(clean) < 2:
            return None

        return clean.title()

class AISupplierScraperFactory:
    @staticmethod
    def get_ai_config():
        ai_provider = os.getenv('KISLIST_AI_PROVIDER', 'ollama')
        model = os.getenv('KISLIST_AI_MODEL', 'llama3.2:latest')
        api_key = os.getenv('OPENAI_API_KEY') if ai_provider == 'openai' else None
        return ai_provider, model, api_key

    @staticmethod
    def get_scraper(url: str, session):
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        ai_provider, model, api_key = AISupplierScraperFactory.get_ai_config()

        if 'porta.com.pl' in domain:
            return AIPortaScraper(session, ai_provider, model, api_key)
        else:
            return AIUniversalScraper(session, ai_provider, model, api_key)

    @staticmethod
    def scrape_product_url(url: str, session) -> List[ProductVariant]:
        scraper = AISupplierScraperFactory.get_scraper(url, session)
        return scraper.scrape_product(url)
