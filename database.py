

import sqlite3
import pandas as pd
import os

# CONFIGURATION


DB_NAME = "jumia_kenya.db"                     
CSV_FILE = "jumia_smartphones_cleaned.csv"          


# STEP 1: CREATE THE DATABASE


def create_database():
    """Create the database and products table"""
    
    print("\n Creating database: jumia_kenya.db ...")
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Drop table if it exists
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Create the products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            brand TEXT,
            current_price_kes REAL,
            original_price_kes REAL,
            discount_percentage REAL,
            high_discount_flag BOOLEAN,
            rating REAL,
            rating_category TEXT,
            value_score REAL,
            price_category TEXT,
            storage_gb INTEGER,
            ram_gb INTEGER,
            battery_mah INTEGER,
            camera_mp INTEGER,
            product_url TEXT,
            scraped_at TEXT
        )
    """)
    
    conn.commit()
    print(" Database 'jumia_kenya.db' created with 'products' table")
    print("   Columns: product_name, brand, current_price_kes, ...")
    
    return conn, cursor


# STEP 2: IMPORT CSV DATA INTO DATABASE


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
    print(f"   Read {len(df)} rows from CSV")
    print(f"   Columns found: {df.columns.tolist()}")
    
    print("\n Inserting data into jumia_kenya.db...")
    
    # Insert each row into the database
    for index, row in df.iterrows():
        cursor.execute("""
            INSERT INTO products (
                product_name, brand, current_price_kes, original_price_kes,
                discount_percentage, high_discount_flag, rating, rating_category,
                value_score, price_category, storage_gb, ram_gb,
                battery_mah, camera_mp, product_url, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get('Product Name'),
            row.get('Brand'),
            row.get('Price (KSh)'),
            row.get('Original Price (KSh)'),
            row.get('Discount %'),
            row.get('High Discount Flag', False),
            row.get('Rating'),
            row.get('Rating Category'),
            row.get('Value Score'),
            row.get('Price Category'),
            row.get('Storage (GB)'),
            row.get('RAM (GB)'),
            row.get('Battery (mAh)'),
            row.get('Camera (MP)'),
            row.get('Product URL'),
            row.get('Scraped Date')
        ))
        
        # Show progress every 50 rows
        if (index + 1) % 50 == 0:
            print(f"   Inserted {index + 1} rows...")
    
    conn.commit()
    print(f"  Inserted all {len(df)} rows successfully into jumia_kenya.db!")
    return True


# STEP 3: VERIFY THE DATA


def verify_data(conn, cursor):
    """Check that the data loaded correctly"""
    
    print("\n Verifying data in jumia_kenya.db...")
    
    # Count total rows
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"  Total products in database: {count}")
    
    # Show sample rows
    print("\n  Sample Products (First 5 rows) ")
    cursor.execute("""
        SELECT product_name, brand, current_price_kes, 
               discount_percentage, rating, rating_category
        FROM products
        LIMIT 5
    """)
    
    print(f"   {'Product Name':<30} {'Brand':<10} {'Price':<10} {'Disc%':<8} {'Rating':<8} {'Category':<12}")
    print(f"   {'-'*30} {'-'*10} {'-'*10} {'-'*8} {'-'*8} {'-'*12}")
    
    for row in cursor.fetchall():
        name = row[0][:27] + '...' if len(row[0]) > 30 else row[0]
        print(f"   {name:<30} {row[1]:<10} KSh{row[2]:<8.0f} {row[3]:<7.1f}% {row[4]:<7.1f}⭐ {row[5]:<12}")
    
    return count


# MAIN EXECUTION


def main():
    print("=" * 60)
    print("   JUMIA KENYA DATABASE SETUP")
    print("   Using: jumia_kenya.db")
    print("   Source: jumia_smartphones_cleaned.csv")
    print("=" * 60)
    print("\nThis script will:")
    print("   1. Create a SQLite database (jumia_kenya.db)")
    print("   2. Import your CSV data into jumia_kenya.db")
    print("   3. Verify everything loaded correctly")
    
    #  Create database
    conn, cursor = create_database()
    
    #Import data
    success = import_csv_to_db(conn, cursor)
    
    if success:
        #  Verify
        count = verify_data(conn, cursor)
        print(f"\n Database setup complete! {count} products ready for analysis.")
        print(f"   Database file: jumia_kenya.db")
        print(f"   Data source: {CSV_FILE}")
    else:
        print("\n Database setup failed. Please check the error messages above.")
    
    # Close connection
    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()