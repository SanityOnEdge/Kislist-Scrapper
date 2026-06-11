#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified runner for KislistScraper Pro
- GUI mode: --gui
- CLI auto-batch mode: provide --url and optional --batch/--limit/--output
Examples:
  python run_kislist.py --gui
  python run_kislist.py --url "https://kislist.com/list-preview/..." --auto --batch 50 --limit 999 \
         --output "/mnt/RZECZY/Produkty_z_Kislist"
"""

import argparse
import subprocess
import sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gui', action='store_true', help='Launch Selenium GUI')
    ap.add_argument('--url', help='Kislist list-preview URL (for CLI mode)')
    ap.add_argument('--batch', type=int, default=50)
    ap.add_argument('--limit', type=int, default=999)
    ap.add_argument('--output', default='/mnt/RZECZY/Produkty_z_Kislist')
    ap.add_argument('--state', default='/mnt/RZECZY/KislistScraper_Pro/.kislist_state.json')
    ap.add_argument('--auto', action='store_true', help='Process all batches automatically')
    args = ap.parse_args()

    base = Path(__file__).resolve().parent

    if args.gui:
        cmd = [sys.executable, str(base / 'selenium_gui.py')]
        return subprocess.call(cmd)

    if not args.url:
        print('❌ Podaj --url lub użyj --gui')
        return 2

    cmd = [
        sys.executable, str(base / 'test_kislist_cli.py'),
        '--url', args.url,
        '--limit', str(args.limit),
        '--batch', str(args.batch),
        '--output', args.output,
        '--state', args.state
    ]
    if args.auto:
        cmd.append('--auto')

    print('🚀 Start CLI:', ' '.join(cmd))
    return subprocess.call(cmd)

if __name__ == '__main__':
    sys.exit(main())