#!/usr/bin/env bash
set -euo pipefail
PYTHON="/usr/bin/python"
ROOT="/mnt/RZECZY/KislistScraper_Pro"
exec "$PYTHON" "$ROOT/run_kislist.py" --gui
