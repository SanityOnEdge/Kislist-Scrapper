#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Product Variant Detector
Podstawowy moduł do wykrywania wariantów produktów
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ProductVariant:
    """Reprezentuje wariant produktu kompatybilny ze wszystkimi scraperami."""
    name: str = ""
    color: str = ""
    size: str = ""
    material: str = ""
    image_url: str = ""
    images: List[str] = field(default_factory=list)
    url: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.name and self.color:
            self.name = self.color
        if self.image_url and not self.images:
            self.images = [self.image_url]

    def __str__(self):
        return f"Variant({self.name or self.color}, images={len(self.images)})"


class SimpleVariantDetector:
    """Prosty detektor wariantów produktów."""

    color_mapping = {
        'biały': 'white', 'bialy': 'white', 'biała': 'white', 'white': 'white',
        'czarny': 'black', 'black': 'black', 'grafit': 'graphite', 'graphite': 'graphite',
        'szary': 'grey', 'gray': 'grey', 'grey': 'grey',
        'brązowy': 'brown', 'brazowy': 'brown', 'brown': 'brown',
        'beżowy': 'beige', 'bezowy': 'beige', 'beż': 'beige', 'beige': 'beige',
        'kremowy': 'cream', 'cream': 'cream',
        'dąb': 'oak', 'dab': 'oak', 'oak': 'oak',
        'sosna': 'pine', 'pine': 'pine',
        'buk': 'beech', 'beech': 'beech',
        'orzech': 'walnut', 'walnut': 'walnut',
        'wenge': 'wenge'
    }

    COMMON_COLORS = list(color_mapping.keys())
    COMMON_SIZES = [
        '60', '70', '80', '90', '100', '120', '140', '160', '180', '200',
        '60cm', '70cm', '80cm', '90cm', '100cm', '120cm', '140cm', '160cm'
    ]

    def __init__(self):
        self.color_pattern = re.compile(r'\b(' + '|'.join(self.COMMON_COLORS) + r')\b', re.IGNORECASE)
        self.size_pattern = re.compile(r'\b(' + '|'.join(self.COMMON_SIZES) + r')\b', re.IGNORECASE)

    def _normalize_color(self, text: str) -> str:
        """Normalizuje nazwę koloru z tekstu do ujednoliconej nazwy."""
        if not text:
            return "default"
        text_low = text.lower()
        for pl_color, norm_color in self.color_mapping.items():
            if pl_color in text_low:
                return norm_color
        return "default"

    def _is_valid_product_image(self, src: str) -> bool:
        """Sprawdza, czy URL wskazuje na prawidłowy obraz produktu, a nie ikonę/logo."""
        if not src or len(src) < 5:
            return False
        src_low = src.lower()
        excluded = ['logo', 'icon', 'sprite', 'banner', 'pixel', 'placeholder', 'avatar', 'loader']
        if any(bad in src_low for bad in excluded):
            return False
        return any(ext in src_low for ext in ['.jpg', '.jpeg', '.png', '.webp'])

    def detect_variants_from_text(self, text: str) -> List[ProductVariant]:
        variants = []
        for line in text.split('\n'):
            line = line.strip()
            if line and self._looks_like_variant(line):
                variant = self._parse_variant(line)
                if variant:
                    variants.append(variant)
        return variants

    def _looks_like_variant(self, text: str) -> bool:
        return bool(self.color_pattern.search(text) or self.size_pattern.search(text))

    def _parse_variant(self, text: str) -> Optional[ProductVariant]:
        color_match = self.color_pattern.search(text)
        size_match = self.size_pattern.search(text)
        return ProductVariant(
            name=text.strip(),
            color=color_match.group(1) if color_match else "",
            size=size_match.group(1) if size_match else "",
            description=text
        )


class UniversalVariantDetector(SimpleVariantDetector):
    """Uniwersalny detektor wariantów używany jako baza i fallback."""

    def scrape_product(self, url: str) -> List[ProductVariant]:
        return []

    def detect_variants(self, url: str) -> List[ProductVariant]:
        return []


def detect_variants(text: str) -> List[ProductVariant]:
    detector = SimpleVariantDetector()
    return detector.detect_variants_from_text(text)
