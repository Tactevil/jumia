

import pandas as pd
import re

# Load data
df = pd.read_csv("jumia_tech_products_full_v2.csv")
print(f"Loaded {len(df)} products")

# Remove rows with missing product name
df = df[df['Product Name'].notna()]
df = df[df['Product Name'] != 'N/A']

# Remove duplicates
df = df.drop_duplicates(subset=['Product Name', 'Brand'], keep='first')

# Fill missing ratings with 0 (for those still missing)
df['Rating'] = df['Rating'].fillna(0)
df['Review Count'] = df['Review Count'].fillna(0)

# Ensure price and discount are floats
df['Price (KSh)'] = df['Price (KSh)'].fillna(0)
df['Discount %'] = df['Discount %'].fillna(0)

# Recalculate discount if original price exists
mask = (df['Discount %'] == 0) & (df['Original Price (KSh)'].notna()) & (df['Price (KSh)'] > 0)
df.loc[mask, 'Discount %'] = ((df.loc[mask, 'Original Price (KSh)'] - df.loc[mask, 'Price (KSh)']) / df.loc[mask, 'Original Price (KSh)']) * 100
df.loc[mask, 'Discount %'] = df.loc[mask, 'Discount %'].round(1)

# Create Rating Category
def rating_cat(r):
    if r == 0:
        return 'No Rating'
    elif r >= 4.5:
        return 'Excellent'
    elif r >= 3.5:
        return 'Good'
    elif r >= 2.5:
        return 'Average'
    else:
        return 'Poor'

df['Rating Category'] = df['Rating'].apply(rating_cat)

# Create Price Category
def price_cat(p):
    if p == 0:
        return 'Price Unavailable'
    elif p < 5000:
        return 'Budget (<5k)'
    elif p < 15000:
        return 'Entry (5k-15k)'
    elif p < 30000:
        return 'Mid-Range (15k-30k)'
    elif p < 50000:
        return 'Premium (30k-50k)'
    else:
        return 'Luxury (>50k)'

df['Price Category'] = df['Price (KSh)'].apply(price_cat)

# Value Score
df['Value Score'] = ((df['Rating'] / 5) * 0.5 + (df['Discount %'] / 100) * 0.3 + (df['Review Count'] / 100) * 0.2).round(3)

# Save
df.to_csv("jumia_tech_cleaned_final.csv", index=False)
print(f"Cleaned data saved: {len(df)} products")