import agentql
from playwright.sync_api import sync_playwright
import time
import requests
from bs4 import BeautifulSoup
import sqlite3

# Database setup
DB_NAME = "alcohol_products.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS alcohol_products (
    source TEXT,
    product_name TEXT UNIQUE,
    type TEXT,
    subtype TEXT,
    brand TEXT,
    abv TEXT,
    price TEXT,
    volume_packaging TEXT
);
"""

INSERT_SQL = """
INSERT OR IGNORE INTO alcohol_products (source, product_name, type, subtype, brand, abv, price, volume_packaging)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

def get_last_processed_product(cursor):
    """Get the name of the last product in the database"""
    cursor.execute("SELECT source FROM alcohol_products ORDER BY ROWID DESC LIMIT 1")
    result = cursor.fetchone()
    return result[0] if result else None

def get_total_products_processed(cursor):
    """Get total count of products in database"""
    cursor.execute("SELECT COUNT(*) FROM alcohol_products")
    return cursor.fetchone()[0]


def get_product_links_generator(base_url, last_url=None):
    """Generator function that yields product links one at a time"""
    current_url = base_url
    processed_links = set()
    found_last_product = last_url is None
    
    while current_url:
        print(f"\nFetching products from: {current_url}")
        try:
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get product links from current page
            for element in soup.find_all(attrs={'data-href': True}):
                link = base_url.split("/search")[0] + element['data-href']
                if link not in processed_links:
                    processed_links.add(link)
                    
                    # If we're looking for the last processed URL and haven't found it yet
                    if not found_last_product:
                        if link == last_url:
                            found_last_product = True
                            print(f"Found last processed URL: {link}")
                        continue  # Skip until we find the last processed URL
                    
                    yield [link, current_url]
            
            # Get current page number from URL
            current_page_num = 1
            if "/page/" in current_url:
                current_page_num = int(current_url.split("/page/")[1])
            
            # Find next page link
            next_page = None
            pagination_items = soup.find_all('li', class_='page-item0')
            
            for item in pagination_items:
                link = item.find('a', class_='page-link')
                if link and link.text.strip().isdigit():
                    page_num = int(link.text.strip())
                    if page_num == current_page_num + 1:
                        next_page = base_url.split("/search")[0] + link['href']
                        print(f"Found next page: {next_page}")
                        break
            
            current_url = next_page
            if current_url:
                print(f"Moving to page {current_page_num + 1}")
                time.sleep(1)
            else:
                print("No more pages found")
                
        except requests.RequestException as e:
            print(f"Error fetching page {current_url}: {e}")
            break

def main():
    URL = "https://www.allendalewine.com/search/categories/Wine"
    alc_info = """
    {
        product_data[] {
            product_name
            category
            brand
            alcohol_by_volume
            price
            volume_or_packaging(num bottles/cans and volume or volume of bottle sold)
        }
    }
    """
    
    # Connect to SQLite and create table
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    
    # Get last processed product and total count
    last_product = get_last_processed_product(cursor)
    total_processed = get_total_products_processed(cursor)
    
    if last_product:
        print(f"Resuming from after product: {last_product}")
        print(f"Total products processed so far: {total_processed}")
    else:
        print("Starting fresh scrape")
    
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = agentql.wrap(browser.new_page())
            
            first_item = True
            session_processed = 0
            
            # Process links one at a time
            
            for result in get_product_links_generator(URL, last_product):
                try:
                    page.goto(result[0])
                    if first_item:
                        input("Please complete the verification and close any popups manually, then press Enter to continue...")
                        first_item = False
                    
                    print(f"\nProcessing product {total_processed + session_processed + 1}: {result[0]}")
                    info = page.query_data(alc_info)["product_data"][0]
                    
                    # Print the data that would be stored
                    print("\nExtracted Data:")
                    print(f"Product Name: {info['product_name']}")
                    print(f"Category: {info['category']}")
                    print(f"Brand: {info['brand']}")
                    print(f"ABV: {info['alcohol_by_volume']}")
                    print(f"Price: {info['price']}")
                    print(f"Volume/Packaging: {info['volume_or_packaging']}")
                    print("-" * 50)
                    
                    # Store data in database
                    cursor.execute(INSERT_SQL, (
                        result[1],
                        info["product_name"],
                        "wine",
                        info["category"],
                        info["brand"],
                        info["alcohol_by_volume"],
                        info["price"],
                        info["volume_or_packaging"]
                    ))
                    conn.commit()
                    
                    session_processed += 1
                    
                except Exception as e:
                    print(f"Error processing product {link}: {e}")
                    continue
                
            final_total = get_total_products_processed(cursor)
            print(f"\nSession summary:")
            print(f"Products processed this session: {session_processed}")
            print(f"Total products in database: {final_total}")
            
    except Exception as e:
        print(f"Error in main process: {e}")
    
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()