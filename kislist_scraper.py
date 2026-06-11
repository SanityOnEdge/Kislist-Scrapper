#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania i katalogowania produktów ze strony kislist.com

Autor: Assistant
Data: 2025-09-25
"""

import re
import json
import os
import requests
from urllib.parse import urljoin
from pathlib import Path
import csv
from typing import Dict, List, Any

class KislistScraper:
    def __init__(self, output_dir: str = "kislist_products"):
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract_data_from_page(self, url: str) -> Dict[str, Any]:
        """
        Pobiera stronę i ekstraktuje dane JSON z sekcjami produktów
        """
        try:
            print(f"Pobieranie danych z: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            
            # Szukamy w kodzie strony zmiennej window.sections
            content = response.text
            
            # Wzorzec regex do znalezienia window.sections
            pattern = r'window\.sections\s*=\s*(\[.*?\]);'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                sections_data = json.loads(json_str)
                return sections_data
            else:
                print("Nie znaleziono danych window.sections na stronie")
                return {}
                
        except Exception as e:
            print(f"Błąd podczas pobierania strony: {e}")
            return {}
    
    def create_directories(self, sections_data: List[Dict]):
        """
        Tworzy strukturę katalogów dla sekcji produktów
        """
        self.output_dir.mkdir(exist_ok=True)
        
        for section in sections_data:
            section_name = self.sanitize_filename(section.get('name', 'bez_nazwy'))
            section_dir = self.output_dir / section_name
            section_dir.mkdir(exist_ok=True)
            # Dalsze podkatalogi (pojedyncze produkty) będą tworzone w trakcie przetwarzania
            
    def sanitize_filename(self, filename: str) -> str:
        """
        Czyści nazwę pliku z niedozwolonych znaków
        """
        # Zamienia polskie znaki i usuwa problematyczne znaki
        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 
            'ó': 'o', 'ś': 's', 'ż': 'z', 'ź': 'z',
            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
            'Ó': 'O', 'Ś': 'S', 'Ż': 'Z', 'Ź': 'Z'
        }
        
        for polish, latin in replacements.items():
            filename = filename.replace(polish, latin)
            
        # Usuwa lub zamienia problematyczne znaki
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        
        return filename.strip('_')
    
    def download_image(self, url: str, filepath: Path) -> bool:
        """
        Pobiera obraz z podanego URL
        """
        try:
            if url and not filepath.exists():
                response = self.session.get(url)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Błąd podczas pobierania obrazu {url}: {e}")
        return False
    
    def process_products(self, sections_data: List[Dict]):
        """
        Przetwarza produkty z każdej sekcji i zapisuje do plików
        """
        print("\nPrzetwarzanie produktów...")
        
        for section in sections_data:
            section_name = self.sanitize_filename(section.get('name', 'bez_nazwy'))
            section_dir = self.output_dir / section_name
            
            print(f"\nPrzetwarzam sekcję: {section.get('name', 'bez_nazwy')}")
            print(f"Liczba produktów: {len(section.get('items', []))}")
            
            # Przygotowanie listy produktów dla CSV
            products_list = []
            
            for idx, item in enumerate(section.get('items', []), 1):
                # Tworzymy katalog produktu: typ_produktu/nazwa_produktu/
                product_name_base = item.get('collection') or item.get('supplier_product_uid') or item.get('catalog_nr') or item.get('key') or f"produkt_{idx:03d}"
                product_name = f"{idx:03d}_{self.sanitize_filename(str(product_name_base))}"
                product_dir = section_dir / product_name
                product_dir.mkdir(exist_ok=True)
                
                product = {
                    'lp': idx,
                    'nazwa_kolekcji': item.get('collection', ''),
                    'katalog_nr': item.get('catalog_nr', ''),
                    'cena': item.get('price', 0),
                    'cena_netto': item.get('net_price', 0),
                    'rozmiar': item.get('size', ''),
                    'dostawca': item.get('supplier', ''),
                    'url': item.get('url', ''),
                    'vat': item.get('vat', 0),
                    'notatki': item.get('notes', ''),
                    'typ': item.get('type', ''),
                    'obrazek_lokalny': ''
                }
                
                # Pobieranie obrazków jeśli dostępne
                photo_info = item.get('photo', {})
                thumb_urls = photo_info.get('thumb_urls', {})
                
                for file_ref, urls in thumb_urls.items():
                    tiny_thumb = urls.get('tiny_thumb')
                    if tiny_thumb:
                        img_filepath = product_dir / "image.jpg"
                        if self.download_image(tiny_thumb, img_filepath):
                            product['obrazek_lokalny'] = f"{product_dir.name}/image.jpg"
                            print(f"  ✓ Pobrano obraz dla {product_dir.name}: image.jpg")
                        break  # Bierzemy tylko pierwszy obrazek
                
                # Zapisz metadane produktu w katalogu produktu
                meta_filepath = product_dir / "product.json"
                with open(meta_filepath, 'w', encoding='utf-8') as pf:
                    json.dump(item, pf, ensure_ascii=False, indent=2)
                
                products_list.append(product)
            
            # Zapisanie do CSV
            csv_filename = f"{section_name}_produkty.csv"
            csv_filepath = section_dir / csv_filename
            
            self.save_to_csv(products_list, csv_filepath)
            
            # Zapisanie również do JSON dla pełnych danych sekcji
            json_filename = f"{section_name}_dane.json"
            json_filepath = section_dir / json_filename
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(section, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ Zapisano {len(products_list)} produktów do {csv_filename}")
            
            # Dodatkowe informacje o sekcji
            section_info = {
                'nazwa_sekcji': section.get('name', ''),
                'kolor': section.get('color', ''),
                'liczba_produktow': len(section.get('items', [])),
                'suma_brutto': section.get('total_sum', 0),
                'suma_po_rabacie': section.get('total_sum_with_discount', 0)
            }
            
            info_filepath = section_dir / "info_sekcji.json"
            with open(info_filepath, 'w', encoding='utf-8') as f:
                json.dump(section_info, f, ensure_ascii=False, indent=2)
    
    def save_to_csv(self, products: List[Dict], filepath: Path):
        """
        Zapisuje produkty do pliku CSV
        """
        if not products:
            return
            
        fieldnames = products[0].keys()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
    
    def create_summary_report(self, sections_data: List[Dict]):
        """
        Tworzy raport podsumowujący
        """
        summary = {
            'data_pobrania': str(Path().cwd()),
            'liczba_sekcji': len(sections_data),
            'calkowita_liczba_produktow': sum(len(section.get('items', [])) for section in sections_data),
            'sekcje': []
        }
        
        for section in sections_data:
            section_summary = {
                'nazwa': section.get('name', ''),
                'liczba_produktow': len(section.get('items', [])),
                'suma_brutto': section.get('total_sum', 0),
                'suma_po_rabacie': section.get('total_sum_with_discount', 0),
                'kolor': section.get('color', '')
            }
            summary['sekcje'].append(section_summary)
        
        summary_filepath = self.output_dir / "raport_podsumowanie.json"
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Tworzenie czytelnego raportu tekstowego
        text_report = self.output_dir / "raport.txt"
        with open(text_report, 'w', encoding='utf-8') as f:
            f.write("RAPORT POBIERANIA PRODUKTÓW Z KISLIST.COM\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Liczba sekcji: {summary['liczba_sekcji']}\n")
            f.write(f"Całkowita liczba produktów: {summary['calkowita_liczba_produktow']}\n\n")
            
            for sekcja in summary['sekcje']:
                f.write(f"Sekcja: {sekcja['nazwa']}\n")
                f.write(f"  - Produktów: {sekcja['liczba_produktow']}\n")
                f.write(f"  - Suma brutto: {sekcja['suma_brutto']:.2f} zł\n")
                f.write(f"  - Suma po rabacie: {sekcja['suma_po_rabacie']:.2f} zł\n\n")
        
        print(f"\n✓ Utworzono raport podsumowujący: {summary_filepath}")
        print(f"✓ Utworzono raport tekstowy: {text_report}")
    
    def scrape(self, url: str):
        """
        Główna metoda scrapowania
        """
        print("=" * 60)
        print("KISLIST.COM SCRAPER")
        print("=" * 60)
        
        # Pobieranie danych
        sections_data = self.extract_data_from_page(url)
        
        if not sections_data:
            print("Nie udało się pobrać danych ze strony!")
            return
        
        print(f"Znaleziono {len(sections_data)} sekcji produktów")
        
        # Tworzenie struktury katalogów
        self.create_directories(sections_data)
        
        # Przetwarzanie produktów
        self.process_products(sections_data)
        
        # Tworzenie raportu
        self.create_summary_report(sections_data)
        
        print(f"\n✓ Zakończono! Produkty zostały zapisane w katalogu: {self.output_dir}")
        print(f"✓ Struktura katalogów została utworzona według sekcji produktów")


def main():
    """
    Funkcja główna
    """
    # URL do scrapowania - może być przekazany jako argument
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://kislist.com/list-preview/CzjnBnLJkchnqmYFI2An2KDZhFA0crwntz7D?lang=pl"
    
    # Katalog wyjściowy - może być przekazany jako drugi argument
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "kislist_products"
    
    print(f"URL: {url}")
    print(f"Katalog wyjściowy: {output_dir}")
    
    scraper = KislistScraper(output_dir)
    scraper.scrape(url)


if __name__ == "__main__":
    main()