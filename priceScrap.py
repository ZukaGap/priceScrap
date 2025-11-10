import sys
import os
import requests
import re
import json  # <-- ADDED IMPORT
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils.exceptions import InvalidFileException

# --- Helper Function to Clean Prices ---

def clean_price(price_text):
    """
    Cleans text like "1,299.99 ₾" or "$49.50" into a simple float (e.g., 1299.99 or 49.50)
    """
    if price_text is None:
        return None
    try:
        # Remove all non-digit characters except for the decimal point
        # This will handle "1,299.99 ₾" -> "1299.99"
        cleaned_text = re.sub(r"[^0-9.]", "", price_text)
        
        # Handle cases where multiple dots might exist after cleaning, e.g., "1.299.99"
        parts = cleaned_text.split('.')
        if len(parts) > 2:
            # Join all parts except the last one, then add the last part back
            cleaned_text = "".join(parts[:-1]) + "." + parts[-1]
            
        return float(cleaned_text)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert price text '{price_text}' to a number.")
        return None

# --- Main Scraping and File Function ---

def process_url(url):
    """
    Main function to scrape a URL, save HTML, and update Excel files.
    """
    
    # --- 1. SETUP AND NETWORK REQUEST ---
    print(f"Processing URL: {url}")
    
    # Set headers to mimic a real browser
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"
    }
    
    # Get current timestamp for filenames and logs
    now = datetime.now()
    mod_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Get base directory (where the script is located)
    base_dir = os.getcwd()
    
    # Parse domain from URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if not domain:
        raise ValueError("Invalid URL provided. Could not determine domain.")
        
    # Create domain directory (e.g., /priceScrap/nova.ge/)
    domain_dir = os.path.join(base_dir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    
    # Fetch the webpage content
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # Raise an error if the request failed (e.g., 404, 500)
    html_content = response.text
    
    # --- 2. PARSE HTML (BeautifulSoup) ---
    print("Parsing HTML content...")
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 2a. Find SKU and [ID]
    #
    # --- *** MODIFIED SECTION *** ---
    #
    # First, find the parent element with class="sku" (which is a <p> tag in this case)
    sku_parent_element = soup.find(class_="sku")
    
    if not sku_parent_element:
        raise ValueError("Could not find the parent element with class='sku'. Cannot proceed.")
    
    # Now, find the <span> tag *inside* that parent element
    sku_span = sku_parent_element.find("span")
    
    if not sku_span:
        raise ValueError("Found element with class='sku', but could not find the nested <span> tag. Cannot proceed.")
        
    # The SKU is the text *inside* the span (e.g., "1823396")
    sku = sku_span.get_text(strip=True)
    
    # The [ID] is part of the span's 'id' attribute (e.g., "sku-28859")
    sku_id_attr = sku_span.get("id", "")
    
    item_id = None
    if sku_id_attr.startswith("sku-"):
        item_id = sku_id_attr.split('-')[-1] # This will get "28859"
    
    if not item_id:
        raise ValueError("Could not extract [ID] from SKU span's id attribute. Cannot proceed.")
    #
    # --- *** END OF MODIFIED SECTION *** ---
    #
    
    print(f"Found SKU: {sku} and Item ID: {item_id}")
    
    # 2b. Find Title
    # find class="product__details--title" where nested h1 and get title
    title_div = soup.find(class_="product__details--title")
    title_h1 = title_div.find("h1") if title_div else None
    title = title_h1.get_text(strip=True) if title_h1 else "No Title Found"
    
    # 2c. Find Prices
    # find class="product__oldprice old-price-value-[ID]"
    # find class="product__newprice price-value-[ID]"
    old_price_span = soup.find(class_=f"product__oldprice old-price-value-{item_id}")
    new_price_span = soup.find(class_=f"product__newprice price-value-{item_id}")
    
    old_price_text = old_price_span.get_text(strip=True) if old_price_span else None
    new_price_text = new_price_span.get_text(strip=True) if new_price_span else None
    
    # 2d. Clean prices into numbers
    oldPrice = clean_price(old_price_text)
    newPrice = clean_price(new_price_text)
    
    # Determine the "current price" for min/max logic
    # If it's on sale, newPrice is current. Otherwise, oldPrice is current.
    current_price = newPrice if newPrice is not None else oldPrice
    if current_price is None:
        print("Warning: Could not determine any price for this item.")
        
    print(f"Title: {title}")
    print(f"Old Price: {oldPrice} | New/Sale Price: {newPrice}")

    # --- 3. SAVE HTML FILE ---
    # Create [ID] directory (e.g., /priceScrap/nova.ge/28859/)
    item_dir = os.path.join(domain_dir, item_id)
    os.makedirs(item_dir, exist_ok=True)
    
    # Save HTML file: sku-[ID]-[modifidata].html
    html_filename = f"sku-{item_id}-{file_time_str}.html"
    html_filepath = os.path.join(item_dir, html_filename)
    
    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML content saved to: {html_filepath}")

    # --- 4. UPDATE INDIVIDUAL ITEM EXCEL (Historical Log) ---
    print(f"Updating individual item log: sku-{item_id}.xlsx")
    item_excel_path = os.path.join(item_dir, f"sku-{item_id}.xlsx")
    item_headers = ["SKU", "newPrice", "oldPrice", "title", "url website", "modified data"]
    
    # Define the green fill for sale prices
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    try:
        # Try to load existing workbook
        wb_item = openpyxl.load_workbook(item_excel_path)
        ws_item = wb_item.active
    except (FileNotFoundError, InvalidFileException):
        # Create new one if it doesn't exist or is corrupt
        wb_item = openpyxl.Workbook()
        ws_item = wb_item.active
        ws_item.append(item_headers)

    # Append the new data
    data_row = [sku, newPrice, oldPrice, title, url, mod_time_str]
    ws_item.append(data_row)
    
    # Color the `newPrice` cell if it exists
    if newPrice is not None:
        new_price_cell = ws_item.cell(row=ws_item.max_row, column=2) # Column 2 = "B"
        new_price_cell.fill = green_fill
        
    wb_item.save(item_excel_path)
    wb_item.close()

    # --- 5. UPDATE DOMAIN SUMMARY EXCEL (Master List) ---
    print(f"Updating domain summary log: {domain}-summary.xlsx")
    summary_excel_path = os.path.join(domain_dir, f"{domain}-summary.xlsx")
    summary_headers = ["SKU", "newPrice", "oldPrice", "title", "max price", "min price", "url website", "last modified data"]

    try:
        wb_summary = openpyxl.load_workbook(summary_excel_path)
        ws_summary = wb_summary.active
    except (FileNotFoundError, InvalidFileException):
        wb_summary = openpyxl.Workbook()
        ws_summary = wb_summary.active
        ws_summary.append(summary_headers)

    # Find if this SKU already exists in the summary file
    sku_row_index = None
    # Iterate rows, starting from row 2 (after header)
    for row_idx, row in enumerate(ws_summary.iter_rows(min_row=2, max_col=1), start=2):
        if row[0].value == sku:
            sku_row_index = row_idx
            break
            
    if sku_row_index:
        # --- SKU EXISTS: UPDATE THE ROW ---
        print(f"SKU {sku} found in summary. Updating row {sku_row_index}...")
        
        # Get old min/max prices
        try:
            old_max = float(ws_summary.cell(row=sku_row_index, column=5).value)
        except (ValueError, TypeError):
            old_max = current_price # Set to current if old value is invalid
            
        try:
            old_min = float(ws_summary.cell(row=sku_row_index, column=6).value)
        except (ValueError, TypeError):
            old_min = current_price # Set to current if old value is invalid

        # Calculate new min/max
        new_max = old_max
        new_min = old_min
        if current_price is not None:
            if old_max is None:
                new_max = current_price
            else:
                new_max = max(old_max, current_price)
                
            if old_min is None:
                new_min = current_price
            else:
                new_min = min(old_min, current_price)
            
        # Update row data
        ws_summary.cell(row=sku_row_index, column=2, value=newPrice) # newPrice
        ws_summary.cell(row=sku_row_index, column=3, value=oldPrice) # oldPrice
        ws_summary.cell(row=sku_row_index, column=4, value=title) # title
        ws_summary.cell(row=sku_row_index, column=5, value=new_max) # max price
        ws_summary.cell(row=sku_row_index, column=6, value=new_min) # min price
        ws_summary.cell(row=sku_row_index, column=7, value=url) # url
        ws_summary.cell(row=sku_row_index, column=8, value=mod_time_str) # last modified
        
        # Update cell color
        new_price_cell = ws_summary.cell(row=sku_row_index, column=2)
        if newPrice is not None:
            new_price_cell.fill = green_fill
        else:
            new_price_cell.fill = PatternFill(fill_type=None) # Remove fill if no longer on sale
            
    else:
        # --- SKU IS NEW: APPEND A NEW ROW ---
        print(f"SKU {sku} is new. Appending to summary...")
        
        # Set min/max to the current price since it's the first entry
        new_row_data = [sku, newPrice, oldPrice, title, current_price, current_price, url, mod_time_str]
        ws_summary.append(new_row_data)
        
        # Color the `newPrice` cell
        if newPrice is not None:
            new_price_cell = ws_summary.cell(row=ws_summary.max_row, column=2)
            new_price_cell.fill = green_fill

    # Save and close the summary workbook
    wb_summary.save(summary_excel_path)
    wb_summary.close()

# --- SCRIPT EXECUTION (MODIFIED FOR BATCH PROCESSING) ---

if __name__ == "__main__":
    # This block runs when you execute: python3 priceScrap.py [ARGUMENT]
    
    # Check if an argument is provided
    if len(sys.argv) != 2:
        print("--- ERROR: Invalid Usage ---")
        print("Please provide a single URL or a path to a .json file.")
        print("\nExample (Single URL):")
        print("  python3 priceScrap.py 'https://www.example.com/product/123'")
        print("\nExample (Batch File):")
        print("  python3 priceScrap.py targetURL.json")
        sys.exit(1) # Exit with a (1) error code
        
    argument = sys.argv[1]
    
    # --- BATCH MODE: Argument is a .json file ---
    if argument.endswith('.json'):
        print(f"--- Running in BATCH mode from file: {argument} ---")
        urls_to_process = []
        
        # --- 1. Read and Parse JSON file ---
        try:
            with open(argument, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's a list of objects, as per your example
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "url" in item:
                        urls_to_process.append(item["url"])
                    else:
                        print(f"Warning: Skipping invalid item in JSON list: {item}")
            else:
                print(f"Error: JSON file must contain a list of objects, e.g., [ {{'url': '...'}} ]")
                sys.exit(1)
                
        except FileNotFoundError:
            print(f"--- SCRIPT FAILED ---")
            print(f"Error: The file '{argument}' was not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"--- SCRIPT FAILED ---")
            print(f"Error: The file '{argument}' contains invalid JSON.")
            print("Please check the file for syntax errors (e.g., missing commas, brackets).")
            sys.exit(1)
        except Exception as e:
            print(f"--- SCRIPT FAILED ---")
            print(f"An error occurred while reading the file: {e}")
            sys.exit(1)

        if not urls_to_process:
            print("No valid URLs found in the JSON file. Exiting.")
            sys.exit(0)
            
        print(f"Found {len(urls_to_process)} URLs to process...")
        print("=" * 50)
        
        # --- 2. Process each URL from the list ---
        success_count = 0
        fail_count = 0
        
        for i, url in enumerate(urls_to_process, 1):
            print(f"Processing URL {i} of {len(urls_to_process)}: {url}")
            try:
                process_url(url)
                print("--- URL processed successfully ---")
                success_count += 1
                
            # Individual error handling so one bad URL doesn't stop the batch
            except requests.exceptions.HTTPError as e:
                print(f"--- FAILED (HTTP Error): {e} ---")
                fail_count += 1
            except (ValueError, AttributeError) as e:
                print(f"--- FAILED (Parsing Error): {e} ---")
                fail_count += 1
            except Exception as e:
                print(f"--- FAILED (Unexpected Error): {e} ---")
                fail_count += 1
            print("-" * 50) # Add a separator between items
            
        # --- 3. Print final summary ---
        print("\n" + "="*50)
        print("--- BATCH PROCESSING FINISHED ---")
        print(f"Successfully processed: {success_count}")
        print(f"Failed to process:     {fail_count}")
        print("="*50)

    # --- SINGLE URL MODE: Argument is not a .json file ---
    else:
        print(f"--- Running in SINGLE URL mode ---")
        url_to_scrape = argument
        try:
            # Run the main function
            process_url(url_to_scrape)
            
            # If it gets here, everything worked
            print("\n" + "="*50)
            print("--- SCRIPT FINISHED SUCCESSFULLY ---")
            print("="*50)
            
        except requests.exceptions.HTTPError as e:
            print("\n" + "="*50)
            print("--- SCRIPT FAILED ---")
            print(f"An HTTP error occurred: {e}")
            print("The website might be down, or it blocked the request (e.g., 403 Forbidden, 404 Not Found).")
            print("="*50)
            sys.exit(1)
            
        except requests.exceptions.RequestException as e:
            print("\n" + "="*50)
            print("--- SCRIPT FAILED ---")
            print(f"A network error occurred: {e}")
            print("Check your internet connection or the URL.")
            print("="*50)
            sys.exit(1)
            
        except (ValueError, AttributeError) as e:
            print("\n" + "="*50)
            print("--- SCRIPT FAILED ---")
            print(f"A parsing error occurred: {e}")
            print("This usually means the website's HTML structure has changed,")
            print("and the script couldn't find the required elements (like 'sku', 'price', etc.).")
            print("="*50)
            sys.exit(1)
            
        except Exception as e:
            # Catch-all for any other unexpected errors
            print("\n" + "="*50)
            print("--- SCRIPT FAILED ---")
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc() # Print detailed error info
            print("="*50)
            sys.exit(1)
