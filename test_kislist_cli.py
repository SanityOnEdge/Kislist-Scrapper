#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless test runner for KislistScraper.
- Fetches products from a Kislist list URL (parsing window.sections)
- Picks first N products with supplier URLs
- Runs SeleniumVariantScraper in headless mode to save variant images
- Saves into: output_dir/typ_produktu/NNN_nazwa/kolor/obrazki
"""

import argparse
import json
import re
import sys
from pathlib import Path
import requests
from datetime import datetime

# Local imports
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

# Mapa typów pochodzących z nazw sekcji w Kislist (priorytetowa)
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


def sanitize_filename(name: str) -> str:
    if not name:
        return 'unknown'
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    for pl, en in replacements.items():
        name = name.replace(pl, en)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('_')
    return name[:100]


def detect_product_type(product_name: str, product_url: str = '', section_name: str = '') -> str:
    # 1) Priorytet: nazwa sekcji z Kislist
    s = (section_name or '').lower()
    for key, mapped in SECTION_TYPE_MAP:
        if key in s:
            return mapped
    # 2) Heurystyka po nazwie i URL
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
            # Prefer producer URLs (ale i tak bierzemy wszystko)
            products.append({'section': sec_name, 'name': name, 'url': purl})
            if len(products) >= limit:
                return products
    return products[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True, help='Kislist list-preview URL')
    ap.add_argument('--limit', type=int, default=2, help='Number of products to test (max collected this run)')
    ap.add_argument('--output', default='/mnt/RZECZY/Produkty_z_Kislist', help='Main output folder')
    ap.add_argument('--batch', type=int, default=50, help='Batch size per run')
    ap.add_argument('--state', default='/mnt/RZECZY/KislistScraper_Pro/.kislist_state.json', help='Checkpoint state file')
    ap.add_argument('--auto', action='store_true', help='Process all batches automatically in a single run')
    ap.add_argument('--log', help='Path to JSONL log file; defaults to /mnt/RZECZY/AgentMode_Archive/run_logs/log_YYYYmmdd_HHMMSS.jsonl')
    args = ap.parse_args()

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    # Logger
    if args.log:
        log_path = Path(args.log)
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = Path('/mnt/RZECZY/AgentMode_Archive/run_logs') / f'log_{ts}.jsonl'
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
        print('❌ Nie znaleziono produktów w liście')
        write_log({'event': 'no_products', 'ts': datetime.now().isoformat()})
        return 2

    # Wczytaj checkpoint
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
        print(f'✅ Batch: {len(batch_products)} produktów ({s_idx+1}-{e_idx} z {len(products)})')
        write_log({'event': 'batch_start', 'from': s_idx+1, 'to': e_idx, 'total': len(products), 'ts': datetime.now().isoformat()})
        for idx, p in enumerate(batch_products, start=s_idx + 1):
            ptype = detect_product_type(p['name'], p['url'], p.get('section',''))
            clean_name = sanitize_filename(p['name'])
            product_folder = out_root / ptype / f"{idx:03d}_{clean_name}"
            product_folder.mkdir(parents=True, exist_ok=True)

            print(f"\n[{idx}] {p['name']} ({ptype}) -> {p['url']}")
            write_log({'event': 'product_start', 'idx': idx, 'name': p['name'], 'ptype': ptype, 'url': p['url'], 'folder': str(product_folder), 'ts': datetime.now().isoformat()})
            try:
                scraper.scrape_universal_variants(p['url'], f"{idx:03d}_{clean_name}", str(product_folder), ptype)
                write_log({'event': 'product_done', 'idx': idx, 'status': 'ok', 'ts': datetime.now().isoformat()})
            except Exception as e:
                print(f"❌ Błąd produktu {idx}: {e}")
                write_log({'event': 'product_done', 'idx': idx, 'status': 'error', 'error': str(e), 'ts': datetime.now().isoformat()})

    # Tryb pojedynczego batcha lub automatyczny loop
    if args.auto:
        while start_index < len(products):
            end_index = min(start_index + args.batch, len(products))
            process_range(start_index, end_index)
            start_index = end_index
            # Zapisz checkpoint po każdym batchu
            try:
                state = {
                    'url': args.url,
                    'last_index': end_index if end_index < len(products) else 0,
                    'total': len(products)
                }
                state_path.parent.mkdir(parents=True, exist_ok=True)
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
                print(f"\n💾 Zapisano checkpoint: {state_path} -> last_index={state['last_index']}")
                write_log({'event': 'checkpoint', 'last_index': state['last_index'], 'ts': datetime.now().isoformat()})
            except Exception as e:
                print(f"⚠️ Nie można zapisać checkpointu: {e}")
                write_log({'event': 'checkpoint_error', 'error': str(e), 'ts': datetime.now().isoformat()})
        print(f"\n🎉 Wszystkie batch'e zakończone. Sprawdź: {out_root}")
        write_log({'event': 'done', 'ts': datetime.now().isoformat()})
        return 0
    else:
        end_index = min(start_index + args.batch, len(products))
        process_range(start_index, end_index)
        # Zapisz checkpoint
        try:
            state = {
                'url': args.url,
                'last_index': end_index if end_index < len(products) else 0,  # 0 = zakończono, gotowe do restartu
                'total': len(products)
            }
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            print(f"\n💾 Zapisano checkpoint: {state_path} -> last_index={state['last_index']}")
            write_log({'event': 'checkpoint', 'last_index': state['last_index'], 'ts': datetime.now().isoformat()})
        except Exception as e:
            print(f"⚠️ Nie można zapisać checkpointu: {e}")
            write_log({'event': 'checkpoint_error', 'error': str(e), 'ts': datetime.now().isoformat()})

        print(f"\n🎉 Batch zakończony. Sprawdź: {out_root}")
        write_log({'event': 'done_batch', 'ts': datetime.now().isoformat()})
        return 0


if __name__ == '__main__':
    sys.exit(main())