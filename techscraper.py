

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime
import os

# CONFIGURATION

BASE_URL = "https://www.jumia.co.ke"
OUTPUT_FILE = "jumia_tech_products_full_v2.csv"


# TECHNOLOGY CATEGORIES


CATEGORIES = {
    "smartphones": {"url": "https://www.jumia.co.ke/smartphones/", "pages": 10},
    "laptops": {"url": "https://www.jumia.co.ke/laptops/", "pages": 8},
    "tablets": {"url": "https://www.jumia.co.ke/tablets/", "pages": 5},
    "headphones": {"url": "https://www.jumia.co.ke/headphones/", "pages": 5},
    "televisions": {"url": "https://www.jumia.co.ke/televisions/", "pages": 5},
    "smart-watches": {"url": "https://www.jumia.co.ke/smart-watches/", "pages": 4},
    "gaming": {"url": "https://www.jumia.co.ke/gaming/", "pages": 3},
    "power-banks": {"url": "https://www.jumia.co.ke/power-banks/", "pages": 3}
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


# HELPER FUNCTIONS


def get_page_content(url):

    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"   Error: {e}")
        return None

def clean_price(price_text):

    if not price_text:
        return None
    price = price_text.replace('KSh', '').replace(',', '').strip()
    try:
        return float(price)
    except:
        return None

def extract_specs(product_name):

    specs = {
        'storage': None,
        'ram': None,
        'battery': None,
        'camera': None
    }
    
    if not product_name:
        return specs
    
    # Storage 
    storage_patterns = [
        r'(\d+)\s*GB\s*(?:ROM|Storage|storage|Rom|rom)',
        r'(\d+)\s*GB\s*(?:,|\s|\))',
    ]
    for pattern in storage_patterns:
        match = re.search(pattern, str(product_name))
        if match:
            try:
                specs['storage'] = int(match.group(1))
                break
            except:
                pass

    if not specs['storage']:
        match = re.search(r'(\d+)\s*GB', str(product_name))
        if match:
            try:
                val = int(match.group(1))
                
                if not re.search(r'(\d+)\s*GB\s*RAM', str(product_name), re.IGNORECASE):
                    specs['storage'] = val
            except:
                pass
    
    # RAM 
    ram_patterns = [
        r'(\d+)\s*GB\s*(?:RAM|Ram|ram)',
        r'(\d+)\s*GB\s*RAM',
    ]
    for pattern in ram_patterns:
        match = re.search(pattern, str(product_name))
        if match:
            try:
                specs['ram'] = int(match.group(1))
                break
            except:
                pass
    
    # Battery
    match = re.search(r'(\d+)\s*mAh', str(product_name), re.IGNORECASE)
    if match:
        try:
            specs['battery'] = int(match.group(1))
        except:
            pass
    
    # Camera
    match = re.search(r'(\d+)\s*MP', str(product_name), re.IGNORECASE)
    if match:
        try:
            specs['camera'] = int(match.group(1))
        except:
            pass
    
    return specs

def extract_product_data(product_card, category):

    try:

        # PRODUCT NAME
    
        name_elem = product_card.find('h3', class_='name')
        name = name_elem.text.strip() if name_elem else None
        if not name:
            return None
        
        # Clean product name
        name = re.sub(r'\s+', ' ', name).strip()
        

        # BRAND
    
        img_elem = product_card.find('img', class_='img')
        brand = img_elem.get('alt', '').strip() if img_elem else None
        if not brand or brand == '':
            brand = name.split()[0] if name else 'Unknown'
        
        
        # PRICE (Current)
        
        price_elem = product_card.find('div', class_='prc')
        current_price = clean_price(price_elem.text) if price_elem else None
        

        # ORIGINAL PRICE 

        old_price_elem = product_card.find('div', class_='old')
        original_price = clean_price(old_price_elem.text) if old_price_elem else None
        

        # DISCOUNT PERCENTAGE
    
        if original_price and current_price and original_price > 0:
            discount = round(((original_price - current_price) / original_price) * 100, 1)
        else:
            discount = 0.0
        

        # RATING 
        rating = None
        rating_elem = product_card.find('div', class_='stars')
        if rating_elem:
            # Try data-rating attribute first
            rating_text = rating_elem.get('data-rating', '')
            if rating_text:
                try:
                    rating = float(rating_text)
                except:
                    pass
            
            # If that fails, try to extract from the stars div text
            if not rating:
                # Look for pattern like "4.5" in the text
                stars_text = rating_elem.text.strip()
                match = re.search(r'(\d+\.?\d*)', stars_text)
                if match:
                    try:
                        rating = float(match.group(1))
                    except:
                        pass
        
        if not rating:
            parent = product_card.find('div', class_='info')
            if parent:
                rating_elem = parent.find('div', class_='stars')
                if rating_elem:
                    rating_text = rating_elem.get('data-rating', '')
                    if rating_text:
                        try:
                            rating = float(rating_text)
                        except:
                            pass
        
        # REVIEW COUNT
    
        review_count = 0
        
        reviews_elem = product_card.find('span', class_='_more')
        if reviews_elem:
            reviews_text = reviews_elem.text.strip()
            numbers = re.findall(r'\d+', reviews_text)
            if numbers:
                review_count = int(numbers[0])
        else:

            reviews_elem = product_card.find('div', class_='reviews')
            if reviews_elem:
                reviews_text = reviews_elem.text.strip()
                numbers = re.findall(r'\d+', reviews_text)
                if numbers:
                    review_count = int(numbers[0])
            
            
            if not review_count:
                info_elem = product_card.find('div', class_='info')
                if info_elem:
                    reviews_elem = info_elem.find('span', class_='_more')
                    if reviews_elem:
                        reviews_text = reviews_elem.text.strip()
                        numbers = re.findall(r'\d+', reviews_text)
                        if numbers:
                            review_count = int(numbers[0])
        

        # PRODUCT URL
    
        link_elem = product_card.find('a', class_='core')
        if link_elem:
            product_url = link_elem.get('href')
            if product_url and not product_url.startswith('http'):
                product_url = BASE_URL + product_url
        else:
            product_url = None
        

        # EXTRACT SPECIFICATIONS
        
        specs = extract_specs(name)
        
    
        # RETURN DATA
    
        return {
            'Category': category,
            'Product Name': name,
            'Brand': brand,
            'Price (KSh)': current_price,
            'Original Price (KSh)': original_price,
            'Discount %': discount,
            'High Discount Flag': discount >= 60,
            'Rating': rating,
            'Review Count': review_count,
            'Product URL': product_url,
            'Scraped Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Storage (GB)': specs.get('storage'),
            'RAM (GB)': specs.get('ram'),
            'Battery (mAh)': specs.get('battery'),
            'Camera (MP)': specs.get('camera')
        }
    
    except Exception as e:
        print(f"   Error extracting product: {e}")
        return None

def scrape_category(category_name, category_url, max_pages):
    """Scrape a single category"""
    print(f"\n{'='*60}")
    print(f" Scraping Category: {category_name.upper()}")
    print(f"   URL: {category_url}")
    print(f"   Pages: {max_pages}")
    print(f"{'='*60}")
    
    all_products = []
    
    for page_num in range(1, max_pages + 1):
        print(f"\n   Page {page_num} of {max_pages}")
        
        # Build page URL
        if page_num == 1:
            page_url = category_url
        else:
            page_url = category_url + f"?page={page_num}"
        
        # Fetch page
        html = get_page_content(page_url)
        if not html:
            print(f"   Failed to fetch page {page_num}, stopping...")
            break
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find product cards
        product_cards = soup.find_all('article', class_='prd')
        
        if not product_cards:
            product_cards = soup.find_all('div', class_='prd')
            if not product_cards:
                print(f"   No products found on page {page_num}")
                break
        
        print(f"   Found {len(product_cards)} products on page {page_num}")
        
        # Extract products
        for idx, card in enumerate(product_cards, 1):
            print(f"    Extracting product {idx}/{len(product_cards)}...")
            product_data = extract_product_data(card, category_name)
            if product_data:
                all_products.append(product_data)
            
            # Polite delay between products
            time.sleep(random.uniform(0.3, 0.8))
        
        # Delay between pages
        if page_num < max_pages:
            delay = random.uniform(3, 6)
            print(f"   Waiting {delay:.1f}s before next page...")
            time.sleep(delay)
    
    print(f"\n   Scraped {len(all_products)} products from {category_name}")
    return all_products


# MAIN


def main():
    print("=" * 70)
    print("   JUMIA KENYA - ENHANCED TECHNOLOGY SCRAPER V2")
    print("   Proper Rating & Review Extraction")
    print("=" * 70)
    
    all_products = []
    total_estimated = sum(cat['pages'] * 25 for cat in CATEGORIES.values())
    print(f"\n Categories: {len(CATEGORIES)}")
    print(f" Estimated Products: ~{total_estimated}")
    print()
    
    for category_name, category_info in CATEGORIES.items():
        products = scrape_category(
            category_name,
            category_info['url'],
            category_info['pages']
        )
        all_products.extend(products)
        print(f"\n Progress: {len(all_products)} products scraped so far")
    
    # SAVE TO CSV
    
    
    print("\n" + "=" * 70)
    print(" SAVING RESULTS")
    print("=" * 70)
    
    if all_products:
        df = pd.DataFrame(all_products)
        
        # Add calculated columns
        def get_rating_category(rating):
            if rating is None or rating == 0:
                return 'No Rating'
            elif rating >= 4.5:
                return 'Excellent'
            elif rating >= 3.5:
                return 'Good'
            elif rating >= 2.5:
                return 'Average'
            else:
                return 'Poor'
        
        def get_price_category(price):
            if price is None or price == 0:
                return 'Price Unavailable'
            elif price < 5000:
                return 'Budget (<5k)'
            elif price < 15000:
                return 'Entry (5k-15k)'
            elif price < 30000:
                return 'Mid-Range (15k-30k)'
            elif price < 50000:
                return 'Premium (30k-50k)'
            else:
                return 'Luxury (>50k)'
        
        def calculate_value_score(row):
            rating = row.get('Rating', 0) or 0
            discount = row.get('Discount %', 0) or 0
            reviews = row.get('Review Count', 0) or 0
            
            score = (rating / 5) * 0.5 + (discount / 100) * 0.3 + (reviews / 100) * 0.2
            return round(score, 3)
        
        df['Rating Category'] = df['Rating'].apply(get_rating_category)
        df['Price Category'] = df['Price (KSh)'].apply(get_price_category)
        df['Value Score'] = df.apply(calculate_value_score, axis=1)
        
        # Save to CSV
        df.to_csv(OUTPUT_FILE, index=False)
        
        print(f"\n SUCCESS! Saved {len(df)} products to:")
        print(f"   {OUTPUT_FILE}")
        
        
        # SUMMARY STATISTICS
        
        
        print("\n" + "=" * 70)
        print(" SUMMARY STATISTICS")
        print("=" * 70)
        
        print(f"\n Total Products: {len(df)}")
        print(f" Categories: {df['Category'].nunique()}")
        print(f" Brands: {df['Brand'].nunique()}")
        
        valid_prices = df[df['Price (KSh)'] > 0]
        if len(valid_prices) > 0:
            print(f"\n Price Range: KSh {valid_prices['Price (KSh)'].min():,.0f} - KSh {valid_prices['Price (KSh)'].max():,.0f}")
            print(f" Average Price: KSh {valid_prices['Price (KSh)'].mean():,.0f}")
        
        valid_ratings = df[df['Rating'] > 0]
        if len(valid_ratings) > 0:
            print(f"\n Average Rating: {valid_ratings['Rating'].mean():.2f}")
            print(f" Max Rating: {valid_ratings['Rating'].max():.2f}")
            print(f" Min Rating: {valid_ratings['Rating'].min():.2f}")
            print(f" Products with Ratings: {len(valid_ratings)}")
        else:
            print(f"\n No ratings extracted. Check the extraction logic.")
        
        print(f"\n Average Discount: {df['Discount %'].mean():.1f}%")
        print(f" Max Discount: {df['Discount %'].max():.1f}%")
        
        print("\n Products by Category:")
        print(df['Category'].value_counts().to_string())
        
        print("\n Products by Rating Category:")
        print(df['Rating Category'].value_counts().to_string())
        
        print("\n Products by Price Category:")
        print(df['Price Category'].value_counts().to_string())
        
        print("\n Products with High Discount (>60%):")
        print(f"   {df['High Discount Flag'].sum()} products")
        
        # Show sample with ratings
        print("\n Sample Products with Ratings:")
        sample = df[df['Rating'] > 0].head(10)
        if len(sample) > 0:
            for _, row in sample.iterrows():
                print(f"  {row['Product Name'][:40]:40} | {row['Rating']:3.1f}⭐ | {row['Discount %']:5.1f}% | {row['Category']}")
        else:
            print("  No ratings found. Check the scraping logic.")
        
        print("\n" + "=" * 70)
        print(" SCRAPING COMPLETE!")
        print("   Data saved to: " + OUTPUT_FILE)
        print("=" * 70)
        
        return df
    else:
        print("\n No products scraped. Please check:")
        print("   1. Your internet connection")
        print("   2. Jumia Kenya is accessible")
        print("   3. The website structure hasn't changed")
        return None

if __name__ == "__main__":
    df = main()