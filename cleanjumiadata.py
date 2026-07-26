# clean_jumia_data_fixed.py

import pandas as pd
import re
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Load the data
df = pd.read_csv('jumia_kenya_smartphones_bulk.csv')

print("="*60)
print(" STARTING DATA CLEANING")
print("="*60)
print(f"Initial rows: {len(df)}")


# 1. FILTER OUT NON-SMARTPHONES


# Keywords that indicate non-smartphone products
non_smartphone_keywords = [
    'screen', 'display', 'lcd', 'touch', 'glass', 'repair', 'part', 'parts',
    'tester', 'magnifier', 'stand', 'holder', 'cable', 'charger', 'adapter',
    'powerbank', 'earphone', 'headset', 'speaker', 'watch', 'smartwatch',
    'case', 'cover', 'protector', 'memory card', 'sim card', 'usb',
    'test', 'digitizer', 'assembly'
]

# Also filter out products that are clearly not smartphones
def is_actual_smartphone(row):
    """More strict smartphone filtering"""
    product_name = str(row['product_name']).lower()
    brand = str(row['brand']).lower()
    product_url = str(row['product_url']).lower()
    
    # Check for non-smartphone keywords
    for keyword in non_smartphone_keywords:
        if keyword in product_name:
            return False
    
    # Must have smartphone characteristics
    phone_indicators = ['gb', 'ram', 'mp', 'camera', 'display', 'screen', 
                       'android', '5g', '4g', 'dual sim', 'smartphone',
                       'inch', '"', 'amoled', 'lcd', 'oled', 'mobile phone',
                       'cell phone', 'feature phone']
    
    has_indicator = any(ind in product_name for ind in phone_indicators)
    
    # Known smartphone brands
    smartphone_brands = ['xiaomi', 'samsung', 'tecno', 'infinix', 'oppo', 
                        'honor', 'nokia', 'poco', 'vivo', 'itel', 'redmi',
                        'apple', 'google', 'oneplus', 'realme', 'motorola',
                        'huawei', 'agm', 'oukitel', 'simi', 'safaricom',
                        'ruioo', 'lesia', 'oking', 'villaon']
    
    is_brand = any(brand in b for b in smartphone_brands)
    
    # Must be a known brand or have smartphone indicators
    return is_brand or has_indicator

# Apply filter
df['is_actual_phone'] = df.apply(is_actual_smartphone, axis=1)
df_phones = df[df['is_actual_phone'] == True].copy()

print(f"After removing non-smartphones: {len(df_phones)} rows")


# 2. CLEAN BRAND NAMES


# Standardize brand names
brand_mapping = {
    'Xiaomi': 'Xiaomi',
    'Redmi': 'Xiaomi', 
    'Poco': 'Xiaomi',   
    'Samsung': 'Samsung',
    'Tecno': 'Tecno',
    'Infinix': 'Infinix',
    'Oppo': 'Oppo',
    'Honor': 'Honor',
    'Nokia': 'Nokia',
    'Vivo': 'Vivo',
    'Itel': 'Itel',
    'Safaricom': 'Safaricom',
    'Huawei': 'Huawei',
    'Apple': 'Apple',
    'Google': 'Google',
    'Motorola': 'Motorola',
    'Realme': 'Realme',
    'OnePlus': 'OnePlus',
    'Agm': 'AGM',
    'Oukitel': 'Oukitel',
    'Ruioo': 'Ruioo',
    'Simi': 'Simi',
    'Lesia': 'Lesia',
    'Oking': 'Oking',
    'Villaon': 'Villaon',
    'Jx': 'JX',
    'Corn': 'Corn',
    'Reno10': 'Reno',
    'A56': 'Unknown',
    'S26': 'Unknown',
    '11': 'Unknown',
    '13': 'Apple',  
    'Fahion': 'Unknown',
    'Koruima': 'Koruima',
    'Sq': 'SQ',
    'Mobile': 'Unknown',
    'Black': 'Unknown',
    'Touch': 'Unknown',
    'Latest': 'Unknown',
    '100%': 'Unknown'
}

df_phones['brand_clean'] = df_phones['brand'].map(brand_mapping).fillna(df_phones['brand'])

# Clean unknown brands
df_phones.loc[df_phones['brand_clean'].isin(['Unknown', 'N/A']), 'brand_clean'] = 'Other'


# 3. CLEAN PRODUCT NAMES


def clean_product_name(name):
    """Clean product name - remove extra text, warranty info, etc."""
    if pd.isna(name) or name == 'N/A':
        return 'Unknown Smartphone'
    
    # Remove warranty info
    name = re.sub(r'\(\d+\s*(Yr|YR|MONTHS?|WRTY|wrt|wty)[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\d+\s*(Yr|YR|MONTHS?|WRTY|wrt|wty)', '', name, flags=re.IGNORECASE)
    
    # Remove "By Xiaomi", "By Samsung"
    name = re.sub(r'By\s+\w+', '', name)
    
    # Remove "Free Gifts", "Free", "Gifts" etc.
    name = re.sub(r'\+?\s*(FREE|GIFT|GIFTS|WATCH|EARPODS|EARBUDS|POWERBANK|ADAPTER|COVER|PROTECTOR)[^,]*', '', name, flags=re.IGNORECASE)
    
    # Remove extra commas and spaces
    name = re.sub(r'\s*,+\s*', ', ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Remove trailing commas
    name = re.sub(r',\s*$', '', name)
    
    # Limit length
    if len(name) > 100:
        name = name[:97] + '...'
    
    return name if name else 'Unknown Smartphone'

df_phones['product_name_clean'] = df_phones['product_name'].apply(clean_product_name)


# 4. FIX DISCOUNTS (Cap unrealistic values)


# If original price is 0 or None, set discount to 0
df_phones.loc[df_phones['original_price_kes'].isna(), 'discount_percentage'] = 0

# Cap discounts at 80% (anything above is likely fake)
df_phones['discount_clean'] = df_phones['discount_percentage'].clip(upper=80)

# Flag suspicious discounts
df_phones['discount_flag'] = df_phones['discount_percentage'] > 70


# 5. HANDLE MISSING RATINGS

brand_avg_ratings = df_phones[df_phones['rating'].notna()].groupby('brand_clean')['rating'].mean()

def fill_missing_rating(row):
    if pd.isna(row['rating']) or row['rating'] == 0:
        avg = brand_avg_ratings.get(row['brand_clean'], np.nan)
        if pd.isna(avg):
        
            return df_phones['rating'].mean()
        return avg
    return row['rating']

df_phones['rating_clean'] = df_phones.apply(fill_missing_rating, axis=1)


# 6. PRICE CATEGORIES


def price_category(price):
    if pd.isna(price) or price == 0:
        return 'Unknown'
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

df_phones['price_category'] = df_phones['current_price_kes'].apply(price_category)


# 7. VALUE SCORE (Rating / Price)


# Normalize rating and price for value score
df_phones['value_score'] = (
    df_phones['rating_clean'] / (df_phones['current_price_kes'] / 1000)
)
df_phones['value_score'] = df_phones['value_score'].round(3)
df_phones['value_score'] = df_phones['value_score'].replace([np.inf, -np.inf], 0).fillna(0)


# 8. RATING CATEGORIES


def rating_category(rating):
    if pd.isna(rating) or rating == 0:
        return 'No Rating'
    elif rating < 2.5:
        return 'Poor'
    elif rating < 3.5:
        return 'Average'
    elif rating < 4.5:
        return 'Good'
    else:
        return 'Excellent'

df_phones['rating_category'] = df_phones['rating_clean'].apply(rating_category)


# 9. EXTRACT KEY SPECS


def extract_spec(product_name, pattern, default='N/A'):
    """Extract specification from product name using regex"""
    match = re.search(pattern, str(product_name), re.IGNORECASE)
    return match.group(1) if match else default

# Extract common specs
df_phones['storage'] = df_phones['product_name'].apply(
    lambda x: extract_spec(x, r'(\d+)\s*GB\s*(?:ROM|Storage|STORAGE|Rom)', 'N/A')
)

df_phones['ram'] = df_phones['product_name'].apply(
    lambda x: extract_spec(x, r'(\d+)\s*GB\s*RAM', 'N/A')
)

df_phones['battery'] = df_phones['product_name'].apply(
    lambda x: extract_spec(x, r'(\d+)\s*mAh', 'N/A')
)

df_phones['camera'] = df_phones['product_name'].apply(
    lambda x: extract_spec(x, r'(\d+)\s*MP', 'N/A')
)


# 10. FINAL CLEANUP


# Select final columns
final_columns = [
    'product_name_clean',
    'brand_clean',
    'current_price_kes',
    'original_price_kes',
    'discount_clean',
    'discount_flag',
    'rating_clean',
    'rating_category',
    'value_score',
    'price_category',
    'storage',
    'ram',
    'battery',
    'camera',
    'product_url',
    'scraped_at'
]

df_final = df_phones[final_columns].copy()

# Rename columns
df_final.columns = [
    'Product Name',
    'Brand',
    'Price (KSh)',
    'Original Price (KSh)',
    'Discount %',
    'High Discount Flag',
    'Rating',
    'Rating Category',
    'Value Score',
    'Price Category',
    'Storage (GB)',
    'RAM (GB)',
    'Battery (mAh)',
    'Camera (MP)',
    'Product URL',
    'Scraped Date'
]


# 11. REMOVE DUPLICATES


df_final = df_final.drop_duplicates(subset=['Product Name', 'Product URL'])


# 12. SORT AND SAVE


# Sort by rating (highest first)
df_final = df_final.sort_values('Rating', ascending=False)

print(f"\n Data cleaning complete!")
print(f"Final rows: {len(df_final)}")
print(f"Unique brands: {df_final['Brand'].nunique()}")

# Save cleaned data
df_final.to_csv('jumia_smartphones_cleaned.csv', index=False)

print("\n Saved file: jumia_smartphones_cleaned.csv")

#  save Excel
try:
    df_final.to_excel('jumia_smartphones_cleaned.xlsx', index=False)
    print(" Saved file: jumia_smartphones_cleaned.xlsx")
except ImportError:
    print("\n openpyxl not installed. Skipping Excel export.")
    print("   To install: pip install openpyxl")
except Exception as e:
    print(f"\n Could not save Excel file: {e}")


# 13. SUMMARY STATISTICS


print("\n" + "="*60)
print(" CLEANED DATA SUMMARY")
print("="*60)

print(f"\n Total Smartphones: {len(df_final)}")
print(f"  Unique Brands: {df_final['Brand'].nunique()}")

print(f"\n Price Statistics:")
print(f"  Min: KSh {df_final['Price (KSh)'].min():,.0f}")
print(f"  Max: KSh {df_final['Price (KSh)'].max():,.0f}")
print(f"  Average: KSh {df_final['Price (KSh)'].mean():,.0f}")
print(f"  Median: KSh {df_final['Price (KSh)'].median():,.0f}")

print(f"\n Rating Statistics:")
print(f"  Average: {df_final['Rating'].mean():.2f}")
print(f"  With Ratings: {df_final[df_final['Rating'].notna() & (df_final['Rating'] > 0)].shape[0]}")
print(f"  Without Ratings: {df_final[df_final['Rating'].isna() | (df_final['Rating'] == 0)].shape[0]}")

print(f"\n Discount Statistics:")
print(f"  Average: {df_final['Discount %'].mean():.1f}%")
print(f"  With Discount: {len(df_final[df_final['Discount %'] > 0])}")
print(f"  Flagged (High): {df_final['High Discount Flag'].sum()}")

print(f"\n Price Categories:")
for category, count in df_final['Price Category'].value_counts().items():
    print(f"  {category}: {count} ({count/len(df_final)*100:.1f}%)")

print(f"\n Rating Categories:")
for category, count in df_final['Rating Category'].value_counts().items():
    print(f"  {category}: {count} ({count/len(df_final)*100:.1f}%)")

print(f"\n Top 10 Brands:")
brand_summary = df_final.groupby('Brand').agg({
    'Product Name': 'count',
    'Price (KSh)': 'mean',
    'Rating': 'mean'
}).rename(columns={'Product Name': 'Count'}).round(2)

brand_summary = brand_summary.sort_values('Count', ascending=False)
for brand, row in brand_summary.head(10).iterrows():
    print(f"  {brand}: {int(row['Count'])} phones, Avg Price: KSh {row['Price (KSh)']:,.0f}, Avg Rating: {row['Rating']:.2f}")


# 14. BEST VALUE RECOMMENDATIONS


print("\n" + "="*60)
print(" TOP 10 BEST VALUE SMARTPHONES")
print("="*60)

# Only consider phones with ratings
best_value = df_final[df_final['Rating'] > 0].nlargest(10, 'Value Score')

for i, (_, row) in enumerate(best_value.iterrows(), 1):
    print(f"\n{i}. {row['Brand']} {row['Product Name'][:60]}...")
    print(f"   Price: KSh {row['Price (KSh)']:,.0f} | Rating: {row['Rating']:.2f} | Discount: {row['Discount %']:.1f}%")
    print(f"   Specs: {row['Storage (GB)']}GB + {row['RAM (GB)']}GB RAM, {row['Battery (mAh)']}mAh")


# 15. EXPORT TO JSON


try:
    df_final.to_json('jumia_smartphones_cleaned.json', orient='records', indent=2)
    print("\n Saved file: jumia_smartphones_cleaned.json")
except Exception as e:
    print(f"\n Could not save JSON file: {e}")

print("\n" + "="*60)
print(" ANALYSIS COMPLETE")
print("="*60)

# Print first few rows
print("\n Preview of cleaned data:")
print(df_final[['Brand', 'Product Name', 'Price (KSh)', 'Rating', 'Discount %']].head(10).to_string())