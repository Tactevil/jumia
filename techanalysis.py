

import sqlite3
import pandas as pd

DB_NAME = "jumia_tech.db"

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
    print("   JUMIA KENYA TECH ANALYSIS")
    print("   Testing the Discount Deception Hypothesis")
    print("   Database: jumia_tech.db")
    print("=" * 60)
    
    # QUESTION 1: Average Rating by Discount Tier
    # This tests our MAIN HYPOTHESIS
    
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
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(review_count), 0) AS avg_reviews
    FROM products
    WHERE rating > 0
    GROUP BY discount_tier
    ORDER BY avg_discount DESC
    """
    df1 = run_query(q1, " QUESTION 1: Average Rating by Discount Tier")
    
    # QUESTION 2: Category Performance
    # Which categories are best?
    
    q2 = """
    SELECT 
        category,
        COUNT(*) AS product_count,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(value_score), 3) AS avg_value_score,
        ROUND(MAX(discount_percentage), 1) AS max_discount
    FROM products
    WHERE rating > 0
    GROUP BY category
    HAVING COUNT(*) >= 10
    ORDER BY avg_rating DESC
    """
    df2 = run_query(q2, " QUESTION 2: Category Performance (Highest Ratings First)")
    
    
    # QUESTION 3: Brand Honesty
    # Which brands are most honest?
    
    q3 = """
    SELECT 
        brand,
        COUNT(*) AS product_count,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(value_score), 3) AS avg_value_score,
        ROUND(AVG(discount_percentage) / NULLIF(AVG(rating), 0), 1) AS deception_index
    FROM products
    WHERE brand != 'N/A' AND rating > 0
    GROUP BY brand
    HAVING COUNT(*) >= 3
    ORDER BY avg_rating ASC
    LIMIT 15
    """
    df3 = run_query(q3, " QUESTION 3: Brand Honesty (Lowest Ratings First = Most Deceptive)")
    
    
    # QUESTION 4: Best Deals
    # High discount + High rating = Genuine bargains
    
    q4 = """
    SELECT 
        category,
        product_name,
        brand,
        discount_percentage,
        rating,
        rating_category,
        current_price_kes,
        original_price_kes,
        review_count,
        value_score
    FROM products
    WHERE rating > 0 AND discount_percentage > 30
    ORDER BY discount_percentage DESC, rating DESC
    LIMIT 15
    """
    df4 = run_query(q4, " QUESTION 4: Best Deals (High Discount + High Rating)")
    
    # QUESTION 5: Worst Deals
    # High discount + Low rating = Red flag
    
    q5 = """
    SELECT 
        category,
        product_name,
        brand,
        discount_percentage,
        rating,
        rating_category,
        current_price_kes,
        original_price_kes,
        review_count
    FROM products
    WHERE rating > 0 AND discount_percentage > 30
    ORDER BY discount_percentage DESC, rating ASC
    LIMIT 15
    """
    df5 = run_query(q5, " QUESTION 5: Worst Deals (High Discount + Low Rating)")
    

    # QUESTION 6: Price Category Analysis
    # Which price tier offers best value?

    q6 = """
    SELECT 
        price_category,
        COUNT(*) AS product_count,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(discount_percentage), 1) AS avg_discount,
        ROUND(AVG(value_score), 3) AS avg_value_score
    FROM products
    WHERE price_category != 'Price Unavailable' AND rating > 0
    GROUP BY price_category
    ORDER BY avg_value_score DESC
    """
    df6 = run_query(q6, " QUESTION 6: Price Category Analysis (Best Value First)")
    
    # QUESTION 7: Overall Summary
    # The big picture

    q7 = """
    SELECT 
        COUNT(*) AS total_products,
        ROUND(AVG(current_price_kes), 0) AS avg_price_kes,
        ROUND(AVG(discount_percentage), 1) AS avg_discount_percent,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(MAX(rating), 2) AS max_rating,
        ROUND(MIN(rating), 2) AS min_rating,
        ROUND(AVG(value_score), 3) AS avg_value_score,
        ROUND(AVG(review_count), 0) AS avg_reviews
    FROM products
    WHERE rating > 0
    """
    df7 = run_query(q7, " QUESTION 7: Overall Summary Statistics")

    # EXTRA: Correlation Analysis
    # Is there a relationship between discount and rating?

    q8 = """
    SELECT 
        ROUND(discount_percentage, -1) AS discount_bucket,
        COUNT(*) AS product_count,
        ROUND(AVG(rating), 2) AS avg_rating,
        ROUND(AVG(review_count), 0) AS avg_reviews
    FROM products
    WHERE rating > 0
    GROUP BY discount_bucket
    ORDER BY discount_bucket
    """
    df8 = run_query(q8, " EXTRA: Discount vs Rating Correlation")
    
    # SAVE ALL RESULTS

    print("\n" + "=" * 60)
    print(" Saving results to CSV files...")
    print("=" * 60)
    
    df1.to_csv("analysis_1_discount_tiers.csv", index=False)
    df2.to_csv("analysis_2_category_performance.csv", index=False)
    df3.to_csv("analysis_3_brand_honesty.csv", index=False)
    df4.to_csv("analysis_4_best_deals.csv", index=False)
    df5.to_csv("analysis_5_worst_deals.csv", index=False)
    df6.to_csv("analysis_6_price_categories.csv", index=False)
    df7.to_csv("analysis_7_summary.csv", index=False)
    df8.to_csv("analysis_8_correlation.csv", index=False)
    
    print(" All results saved!")
    print("\n    Files created:")
    print("      - analysis_1_discount_tiers.csv   (Main hypothesis test)")
    print("      - analysis_2_category_performance.csv (Best categories)")
    print("      - analysis_3_brand_honesty.csv   (Brand rankings)")
    print("      - analysis_4_best_deals.csv      (Products to BUY)")
    print("      - analysis_5_worst_deals.csv     (Products to AVOID)")
    print("      - analysis_6_price_categories.csv (Best price tiers)")
    print("      - analysis_7_summary.csv         (Overall stats)")
    print("      - analysis_8_correlation.csv     (Discount vs Rating)")
    
    print("\n" + "=" * 60)
    print(" ANALYSIS COMPLETE!")
    print("   Open the CSV files in Excel to see your results.")
    print("=" * 60)

if __name__ == "__main__":
    main()