# Alcohol Database Creation project

This project implements web scrapers for collecting alcohol product information using AgentQL, Playwright, and SQLite. The scraper is designed to extract detailed product information and store it in a structured database.

## Features

- Automated scraping of wine product information
- Persistent storage in SQLite database
- Resume capability from last processed product
- Duplicate product detection and prevention
- Automatic pagination handling
- Manual verification bypass support

## Prerequisites

- Python 3.x
- AgentQL
- Playwright
- Beautiful Soup 4
- SQLite3
- Requests

## Installation

1. Clone the repository
2. Install required dependencies:
```bash
pip install agentql playwright beautifulsoup4 requests
```
3. Install Playwright browsers:
```bash
playwright install
```

## Database Schema

The scraper stores data in an SQLite database with the following structure:

```sql
CREATE TABLE alcohol_products (
    source TEXT,
    product_name TEXT UNIQUE,
    type TEXT,
    subtype TEXT,
    brand TEXT,
    abv TEXT,
    price TEXT,
    volume_packaging TEXT
);
```

## Usage

There are two main scraper implementations:

### Basic Scraper (AgentQLTest.py)
- Basic implementation without resume capability
- Supports skipping specific product ranges
- Run with:
```bash
python AgentQLTest.py
```

### Enhanced Scraper (AllendaleScraper.py)
- Includes resume capability
- Handles duplicates
- Maintains session statistics
- Run with:
```bash
python AllendaleScraper.py
```

On first run, you'll need to:
1. Complete any CAPTCHA or verification manually
2. Close any popups that appear
3. Press Enter in the terminal to continue scraping

## Features in Detail

### Product Information Extraction
The scraper collects the following information for each product:
- Product name
- Category/Type
- Brand
- Alcohol by volume (ABV)
- Price
- Volume/Packaging information

### Error Handling
- Graceful handling of network errors
- Skip and continue on product processing failures
- Database transaction management

### Rate Limiting
- Built-in delays between page requests
- Configurable timing to prevent server overload

## Notes

- The scraper uses a headless browser but launches in visible mode for manual verification
- Products are uniquely identified by name to prevent duplicates
- Progress is logged to the console during execution
- The database connection is properly closed even if errors occur

## Limitations

- Requires manual CAPTCHA/verification handling on first run
- Depends on specific website structure
- May need adjustments if website layout changes

## Contributing

Feel free to submit issues and enhancement requests.