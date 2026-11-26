# KislistScraper Pro

(Author: Maciej Bronisz)

Automated product variant scraper and data-structuring pipeline for Kislist.com listings. Extracts product metadata, color variants, and high-resolution images from external supplier websites (including Porta, Dekordia, Domni, and Lazienkarium) using Selenium and LLM-based DOM classification.

## Key Features

* **Automated Variant Extraction:** Crawls supplier pages to collect available color/material variants and download full-resolution product imagery.
* **LLM-Powered Classification:** Integrates with local models (**Ollama**) or the **OpenAI API** to analyze dynamic HTML structures (DOM) and standardize material and color labels.
* **Adaptive Multithreading:** Detects available system resources (CPU/RAM) via `psutil` to scale parallel scraping threads without overloading the host machine.
* **Dual Interface (GUI & CLI):** Includes a Tkinter desktop interface for ad-hoc runs and a headless batch CLI mode with JSONL logging and checkpoint resume support.

## Output Data Structure

Extracted assets and metadata are automatically organized into a hierarchical directory layout:

```text
Produkty_z_Kislist/
└── [Category]/                       # e.g., drzwi, umywalka
    └── [NNN_Product_Name]/
        └── [Variant_Name]/           # e.g., Dab_Mauvella
            ├── image.jpg
            ├── klamka_01.jpg
            └── main_01.jpg
```

## Tech Stack

* **Language:** Python 3
* **Scraping & Parsing:** Selenium, BeautifulSoup4, Requests, Regex
* **AI / Classification:** Ollama (local LLMs), OpenAI API
* **Interface & Concurrency:** Tkinter, `ThreadPoolExecutor`, `psutil`

## Quick Start

1. Clone the repository and set up a virtual environment:
   ```bash
   git clone https://github.com/SanityOnEdge/KislistScraper-Pro.git
   cd KislistScraper-Pro
   python -m venv .venv
   source .venv/bin/activate      # Bash/Zsh (Fish: source .venv/bin/activate.fish)
   pip install -r requirements.txt
   ```
2. Ensure Chromium/Chrome and `chromedriver` are installed on your system, and configure your LLM backend (local **Ollama** or OpenAI API key) in `ai_config.py`.
3. Launch the application:
   ```bash
   # GUI mode
   python run_kislist.py --gui

   # Headless CLI batch mode
   python run_kislist.py --url "https://kislist.com/list-preview/<LIST_ID>" --auto --batch 50
   ```
