# KislistScraper Pro

Zaawansowany scraper produktów z list Kislist.com. Narzędzie automatyzuje pobieranie danych i obrazów wariantów ze stron dostawców (m.in. Porta, Dekordia, Domni, Lazienkarium), wykorzystując Selenium oraz analizę AI.

## Główne funkcje

* **Głęboki scraping wariantów:** Skrypt analizuje źródłowe strony producentów, pobierając wszystkie dostępne opcje kolorystyczne i powiązane zdjęcia w najwyższej jakości.
* **Integracja z AI:** Wykorzystanie modeli językowych (Ollama lub OpenAI API) do inteligentnej analizy struktury strony (DOM) oraz nazw plików w celu trafnego kategoryzowania materiałów i kolorów.
* **Wielowątkowość:** Automatyczna detekcja zasobów systemowych (CPU/RAM) w celu optymalizacji liczby wątków pracujących równolegle.
* **Dwa tryby pracy:** Możliwość uruchomienia przez interfejs graficzny (GUI - Tkinter) dla łatwej obsługi lub z poziomu wiersza poleceń (CLI) w celu automatyzacji zadań wsadowych.

## Struktura pobranych danych

Produkty są automatycznie kategoryzowane w przejrzystej strukturze katalogów:

```text
Produkty_z_Kislist/
├── [Kategoria] (np. Drzwi_Wewnetrzne)/
│   ├── [ID_Nazwa_Produktu]/
│   │   ├── [Nazwa_Wariantu] (np. Dab_Mauvella)/
│   │   │   ├── image.jpg
│   │   │   ├── door_variant.jpg
│   │   │   └── variant_info.json (metadane)
