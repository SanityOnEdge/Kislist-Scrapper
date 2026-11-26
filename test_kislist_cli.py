#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless CLI runner for KislistScraper.
- Fetches products from a Kislist list URL (parsing window.sections)
- Picks first N products with supplier URLs
- Runs SeleniumVariantScraper in headless mode to save variant images
- Saves into: output_dir/typ_produktu/NNN_nazwa/kolor/obrazki
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
import requests

from utils import sanitize_filename
from selenium_variant_scraper import SeleniumVariantScraper

PRODUCER_DOMAINS = [
    'porta.com.pl', 'dekordia.pl', 'domni.pl', 'lazienkarium.pl',
    'cersanit', 'grohe', 'paradyz'
]

PRODUCT_TYPES = {
    'drzwi': ['door', 'drzwi', 'porta', 'verte'],
    'płytki_ceramiczne': ['płytka', 'ceramic', 'tile', 'paradyż', 'paradyz', 'tubądzin', 'tubadzin', 'opoczno'],
    'listwy_przypodłogowe': ['listwa', 'przypodłogowa', 'baseboards', 'skirting', 'listwy'],
    'miska_wc': ['miska', 'wc', 'toilet', 'bowl', 'kompakt', 'stelaż', 'sedes', 'kompaktowa'],
    'umywalka': ['umywalka', 'basin', 'sink', 'washbasin', 'lavatory'],
    'bateria_umywalkowa': ['bateria', 'kran', 'faucet', 'tap', 'mixer', 'umywalkowa'],
    'wanna': ['wanna', 'bathtub', 'bath', 'akrylowa', 'stalowa'],
    'kabina_prysznicowa': ['kabina', 'prysznicowa', 'shower', 'cabin', 'enclosure'],
    'brodzik': ['brodzik', 'shower', 'tray', 'base', 'akrylowy'],
    'zestaw_prysznicowy': ['zestaw', 'prysznicowy', 'shower', 'set', 'deszczownica'],
    'tapeta': ['tapeta', 'wallpaper', 'fototapeta', 'wall', 'covering'],
    'stelaż': ['stelaż', 'frame', 'mounting', 'podtynkowy', 'installation']
}

SECTION_TYPE_MAP = [
    ('drzwi', 'drzwi'),
    ('listwy', 'listwy_przypodłogowe'),
    ('listwa', 'listwy_przypodłogowe'),
    ('płytki', 'płytki_ceramiczne'),
    ('plytki', 'płytki_ceramiczne'),
    ('miska', 'miska_wc'),
    ('wc', 'miska_wc'),
    ('umywal', 'umywalka'),
    ('wanna', 'wanna'),
    ('bateria', 'bateria_umywalkowa'),
    ('kabina', 'kabina_prysznicowa'),
    ('prysznic', 'kabina_prysznicowa'),
    ('brodzik', 'brodzik'),
    ('zestaw prysznicowy', 'zestaw_prysznicowy'),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}


def detect_product_type(product_name: str, product_url: str = '', section_name: str = '') -> str:
    s = (section_name or '').lower()
    for key, mapped in SECTION_TYPE_MAP:
        if key in s:
            return mapped

    text = f"{product_name} {product_url}".lower()
    for ptype, keywords in PRODUCT_TYPES.items():
        for kw in keywords:
            if kw.lower() in text:
                return ptype
    return 'produkty_inne'


def extract_sections(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    m = re.search(r'window\.sections\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
    if not m:
        return []
    return json.loads(m.group(1))


def collect_products(kislist_url: str, limit: int):
    sections = extract_sections(kislist_url)
    products = []
    for section in sections:
        sec_name = section.get('name', 'bez_nazwy')
        for idx, item in enumerate(section.get('items', []), 1):
            name = item.get('collection') or f"produkt_{idx:03d}"
            purl = item.get('url') or ''
            if not purl:
                continue
            products.append({'section': sec_name, 'name': name, 'url': purl})
            if len(products) >= limit:
                return products
    return products[:limit]


def main():
    base = Path(__file__).resolve().parent
    default_out = base / 'output' / 'Produkty_z_Kislist'

    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True, help='Kislist list-preview URL')
    ap.add_argument('--limit', type=int, default=2, help='Number of products to test (max collected this run)')
    ap.add_argument('--output', default=str(default_out), help='Main output folder')
    ap.add_argument('--batch', type=int, default=50, help='Batch size per run')
    ap.add_argument('--state', default=str(base / '.kislist_state.json'), help='Checkpoint state file')
    ap.add_argument('--auto', action='store_true', help='Process all batches automatically in a single run')
    ap.add_argument('--log', help=f'Path to JSONL log file; defaults to {default_out}')
    args = ap.parse_args()

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    if args.log:
        log_path = Path(args.log)
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = out_root / f'log_{ts}.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def write_log(event: dict):
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        except Exception:
            pass

    write_log({
        'event': 'start',
        'url': args.url,
        'limit': args.limit,
        'batch': args.batch,
        'output': str(out_root),
        'state': args.state,
        'auto': args.auto,
        'ts': datetime.now().isoformat()
    })

    products = collect_products(args.url, args.limit)
    if not products:
        print('[BŁĄD] Nie znaleziono produktów w liście')
        write_log({'event': 'no_products', 'ts': datetime.now().isoformat()})
        return 2

    state_path = Path(args.state)
    start_index = 0
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text())
            if data.get('url') == args.url:
                start_index = int(data.get('last_index', 0))
        except Exception:
            start_index = 0

    scraper = SeleniumVariantScraper(headless=True, ai_image_detection=True)

    def process_range(s_idx: int, e_idx: int):
        batch_products = products[s_idx:e_idx]
        print(f'[INFO] Batch: {len(batch_products)} produktów ({s_idx+1}-{e_idx} z {len(products)})')
        write_log({'event': 'batch_start', 'from': s_idx + 1, 'to': e_idx, 'total': len(products), 'ts': datetime.now().isoformat()})
        for idx, p in enumerate(batch_products, start=s_idx + 1):
            ptype = detect_product_type(p['name'], p['url'], p.get('section', ''))
            clean_name = sanitize_filename(p['name'])
            product_folder = out_root / ptype / f"{idx:03d}_{clean_name}"
            product_folder.mkdir(parents=True, exist_ok=True)

            print(f"\n[{idx}] {p['name']} ({ptype}) -> {p['url']}")
            write_log({'event': 'product_start', 'idx': idx, 'name': p['name'], 'ptype': ptype, 'url': p['url'], 'folder': str(product_folder), 'ts': datetime.now().isoformat()})
            try:
                scraper.scrape_universal_variants(p['url'], f"{idx:03d}_{clean_name}", str(product_folder), ptype)
                write_log({'event': 'product_done', 'idx': idx, 'status': 'ok', 'ts': datetime.now().isoformat()})
            except Exception as e:
                print(f"[BŁĄD] Błąd produktu {idx}: {e}")
                write_log({'event': 'product_done', 'idx': idx, 'status': 'error', 'error': str(e), 'ts': datetime.now().isoformat()})

    def save_checkpoint(end_index: int):
        try:
            state = {
                'url': args.url,
                'last_index': end_index if end_index < len(products) else 0,
                'total': len(products)
            }
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            print(f"\n[INFO] Zapisano checkpoint: {state_path} -> last_index={state['last_index']}")
            write_log({'event': 'checkpoint', 'last_index': state['last_index'], 'ts': datetime.now().isoformat()})
        except Exception as e:
            print(f"[OSTRZEŻENIE] Nie można zapisać checkpointu: {e}")
            write_log({'event': 'checkpoint_error', 'error': str(e), 'ts': datetime.now().isoformat()})

    if args.auto:
        while start_index < len(products):
            end_index = min(start_index + args.batch, len(products))
            process_range(start_index, end_index)
            start_index = end_index
            save_checkpoint(end_index)
        print(f"\n[OK] Wszystkie batche zakończone. Sprawdź: {out_root}")
        write_log({'event': 'done', 'ts': datetime.now().isoformat()})
        return 0

    end_index = min(start_index + args.batch, len(products))
    process_range(start_index, end_index)
    save_checkpoint(end_index)
    print(f"\n[OK] Batch zakończony. Sprawdź: {out_root}")
    write_log({'event': 'done_batch', 'ts': datetime.now().isoformat()})
    return 0


if __name__ == '__main__':
    sys.exit(main())
