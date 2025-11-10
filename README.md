PriceScrap - Python Price Scraper Python script to scrape product information (SKU, title, price) from e-commerce sites. It logs price history, saves the raw HTML for archival, and generates summary reports in Excel.This script was initially built for nova.ge, but the core scraping logic inside the process_url() function can be adapted to work with other websites.Key FeaturesDual Mode: Run the scraper on a single URL or on a batch of URLs from a targetURL.json file.Price History: Tracks newPrice, oldPrice, min price, and max price over time.Excel Reporting:Domain Summary: Creates a master report (e.g., nova.ge-summary.xlsx) with the latest data for all tracked items from that domain.Item Log: Creates a detailed historical log for each item (e.g., sku-id.xlsx) showing every time it was scraped.HTML Archiving: Saves a timestamped HTML file for every successful scrape, perfect for debugging and historical records.Resilient Batching: In batch mode, if one URL fails (e.g., 404 error or parsing issue), the script logs the error and continues to the next URL without crashing.Output File StructureThe script will automatically create the following directory structure in the same folder where it is run:priceScrap/
├── priceScrap.py            # The main script
├── targetURL.json         # Your list of URLs
│
└── nova.ge/                 <-- Folder for the domain
    ├── nova.ge-summary.xlsx   <-- Master report for all items
    │
    ├── [ID-1]/                 <-- Folder for Item ID
    │   ├── sku-1.xlsx     <-- Historical log for this item
    │   ├── sku-1...html  <-- HTML snapshot from first run
    │   └── sku-1...html  <-- HTML snapshot from second run
    │
    └── [ID-2]/                 <-- Folder for Item ID 
        ├── sku-2.xlsx
        └── sku-2...html
Setup & InstallationDownload:Download priceScrap.py (and optionally targetURL.json as a template) into your project directory.Install Dependencies:This script requires requests, beautifulsoup4, and openpyxl. You can install them using pip3 (for macOS/Linux) or pip (for Windows).pip3 install requests beautifulsoup4 openpyxl
How to RunYou can run the script in two ways:1. Single URL ModePass a single URL as an argument in the terminal. Important: Make sure to wrap the URL in single quotes (' ') so the terminal treats it as one argument.# Example for a single product
python3 priceScrap.py '[https://example.com/product/1](https://example.com/)'
