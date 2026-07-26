# jumia_scraper_MAX_PRODUCTS.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import re
import json

BASE_URL = "https://www.jumia.co.ke"
CATEGORY_URL = "https://www.jumia.co.ke/catalog/?q=smartphones"

#  CONFIGURATION 
MAX_PAGES = 10 
MAX_PRODUCTS = 500 
OUTPUT_FILE = "jumia_kenya_smartphones_bulk.csv"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# List of valid smartphone brands
SMARTPHONE_BRANDS = ['XIAOMI', 'SAMSUNG', 'TECNO', 'INFINIX', 'OPPO', 'HONOR', 'NOKIA', 
                     'POCO', 'VIVO', 'ITEL', 'SAFARICOM', 'REDMI', 'APPLE', 'GOOGLE', 
                     'ONEPLUS', 'REALME', 'MOTOROLA', 'LG', 'SONY', 'HTC', 'ASUS']

# Keywords to identify non-smartphone products
NON_SMARTPHONE_KEYWORDS = ['powerbank', 'charger', 'earphone', 'headset', 'adapter', 
                           'holder', 'stand', 'watch', 'cable', 'case', 'cover', 
                           'protector', 'screen guard', 'battery', 'speaker', 
                           'earbuds', 'headphones', 'usb', 'cable', 'charger']

def get_page_content(url):
    """Fetch page content with retry logic"""
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            print(f" Success! Status: {response.status_code}")
            return response.text
        else:
            print(f" Failed! Status: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f" Connection error: {e}")
        return None

def is_smartphone(product_name, brand):
    
    if not product_name or product_name == 'N/A':
        return False
    
    product_lower = product_name.lower()
    
    # Check for non-smartphone keywords
    for keyword in NON_SMARTPHONE_KEYWORDS:
        if keyword in product_lower:
            return False
    
    # Check if it has smartphone characteristics
    smartphone_indicators = ['gb', 'ram', 'mp', 'camera', 'display', 'screen', 
                            'android', '5g', '4g', 'dual sim', 'smartphone',
                            'inch', '"', 'amoled', 'lcd', 'oled', 'snapdragon',
                            'mediatek', 'processor', 'fingerprint', 'face unlock']
    
    has_indicator = any(indicator in product_lower for indicator in smartphone_indicators)
    
    # Check if brand is a known smartphone brand
    is_brand = brand.upper() in SMARTPHONE_BRANDS or brand in SMARTPHONE_BRANDS
    
    return has_indicator or is_brand

def extract_brand_from_name(product_name):

    brands = ['XIAOMI', 'SAMSUNG', 'TECNO', 'INFINIX', 'OPPO', 'HONOR', 'NOKIA', 
              'POCO', 'VIVO', 'ITEL', 'SAFARICOM', 'OKING', 'RUIOO', 'SIMI', 
              'AGM', 'REDMI', 'APPLE', 'GOOGLE', 'ONEPLUS', 'REALME', 'MOTOROLA',
              'LG', 'SONY', 'HTC', 'ASUS', 'LANDVO', 'LESIA', 'ORAI', 'VIC']
    
    if not product_name or product_name == 'N/A':
        return 'Unknown'
    
    product_upper = product_name.upper()
    for brand in brands:
        if brand in product_upper:
            return brand.title()
    
    # If no brand found, try first word
    first_word = product_name.split()[0].upper()
    if len(first_word) > 1 and first_word not in ['BY', 'FOR', 'WITH', 'AND', 'THE']:
        return first_word.title()
    
    return 'Unknown'

def extract_product_data(product_card):
    
    try:
        # 1. Product Name
        name = 'N/A'
        name_elem = product_card.find('h3', class_='name')
        if not name_elem:
            name_elem = product_card.find('h3')
        if name_elem:
            name = name_elem.text.strip()
        
        # 2. Brand
        brand = extract_brand_from_name(name)
        
        # 3. Current Price
        current_price = None
        price_elem = product_card.find('div', class_='prc')
        if not price_elem:
            price_elem = product_card.find('span', class_='prc')
        if not price_elem:
            price_elem = product_card.find('div', class_='price')
        
        if price_elem:
            price_text = price_elem.text.strip()
            price_text = re.sub(r'[KSh\s,]+', '', price_text).strip()
            price_match = re.search(r'(\d+\.?\d*)', price_text)
            if price_match:
                try:
                    current_price = float(price_match.group(1))
                except:
                    current_price = None
        
        # 4. Original Price
        original_price = None
        old_price_elem = product_card.find('div', class_='old')
        if not old_price_elem:
            old_price_elem = product_card.find('span', class_='old')
        
        if old_price_elem:
            old_price_text = old_price_elem.text.strip()
            old_price_text = re.sub(r'[KSh\s,]+', '', old_price_text).strip()
            price_match = re.search(r'(\d+\.?\d*)', old_price_text)
            if price_match:
                try:
                    original_price = float(price_match.group(1))
                except:
                    original_price = None
        
        # 5. Discount Percentage
        discount = 0.0
        if original_price and current_price and original_price > 0:
            discount = round(((original_price - current_price) / original_price) * 100, 1)
        
        # 6. Rating - Multiple extraction methods
        rating = None
        
        #  Check for data-rating attribute
        rating_container = product_card.find('div', class_='stars')
        if rating_container:
            rating_attr = rating_container.get('data-rating', '')
            if rating_attr:
                try:
                    rating = float(rating_attr)
                except:
                    pass
            
            #  Count filled stars
            if rating is None:
                filled_stars = rating_container.find_all('i', class_='ic-star')
                if filled_stars:
                    rating = float(len(filled_stars))
        
        #  Look for rating in text
        if rating is None:
            rating_elements = product_card.find_all(['span', 'div'], class_=re.compile(r'rating|stars|_rating'))
            for elem in rating_elements:
                rating_text = elem.text.strip()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        break
                    except:
                        pass
        
        # 7. Review Count
        review_count = 0
        review_selectors = [
            ('span', '_more'),
            ('span', 'reviews'),
            ('div', 'reviews'),
            ('span', 'rating'),
            ('div', '_reviews'),
            ('span', 'rev')
        ]
        
        for tag, class_name in review_selectors:
            reviews_elem = product_card.find(tag, class_=class_name)
            if reviews_elem:
                reviews_text = reviews_elem.text.strip()
                numbers = re.findall(r'\d+', reviews_text)
                if numbers:
                    try:
                        review_count = int(numbers[0])
                        break
                    except:
                        pass
        
        # 8. Product URL
        product_url = 'N/A'
        link_elem = product_card.find('a', class_='core')
        if not link_elem:
            link_elem = product_card.find('a', href=True)
        
        if link_elem and link_elem.get('href'):
            product_url = link_elem.get('href')
            if product_url and not product_url.startswith('http'):
                product_url = BASE_URL + product_url
        
        # Return as a dictionary
        return {
            'product_name': name,
            'brand': brand,
            'current_price_kes': current_price,
            'original_price_kes': original_price,
            'discount_percentage': discount,
            'rating': rating,
            'review_count': review_count,
            'product_url': product_url,
            'is_smartphone': is_smartphone(name, brand),
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        print(f" Error extracting product data: {e}")
        return None

def get_total_pages(soup):
    """Try to extract total number of pages from pagination"""
    try:
        # Look for pagination elements
        pagination = soup.find('div', class_='pagination')
        if pagination:
            page_links = pagination.find_all('a')
            if page_links:
                # Get the last page number
                for link in reversed(page_links):
                    page_text = link.text.strip()
                    if page_text.isdigit():
                        return int(page_text)
        
        
        page_info = soup.find('span', class_=re.compile(r'page|pagination'))
        if page_info:
            numbers = re.findall(r'(\d+)', page_info.text)
            if len(numbers) >= 2:
                return int(numbers[-1])
    except:
        pass
    
    return None

def scrape_category_pages(base_url, max_pages, max_products):
    """Scrape multiple pages from a category until reaching max_products"""
    all_products = []
    page_num = 1
    total_pages = None
    
    while page_num <= max_pages and len(all_products) < max_products:
        print(f"\n{'='*60}")
        print(f" Scraping Page {page_num} of {max_pages if max_pages else '?'}")
        print(f" Collected: {len(all_products)} / {max_products} products")
        print(f"{'='*60}")
        
        # correct pagination
        if page_num == 1:
            page_url = base_url
        else:
            if '?' in base_url:
                page_url = f"{base_url}&page={page_num}"
            else:
                page_url = f"{base_url}?page={page_num}"
        
        # Fetch the page content
        html = get_page_content(page_url)
        if not html:
            print(f" Failed to fetch page {page_num}, stopping...")
            break
        
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # get total pages on first page
        if page_num == 1 and total_pages is None:
            total_pages = get_total_pages(soup)
            if total_pages:
                print(f" Found {total_pages} total pages available")
                if total_pages < max_pages:
                    max_pages = total_pages
        
        # Find all product cards
        product_cards = []
        selectors = ['article.prd', 'article._prd', 'div.prd', 'div._prd']
        
        for selector in selectors:
            product_cards = soup.select(selector)
            if product_cards:
                print(f" Found products with selector: {selector}")
                break
        
        if not product_cards:
            print(" No products found on this page. Stopping...")
            break
        
        print(f" Found {len(product_cards)} products on page {page_num}")
        
        # Extract data from each product
        success_count = 0
        smartphone_count = 0
        
        for idx, card in enumerate(product_cards, 1):
            # Check if we've reached the target
            if len(all_products) >= max_products:
                print(f"\n Reached target of {max_products} products!")
                break
            
            print(f"  Extracting product {idx}/{len(product_cards)}...", end=' ')
            product_data = extract_product_data(card)
            
            if product_data and product_data['current_price_kes'] is not None:
                # Only add if it's a smartphone
                if product_data['is_smartphone']:
                    all_products.append(product_data)
                    success_count += 1
                    smartphone_count += 1
                    print(f" Smartphone #{len(all_products)}: {product_data['brand']} - KSh{product_data['current_price_kes']}")
                else:
                    print(f" Filtered out: {product_data['brand']} (accessory)")
            else:
                print(f" Skipped (no price data)")
            
            # Polite delay between products
            if idx < len(product_cards) and len(all_products) < max_products:
                time.sleep(random.uniform(0.3, 0.8))
        
        print(f" Page {page_num}: {smartphone_count} smartphones collected")
        print(f" Total so far: {len(all_products)} / {max_products}")
        
        # Check if we've reached the target
        if len(all_products) >= max_products:
            print(f"\n Target reached! Stopping.")
            break
        
        # Check if there are more pages
        if total_pages and page_num >= total_pages:
            print(f" Reached last page ({total_pages}). Stopping.")
            break
        
        # Longer delay between pages
        if page_num < max_pages:
            delay = random.uniform(3, 6)
            print(f" Waiting {delay:.1f} seconds before next page...")
            time.sleep(delay)
        
        page_num += 1
    
    return all_products

def main():
    print("=" * 60)
    print(" JUMIA KENYA SMARTPHONE SCRAPER (BULK MODE)")
    print("=" * 60)
    print(f" Target: {CATEGORY_URL}")
    print(f" Max Pages: {MAX_PAGES}")
    print(f" Target Products: {MAX_PRODUCTS}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Scrape the products
    products = scrape_category_pages(CATEGORY_URL, MAX_PAGES, MAX_PRODUCTS)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f" SCRAPING COMPLETE!")
    print(f" Time taken: {elapsed_time:.1f} seconds")
    print(f" Total products scraped: {len(products)}")
    print(f"{'='*60}")
    
    if products:
        # Convert to DataFrame
        df = pd.DataFrame(products)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['product_url'])
        
        # Filter to only smartphones
        df_smartphones = df[df['is_smartphone'] == True].copy()
        
        print(f"\n Data Summary:")
        print(f"  - Total products scraped: {len(df)}")
        print(f"  - Smartphones: {len(df_smartphones)}")
        print(f"  - Filtered out (accessories): {len(df) - len(df_smartphones)}")
        
        if len(df_smartphones) > 0:
            print("\n Statistics for Smartphones:")
            print(f"  - Price Range: KSh {df_smartphones['current_price_kes'].min():.0f} - KSh {df_smartphones['current_price_kes'].max():.0f}")
            print(f"  - Average Price: KSh {df_smartphones['current_price_kes'].mean():.2f}")
            print(f"  - Median Price: KSh {df_smartphones['current_price_kes'].median():.2f}")
            
            if df_smartphones['discount_percentage'].notna().any():
                print(f"\n  - Average Discount: {df_smartphones['discount_percentage'].mean():.1f}%")
                products_with_discount = len(df_smartphones[df_smartphones['discount_percentage'] > 0])
                print(f"  - Products with Discount: {products_with_discount} ({products_with_discount/len(df_smartphones)*100:.1f}%)")
                print(f"  - Max Discount: {df_smartphones['discount_percentage'].max():.1f}%")
            
            if df_smartphones['rating'].notna().any():
                rated_products = df_smartphones['rating'].notna().sum()
                print(f"\n  - Products with Rating: {rated_products} ({rated_products/len(df_smartphones)*100:.1f}%)")
                print(f"  - Average Rating: {df_smartphones['rating'].mean():.2f}")
                print(f"  - Max Rating: {df_smartphones['rating'].max():.1f}")
            
            if df_smartphones['review_count'].sum() > 0:
                print(f"\n  - Total Reviews: {df_smartphones['review_count'].sum():,}")
                print(f"  - Average Reviews: {df_smartphones['review_count'].mean():.0f}")
            
            print(f"\n  - Unique Brands: {df_smartphones['brand'].nunique()}")
            print(f"\n  - Top 10 Brands:")
            for brand, count in df_smartphones['brand'].value_counts().head(10).items():
                print(f"    {brand}: {count} ({count/len(df_smartphones)*100:.1f}%)")
            
            # Save to CSV
            df_smartphones.to_csv(OUTPUT_FILE, index=False)
            print(f"\n Data saved to: {OUTPUT_FILE}")
            
            print(f"\n Data size: {len(df_smartphones)} smartphones exported")
            
            return df_smartphones
        else:
            print("\n No smartphones found in the scraped data.")
            return None
    else:
        print("\n No products scraped.")
        return None

if __name__ == "__main__":
    main()