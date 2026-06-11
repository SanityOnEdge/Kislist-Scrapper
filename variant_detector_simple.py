#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Product Variant Detector
Podstawowy moduł do wykrywania wariantów produktów
"""

import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ProductVariant:
    """Reprezentuje wariant produktu"""
    name: str
    color: str = ""
    size: str = ""
    material: str = ""
    image_url: str = ""
    description: str = ""
    
    def __str__(self):
        return f"Variant({self.name}, color={self.color})"

class SimpleVariantDetector:
    """Prosty detektor wariantów produktów"""
    
    # Kolory często występujące w nazwach produktów
    COMMON_COLORS = [
        'biały', 'bialy', 'white', 'czarny', 'black', 'szary', 'gray', 'grey',
        'brązowy', 'brazowy', 'brown', 'beż', 'bez', 'beige', 'kremowy', 'cream',
        'czerwony', 'red', 'niebieski', 'blue', 'zielony', 'green', 'żółty', 'yellow',
        'dąb', 'dab', 'oak', 'sosna', 'pine', 'buk', 'beech', 'wenge', 'mahoń', 'mahogany',
        'orzech', 'walnut', 'wiśnia', 'wisnia', 'cherry', 'klon', 'maple'
    ]
    
    # Rozmiary
    COMMON_SIZES = [
        '80', '90', '60', '70', '100', '120', '140', '160', '180', '200',
        '80cm', '90cm', '60cm', '70cm', '100cm', '120cm', '140cm', '160cm'
    ]
    
    def __init__(self):
        self.color_pattern = re.compile(r'\b(' + '|'.join(self.COMMON_COLORS) + r')\b', re.IGNORECASE)
        self.size_pattern = re.compile(r'\b(' + '|'.join(self.COMMON_SIZES) + r')\b', re.IGNORECASE)
    
    def detect_variants_from_text(self, text: str) -> List[ProductVariant]:
        """Wykryj warianty z tekstu"""
        variants = []
        
        # Podziel tekst na linie
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Sprawdź czy linia zawiera potencjalny wariant
            if self._looks_like_variant(line):
                variant = self._parse_variant(line)
                if variant:
                    variants.append(variant)
        
        return variants
    
    def _looks_like_variant(self, text: str) -> bool:
        """Sprawdź czy tekst wygląda jak wariant produktu"""
        # Sprawdź czy zawiera kolor lub rozmiar
        return bool(self.color_pattern.search(text) or self.size_pattern.search(text))
    
    def _parse_variant(self, text: str) -> Optional[ProductVariant]:
        """Parsuj wariant z tekstu"""
        # Wykryj kolor
        color_match = self.color_pattern.search(text)
        color = color_match.group(1) if color_match else ""
        
        # Wykryj rozmiar
        size_match = self.size_pattern.search(text)
        size = size_match.group(1) if size_match else ""
        
        # Nazwa wariantu to cały tekst
        name = text.strip()
        
        return ProductVariant(
            name=name,
            color=color,
            size=size,
            description=text
        )
    
    def extract_color_from_filename(self, filename: str) -> str:
        """Wyciągnij kolor z nazwy pliku"""
        color_match = self.color_pattern.search(filename)
        return color_match.group(1) if color_match else ""
    
    def extract_size_from_text(self, text: str) -> str:
        """Wyciągnij rozmiar z tekstu"""
        size_match = self.size_pattern.search(text)
        return size_match.group(1) if size_match else ""

class UniversalVariantDetector(SimpleVariantDetector):
    """Uniwersalny detektor wariantów - alias dla SimpleVariantDetector"""
    
    def scrape_product(self, url: str) -> List[ProductVariant]:
        """Fallback metoda dla kompatybilności z SupplierScraperFactory"""
        # Ta klasa jest używana jako fallback, więc zwróć pustą listę
        return []

# Dla kompatybilności z starszym kodem
def detect_variants(text: str) -> List[ProductVariant]:
    """Funkcja pomocnicza do wykrywania wariantów"""
    detector = SimpleVariantDetector()
    return detector.detect_variants_from_text(text)
