# KislistScraper Pro

(Autor: Maciej Bronisz)


Automated product variant scraper and data-structuring pipeline for Kislist.com listings. Extracts product metadata, color variants, and high-resolution images from external supplier websites (including Porta, Dekordia, Domni, and Lazienkarium) using Selenium and LLM-based DOM classification.

> **Tip:** Add a screenshot of the Tkinter GUI or a sample `variant_info.json` output right here so reviewers can see the project in action within seconds.

## Key Features

* **Automated Variant Extraction:** Crawls supplier pages to collect all available color/material variants and download full-resolution product imagery.
* **LLM-Powered Classification:** Integrates with local models (**Ollama**) or the **OpenAI API** to parse dynamic HTML structures (DOM) and file names, standardizing material and color labels.
* **Adaptive Multithreading:** Detects available system resources (CPU/RAM) to scale parallel scraping threads without overloading the host machine.
* **Dual Interface (GUI & CLI):** Includes a Tkinter desktop interface for ad-hoc runs and a CLI mode suited for batch automation.

## Output Data Structure

Extracted assets and validated metadata are automatically organized into a hierarchical directory layout:

```text
Products_from_Kislist/
└── [Category]/                       # e.g., Interior_Doors
    └── [Product_ID_Name]/
        └── [Variant_Name]/           # e.g., Dab_Mauvella
            ├── image.jpg
            ├── door_variant.jpg
            └── variant_info.json     # Structured product & variant metadata
```

## Tech Stack

* **Language:** Python 3
* **Scraping & Parsing:** Selenium, BeautifulSoup, Regex
* **AI / Classification:** Ollama (local LLMs), OpenAI API
* **Interface & Concurrency:** Tkinter, `threading` / concurrent workers

## Quick Start

1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/SanityOnEdge/<repo-name>.git
   cd <repo-name>
   pip install -r requirements.txt
   ```
2. Configure your LLM backend (local **Ollama** instance or OpenAI API key) in `ai_config.py`.
3. Launch the application:
   ```bash
   # GUI mode
   python selenium_gui.py

   # CLI mode
   python selenium_variant_scraper.py
   ```
