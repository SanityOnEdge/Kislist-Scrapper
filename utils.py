# utils.py
import re
from urllib.parse import urlparse

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Czyści nazwę pliku lub folderu ze znaków specjalnych i polskich znaków diakrytycznych."""
    if not filename:
        return "unknown"
    
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    for pl, en in replacements.items():
        filename = filename.replace(pl, en)
        
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename).strip('_')
    
    return filename[:max_length] or "unknown"

def extract_domain(url: str) -> str:
    """Wyciąga nazwę domeny z adresu URL."""
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return "unknown_domain"
