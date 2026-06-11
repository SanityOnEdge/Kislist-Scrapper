#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Próbka: skrapowanie dwóch produktów z lazienkarium.pl (umywalki)
Uruchomienie:
  python /mnt/RZECZY/KislistScraper_Pro/sample_scrape_lazienkarium.py \
    --output "/mnt/RZECZY/Produkty_z_Kislist"
"""
import argparse
from pathlib import Path
from selenium_variant_scraper import SeleniumVariantScraper

URLS = [
    "https://lazienkarium.pl/p/kolo-rekord-umywalka-wiszaca-65x49-cm-z-otworem-na-baterie-z-przelewem-biala-k91165000",
    "https://lazienkarium.pl/p/geberit-selnova-umywalka-wiszaca-50x42-cm-z-otworem-na-baterie-z-przelewem-biala-500-310-01-7",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='/mnt/RZECZY/Produkty_z_Kislist')
    args = ap.parse_args()

    out_root = Path(args.output)
    ptype = 'umywalka'

    scraper = SeleniumVariantScraper(headless=True, ai_image_detection=True)

    for i, url in enumerate(URLS, 1):
        folder = out_root / ptype / f"{i:03d}_TEST_Umywalka_{i}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{i}] {url} -> {folder}")
        try:
            scraper.scrape_universal_variants(url, f"{i:03d}_TEST_Umywalka_{i}", str(folder), ptype)
        except Exception as e:
            print(f"Błąd: {e}")

    print(f"\nGotowe. Sprawdź: {out_root / ptype}")


if __name__ == '__main__':
    main()
