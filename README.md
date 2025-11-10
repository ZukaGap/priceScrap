# PriceScrap - Python Price Scraper

A Python script to scrape product information (SKU, title, price) from e-commerce sites. It logs price history, saves the raw HTML for archival, and generates summary reports in Excel.

This script was initially built for `nova.ge`, but the core scraping logic inside the `process_url()` function can be adapted to work with other websites.

## Key Features

* **Dual Mode**: Run the scraper on a single URL or on a batch of URLs from a `targetURL.json` file.
* **Price History**: Tracks `newPrice`, `oldPrice`, `min price`, and `max price` over time.
* **Excel Reporting**:
   * **Domain Summary**: Creates a master report (e.g., `nova.ge-summary.xlsx`) with the latest data for all tracked items from that domain.
   * **Item Log**: Creates a detailed historical log for each item (e.g., `sku-ID.xlsx`) showing every time it was scraped.
* **HTML Archiving**: Saves a timestamped HTML file for every successful scrape, perfect for debugging and historical records.
* **Resilient Batching**: In batch mode, if one URL fails (e.g., 404 error or parsing issue), the script logs the error and continues to the next URL without crashing.

## Output File Structure

The script will automatically create the following directory structure in the same folder where it is run:

```
priceScrap/
├── priceScrap.py              # The main script
├── targetURL.json             # Your list of URLs
│
└── nova.ge/                   # Folder for the domain
    ├── nova.ge-summary.xlsx   # Master report for all items
    │
    ├── 28859/                 # Folder for Item ID 28859
    │   ├── sku-28859.xlsx     # Historical log for this item
    │   ├── sku-28859_...html  # HTML snapshot from first run
    │   └── sku-28859_...html  # HTML snapshot from second run
    │
    └── 30123/                 # Folder for Item ID 30123
        ├── sku-30123.xlsx
        └── sku-30123_...html
```

## Setup & Installation

### 1. Download

Download `priceScrap.py` (and optionally `targetURL.json` as a template) into your project directory.

### 2. Install Dependencies

This script requires `requests`, `beautifulsoup4`, and `openpyxl`. You can install them using `pip3` (for macOS/Linux) or `pip` (for Windows).

```bash
pip3 install requests beautifulsoup4 openpyxl
```

Or on Windows:

```bash
pip install requests beautifulsoup4 openpyxl
```

## How to Run

You can run the script in two ways:

### 1. Single URL Mode

Pass a single URL as an argument in the terminal. **Important**: Make sure to wrap the URL in single quotes (`' '`) so the terminal treats it as one argument.

```bash
# Example for a single product
python3 priceScrap.py 'https://nova.ge/product-1'
```

On Windows, use:

```bash
python priceScrap.py 'https://nova.ge/product-1'
```

### 2. Batch Mode (Multiple URLs)

Create a `targetURL.json` file in the same directory as the script with your list of URLs:

```json
{
  "urls": [
    "https://nova.ge/product-1",
    "https://nova.ge/product-2",
    "https://nova.ge/product-3"
  ]
}
```

Then run the script without any arguments:

```bash
python3 priceScrap.py
```

The script will process all URLs in the JSON file, logging any errors and continuing with the next URL if one fails.

## Understanding the Output

### Domain Summary Report

The `{domain}-summary.xlsx` file contains a snapshot of all tracked items with their most recent data:

| SKU | Title | New Price | Old Price | Min Price | Max Price | Last Updated |
|-----|-------|-----------|-----------|-----------|-----------|--------------|

### Item Historical Log

Each item gets its own `sku-{id}.xlsx` file with a complete history of every scrape:

| Timestamp | New Price | Old Price | Min Price | Max Price |
|-----------|-----------|-----------|-----------|-----------|

### HTML Archives

Each scrape saves a timestamped HTML file for that specific product, allowing you to:
- Debug parsing issues
- Review historical product descriptions
- Verify price changes manually

## Customization

To adapt this script for other e-commerce sites, you'll need to modify the `process_url()` function to match the HTML structure of your target website. Look for:

- Product SKU/ID selectors
- Product title selectors
- Price element selectors (current and original price)
- URL structure patterns

## Error Handling

The script includes comprehensive error handling:
- Network errors (connection timeouts, DNS failures)
- HTTP errors (404, 500, etc.)
- Parsing errors (missing elements, unexpected HTML structure)
- File I/O errors

All errors are logged to the console with descriptive messages, and in batch mode, the script continues processing remaining URLs.

## Requirements

- Python 3.6+
- requests
- beautifulsoup4
- openpyxl

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to fork this project and adapt it for your own e-commerce scraping needs. If you encounter issues or have suggestions, please open an issue or submit a pull request.

---

**Note**: Always respect the terms of service and robots.txt of websites you scrape. This tool is intended for personal price monitoring and should not be used to overload servers or violate website policies.
