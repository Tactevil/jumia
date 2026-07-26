

import sqlite3
import pandas as pd
import os


DB_NAME = "jumia_tech.db"
CSV_FILE = "jumia_tech_products_full_v2.csv" 

# STEP 1: CREATE THE DATABASE


def create_database():

    
    print("\n Creating database: jumia_tech.db ...")
    
    # Connect to SQLite 
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Drop table if it exists
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Create the products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            product_name TEXT,
            brand TEXT,
            current_price_kes REAL,
            original_price_kes REAL,
            discount_percentage REAL,
            high_discount_flag BOOLEAN,
            rating REAL,
            review_count INTEGER,
            product_url TEXT,
            scraped_at TEXT,
            storage_gb INTEGER,
            ram_gb INTEGER,
            battery_mah INTEGER,
            camera_mp INTEGER,
            rating_category TEXT,
            price_category TEXT,
            value_score REAL
        )
    """)
    
    conn.commit()
    print(" Database 'jumia_tech.db' created with 'products' table")
    
    return conn, cursor

# STEP 2: IMPORT CSV DATA


def import_csv_to_db(conn, cursor):
    """Read your CSV file and insert data into the database"""
    
    print(f"\n Reading CSV file: {CSV_FILE}")
    
    # Check if the CSV file exists
    if not os.path.exists(CSV_FILE):
        print(f" ERROR: CSV file '{CSV_FILE}' not found!")
        print(f"   Make sure the file is in: {os.getcwd()}")
        print(f"\n   Files in current folder:")
        for file in os.listdir():
            print(f"      - {file}")
        return False
    
    # Read the CSV using pandas
    df = pd.read_csv(CSV_FILE)
    print(f"    Read {len(df)} rows from CSV")
    print(f"   Columns found: {df.columns.tolist()}")
    
    print("\n Inserting data into jumia_tech.db...")
    
    # Insert each row into the database
    for index, row in df.iterrows():
        cursor.execute("""
            INSERT INTO products (
                category, product_name, brand, current_price_kes,
                original_price_kes, discount_percentage, high_discount_flag,
                rating, review_count, product_url, scraped_at,
                storage_gb, ram_gb, battery_mah, camera_mp,
                rating_category, price_category, value_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get('Category'),
            row.get('Product Name'),
            row.get('Brand'),
            row.get('Price (KSh)'),
            row.get('Original Price (KSh)'),
            row.get('Discount %'),
            row.get('High Discount Flag', False),
            row.get('Rating'),
            row.get('Review Count', 0),
            row.get('Product URL'),
            row.get('Scraped Date'),
            row.get('Storage (GB)'),
            row.get('RAM (GB)'),
            row.get('Battery (mAh)'),
            row.get('Camera (MP)'),
            row.get('Rating Category'),
            row.get('Price Category'),
            row.get('Value Score')
        ))
        
        # Show progress every 50 rows
        if (index + 1) % 50 == 0:
            print(f"   Inserted {index + 1} rows...")
    
    conn.commit()
    print(f"    Inserted all {len(df)} rows successfully into jumia_tech.db!")
    return True

# STEP 3: VERIFY THE DATA


def verify_data(conn, cursor):
    
    
    print("\n Verifying data in jumia_tech.db...")
    
    # Count total rows
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"    Total products in database: {count}")
    
    # Show sample rows
    print("\n   --- Sample Products (First 5 rows) ---")
    cursor.execute("""
        SELECT category, product_name, brand, current_price_kes, 
               discount_percentage, rating, rating_category
        FROM products
        LIMIT 5
    """)
    
    print(f"   {'Category':<12} {'Product Name':<30} {'Brand':<10} {'Price':<10} {'Disc%':<8} {'Rating':<8} {'Category':<12}")
    print(f"   {'-'*12} {'-'*30} {'-'*10} {'-'*10} {'-'*8} {'-'*8} {'-'*12}")
    
    for row in cursor.fetchall():
        name = row[1][:27] + '...' if row[1] and len(row[1]) > 30 else (row[1] or 'N/A')
        cat = row[0] if row[0] else 'N/A'
        brand = row[2] if row[2] else 'N/A'
        price = row[3] if row[3] is not None else 0
        disc = row[4] if row[4] is not None else 0
        rating = row[5] if row[5] is not None else 0
        rating_cat = row[6] if row[6] else 'N/A'
        print(f"   {cat:<12} {name:<30} {brand:<10} KSh{price:<8.0f} {disc:<7.1f}% {rating:<7.1f}⭐ {rating_cat:<12}")
    
    # Rating summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as with_ratings,
            ROUND(AVG(rating), 2) as avg_rating
        FROM products
        WHERE rating > 0
    """)
    result = cursor.fetchone()
    print(f"\n    Rating Summary:")
    print(f"      Total products: {result[0]}")
    print(f"      Products with ratings: {result[1]}")
    print(f"      Average rating: {result[2]}")
    
    return count

# MAIN


def main():
    print("=" * 60)
    print("   JUMIA KENYA DATABASE SETUP")
    print("   Using: jumia_tech.db")
    print(f"   Source: {CSV_FILE}")
    print("=" * 60)
    print("\nThis script will:")
    print("   1. Create a SQLite database (jumia_tech.db)")
    print("   2. Import your CSV data")
    print("   3. Verify everything loaded correctly")
    
    # Step 1: Create database
    conn, cursor = create_database()
    
    # Step 2: Import data
    success = import_csv_to_db(conn, cursor)
    
    if success:
    
        count = verify_data(conn, cursor)
        print(f"\n Database setup complete! {count} products ready for analysis.")
        print(f"   Database file: jumia_tech.db")
        print(f"   Data source: {CSV_FILE}")
    else:
        print("\n Database setup failed. Please check the error messages above.")
    
    # Close connection
    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()