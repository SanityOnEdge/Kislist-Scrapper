# KislistScraper Pro

An advanced product scraper for Kislist.com listings. The tool automates the retrieval of data and images of product variants from supplier websites (including Porta, Dekordia, Domni, and Lazienkarium) using Selenium and AI analysis.

## About the Development Process (AI-Assisted Development)

The system architecture, project logic, and data flow structure were custom-designed. The source code itself was generated, debugged, and optimized using Prompt Engineering techniques and LLM models. The project serves as a practical example of a modern AI-Assisted Development approach, where artificial intelligence acts as an executor for defined engineering objectives

## Key Features

* **In-depth variant scraping:** The script analyzes manufacturers’ source pages, retrieving all available color options and related images in the highest quality.
* **AI integration:** Utilizes language models (Ollama or OpenAI API) to intelligently analyze the page structure (DOM) and file names in order to accurately categorize materials and colors.
* **Multithreading:** Automatic detection of system resources (CPU/RAM) to optimize the number of threads running in parallel.
* **Two operating modes:** Can be launched via a graphical user interface (GUI—Tkinter) for easy use or from the command line (CLI) to automate batch tasks.

## Structure of Downloaded Data

Products are automatically categorized into a clear structure
```text
Products_from_Kislist/
├── [Category] (e.g., Interior_Doors)/
│   ├── [Product_ID_Name]/
│   │   ├── [Variant_Name] (e.g., Dab_Mauvella)/
│   │   │   ├── image.jpg
│   │   │   ├── door_variant.jpg
│   │   │   └── variant_info.json (metadata)
