


import sqlite3
import pandas as pd

DB_NAME = "jumia_kenya.db"

def run_query(query, description="", show_results=True):
    """Run a SQL query and return results as DataFrame"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if description and show_results:
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"{'='*60}")
        print(df.to_string(index=False))
    
    return df

def main():
    print("=" * 60)
    print("   JUMIA KENYA ANALYSIS")
    print("   Testing the Discount Deception Hypothesis")
    print("   Using database: jumia_kenya.db")
    print("=" * 60)
    
    
    # QUERY 1: Average Rating by Discount Tier
    #  MAIN HYPOTHESIS test!
    
    q1 = """
    SELECT 
        CASE 
            WHEN discount_percentage < 10 THEN '0-10% (Minimal)'
            WHEN discount_percentage >= 10 AND discount_percentage < 30 THEN '10-30% (Moderate)'
            WHEN discount_percentage >= 30 AND discount_percentage < 60 THEN '30-60% (High)'
            WHEN discount_percentage >= 60 THEN '60%+ (Extreme)'
            ELSE 'No Discount'
        END AS discount_tier,
        COUNT(*) AS product_count,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(discount_percentage), 1) AS avg_discount
    FROM products
    WHERE rating IS NOT NULL
    GROUP BY discount_tier
    ORDER BY avg_discount DESC
    """
    df1 = run_query(q1, " QUESTION 1: Average Rating by Discount Tier")
    
    
    # QUERY 2: Brand Honesty Index
    # Which brands have high discounts but low ratings?
    
    q2 = """
    SELECT 
        brand,
        COUNT(*) AS product_count,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(value_score), 2) AS avg_value_score,
        ROUND(AVG(discount_percentage) / NULLIF(AVG(rating), 0), 1) AS deception_index
    FROM products
    WHERE brand != 'N/A' AND rating IS NOT NULL
    GROUP BY brand
    HAVING COUNT(*) >= 3
    ORDER BY avg_rating ASC
    LIMIT 15
    """
    df2 = run_query(q2, " QUESTION 2: Brand Honesty Index (Lowest Ratings First)")
    
    
    # QUERY 3: Worst Deals
    # High discount + low rating = The most deceptive products
    
    q3 = """
    SELECT 
        product_name,
        brand,
        discount_percentage,
        rating,
        rating_category,
        current_price_kes,
        original_price_kes,
        value_score
    FROM products
    WHERE rating IS NOT NULL AND discount_percentage > 30
    ORDER BY discount_percentage DESC, rating ASC
    LIMIT 10
    """
    df3 = run_query(q3, " QUESTION 3: Worst Deals (High Discount + Low Rating)")
    
    
    # QUERY 4: Best Deals
    # High discount + high rating = Genuine bargains
    
    q4 = """
    SELECT 
        product_name,
        brand,
        discount_percentage,
        rating,
        rating_category,
        current_price_kes,
        original_price_kes,
        value_score
    FROM products
    WHERE rating IS NOT NULL AND discount_percentage > 30
    ORDER BY discount_percentage DESC, rating DESC
    LIMIT 10
    """
    df4 = run_query(q4, " QUESTION 4: Best Deals (High Discount + High Rating)")
    
    
    # QUERY 5: Price Category Analysis
    # Are expensive products more honest?
    
    q5 = """
    SELECT 
        price_category,
        COUNT(*) AS product_count,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(value_score), 2) AS avg_value_score
    FROM products
    WHERE price_category IS NOT NULL
    GROUP BY price_category
    ORDER BY avg_value_score DESC
    """
    df5 = run_query(q5, " QUESTION 5: Price Category Analysis")
    
    
    # QUERY 6: Rating Category Distribution
    # How many products are Excellent vs Poor?
    
    q6 = """
    SELECT 
        rating_category,
        COUNT(*) AS product_count,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(current_price_kes), 0) AS avg_price
    FROM products
    WHERE rating_category IS NOT NULL
    GROUP BY rating_category
    ORDER BY rating_category
    """
    df6 = run_query(q6, " QUESTION 6: Rating Category Distribution")
    
    
    # QUERY 7: Overall Summary
    # The big picture
    
    q7 = """
    SELECT 
        COUNT(*) AS total_products,
        ROUND(AVG(current_price_kes), 0) AS avg_price_kes,
        ROUND(AVG(discount_percentage), 1) AS avg_discount_percent,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(MAX(rating), 2) AS max_rating,
        ROUND(MIN(rating), 2) AS min_rating,
        ROUND(AVG(value_score), 2) AS avg_value_score
    FROM products
    """
    df7 = run_query(q7, " QUESTION 7: Overall Summary Statistics")
    
    
    # SAVE ALL RESULTS
    
    print("\n" + "=" * 60)
    print(" Saving results to CSV files...")
    print("=" * 60)
    
    df1.to_csv("analysis_1_discount_tiers.csv", index=False)
    df2.to_csv("analysis_2_brand_honesty.csv", index=False)
    df3.to_csv("analysis_3_worst_deals.csv", index=False)
    df4.to_csv("analysis_4_best_deals.csv", index=False)
    df5.to_csv("analysis_5_price_categories.csv", index=False)
    df6.to_csv("analysis_6_rating_categories.csv", index=False)
    df7.to_csv("analysis_7_summary.csv", index=False)
    
    print(" All results saved!")
    print("\n    Files created:")
    print("      - analysis_1_discount_tiers.csv")
    print("      - analysis_2_brand_honesty.csv")
    print("      - analysis_3_worst_deals.csv")
    print("      - analysis_4_best_deals.csv")
    print("      - analysis_5_price_categories.csv")
    print("      - analysis_6_rating_categories.csv")
    print("      - analysis_7_summary.csv")
    
    print("\n" + "=" * 60)
    print(" ANALYSIS COMPLETE!")
    print("   Database used: jumia_kenya.db")
    print("   Now open the CSV files in Excel to see your results.")
    print("=" * 60)

if __name__ == "__main__":
    main()