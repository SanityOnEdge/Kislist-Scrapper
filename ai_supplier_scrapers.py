#!/usr/bin/env python3
# ai_supplier_scrapers.py
from typing import List, Optional
import os
from variant_detector_simple import ProductVariant
from ai_scraper import AIWebScraper, AIProductVariant
from utils import sanitize_filename, extract_domain

class BaseAIScraper:
    """Klasa bazowa dla scraperów wykorzystujących AI."""
    
    def __init__(self, session, ai_provider="ollama", model="llama3.2:latest", api_key=None):
        self.session = session
        self.ai_scraper = AIWebScraper(
            ai_provider=ai_provider,
            model=model,
            api_key=api_key
        )

    def _resolve_raw_name(self, ai_variant: AIProductVariant) -> Optional[str]:
        return ai_variant.color or ai_variant.name

    def _clean_folder_name(self, name: str) -> Optional[str]:
        if not name:
            return None
        clean = sanitize_filename(name)
        if len(clean) < 2 or clean.lower() in {'default', 'none', 'null', 'undefined', 'unknown'}:
            return None
        return clean.title()

    def scrape_product(self, url: str) -> List[ProductVariant]:
        print(f"🧠 {self.__class__.__name__} analizuje: {url}")
        try:
            ai_analysis = self.ai_scraper.analyze_product_page(url)
            if not ai_analysis:
                return []

            variants = []
            for ai_variant in ai_analysis.variants:
                folder_name = self._clean_folder_name(self._resolve_raw_name(ai_variant))
                if folder_name and ai_variant.images:
                    variants.append(ProductVariant(
                        color=folder_name,
                        images=ai_variant.images,
                        url=url
                    ))
            return variants
        except Exception as e:
            print(f"❌ Błąd {self.__class__.__name__}: {e}")
            return []

class AIPortaScraper(BaseAIScraper):
    """Scraper AI dedykowany dla porta.com.pl."""
    pass

class AIUniversalScraper(BaseAIScraper):
    """Uniwersalny scraper AI uwzględniający również materiał produktu."""
    def _resolve_raw_name(self, ai_variant: AIProductVariant) -> Optional[str]:
        return ai_variant.color or ai_variant.material or ai_variant.name

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
