#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI DOM Analyzer
- Jeśli AI (Ollama/OpenAI) jest dostępne wg ai_config, buduje zwięzły zrzut DOM (tylko obrazy i powiązane elementy)
  i prosi model o klasyfikację: product_main, product_variant, handle, ad, logo, ignore.
- Jeśli AI nie jest dostępne, zwraca None (scraper używa heurystyk).
"""
from typing import Optional, Dict, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
import json

try:
    import ai_config
except Exception:
    ai_config = None

PROMPTS_DIR = "prompts"


def _load_prompt_for_domain(domain: str) -> str:
    from pathlib import Path
    base = Path(__file__).resolve().parent
    # dopasuj porta / lazienkarium / default
    fname = "default.md"
    if "porta.com.pl" in domain:
        fname = "porta.md"
    elif "lazienkarium.pl" in domain:
        fname = "lazienkarium.md"
    p = base / PROMPTS_DIR / fname
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return "Zidentyfikuj obrazy produktu i odrzuć reklamy/banery. Zwróć JSON z polami: product_main, handles, ignore, ads."


def _build_dom_snapshot(driver: WebDriver, max_items: int = 80) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    imgs = driver.find_elements(By.TAG_NAME, "img")
    for img in imgs[:max_items]:
        try:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            cls = (img.get_attribute("class") or "").strip()
            idv = img.get_attribute("id") or ""
            w = img.get_attribute("width") or ""
            h = img.get_attribute("height") or ""
            items.append({
                "type": "img",
                "src": src,
                "alt": alt,
                "class": cls,
                "id": idv,
                "w": w,
                "h": h
            })
        except Exception:
            continue
    # proste przyciski/option do koloru/klamki
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, "button, a")
        for b in btns[:80]:
            try:
                txt = (b.text or "").strip()
                cls = (b.get_attribute("class") or "").strip()
                idv = b.get_attribute("id") or ""
                data_color = b.get_attribute("data-color") or ""
                role = b.get_attribute("role") or ""
                items.append({
                    "type": "btn",
                    "text": txt,
                    "class": cls,
                    "id": idv,
                    "data_color": data_color,
                    "role": role
                })
            except Exception:
                continue
    except Exception:
        pass
    return items


def _ask_ai(prompt: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not ai_config:
        return None
    try:
        client = ai_config.get_client()
        if not client:
            return None
        full_prompt = prompt + "\n\nDANE_WEJSCIOWE_JSON:\n" + json.dumps(payload, ensure_ascii=False)
        resp = ai_config.complete_json(full_prompt)
        if isinstance(resp, dict):
            return resp
        try:
            return json.loads(resp)
        except Exception:
            return None
    except Exception:
        return None


def analyze_dom(driver: WebDriver, url: str) -> Optional[Dict[str, Any]]:
    """Zwraca słownik z kluczami: product_main (list[str]), handles (list[str]), ignore (list[str]), ads (list[str])"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
    except Exception:
        domain = ""
    prompt = _load_prompt_for_domain(domain)
    snapshot = _build_dom_snapshot(driver)
    payload = {"url": url, "domain": domain, "nodes": snapshot}
    result = _ask_ai(prompt, payload)
    # spodziewany format
    if not result or not isinstance(result, dict):
        return None
    for k in ["product_main", "handles", "ignore", "ads"]:
        if k not in result:
            result[k] = []
    return result
