"""
Shipper Harmonization Script - Stage 1: Top 35 Companies
=========================================================
SIMPLE KEYWORD MATCHING - Group by core company name
Filter: Only entities with ≥10,000,000 kg (10,000 MT)

Date: 2025-10-15
"""

import pandas as pd
import re
import os
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    INPUT_FILE = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\panjiva_summaries\summary_pairs\u_s_imports__all_shipments_grouped_by_shipper_results_1_to_10_000_of_14_729.csv"
    OUTPUT_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\LLM_analysis\outputs"

    MIN_KG_THRESHOLD = 10000000  # 10 million kg
    PROCESS_ALL = True  # Process entire filtered dataset, not just top N

    # Words to remove before matching
    NOISE_WORDS = {
        'LIMITED', 'LTD', 'LLC', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO',
        'SA', 'DE', 'CV', 'NV', 'BV', 'GMBH', 'AG', 'PLC', 'PTE', 'PTY', 'SDN', 'BHD',
        'TRADING', 'INTERNATIONAL', 'GLOBAL', 'WORLDWIDE', 'OPERATIONS', 'SERVICES',
        'PRODUCTS', 'COMPANY', 'GROUP', 'HOLDINGS', 'INDUSTRIES', 'RESOURCES',
        'MATERIALS', 'SUPPLY', 'MARKETING', 'COMMERCIAL', 'FUELS', 'ENERGY'
    }


# ============================================================================
# FUNCTIONS
# ============================================================================

def extract_core_name(full_name):
    """Extract core company name by removing noise"""
    if pd.isna(full_name) or not isinstance(full_name, str):
        return ""

    # Uppercase
    name = full_name.upper().strip()

    # Remove everything after comma (address)
    if ',' in name:
        name = name.split(',')[0]

    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)

    # Split into words
    words = name.split()

    # Remove noise words but keep significant ones
    core_words = [w for w in words if w not in Config.NOISE_WORDS and len(w) >= 3]

    return ' '.join(core_words).strip()


def find_key_pattern(name):
    """Find the key company identifier (first significant word or acronym)"""
    core = extract_core_name(name)

    if not core:
        return ""

    words = core.split()

    # Single word - use it
    if len(words) == 1:
        return words[0]

    # Check if first word is distinctive brand name (5+ chars, alphabetic)
    # This catches: CHEVRON, EXXONMOBIL, PETROBRAS, MARATHON, etc.
    if words and len(words[0]) >= 5 and words[0].isalpha():
        return words[0]

    # Check if first word is short acronym (2-4 caps letters)
    # This catches: PMI, CEMEX, etc.
    if words and 2 <= len(words[0]) <= 4 and words[0].isalpha():
        return words[0]

    # For 2-word names, return both (MARTIN MARIETTA, RIO TINTO, etc.)
    if len(words) == 2:
        return ' '.join(words[:2])

    # For longer names, return first 2 words if both are significant
    if len(words) >= 3:
        # Check if it's "COMPANY NAME" pattern
        if len(words[0]) >= 4:
            return words[0]
        else:
            return ' '.join(words[:2])

    return core


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SHIPPER HARMONIZATION - SIMPLE KEYWORD GROUPING")
    print("=" * 80)
    print()

    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    # Read data
    print(f"Reading: {Config.INPUT_FILE}")
    df = pd.read_csv(Config.INPUT_FILE)
    print(f"Total records: {len(df):,}")
    print()

    # Filter by KG
    print(f"Filtering: KG >= {Config.MIN_KG_THRESHOLD:,}")
    df_filtered = df[df['KG'] >= Config.MIN_KG_THRESHOLD].copy()
    print(f"After filter: {len(df_filtered):,}")
    print()

    # Process ALL filtered records
    df_to_process = df_filtered.copy()
    print(f"Processing ALL {len(df_to_process):,} companies that meet threshold")
    print()

    # Extract key patterns
    df_to_process['Core_Name'] = df_to_process['Shipper Name'].apply(extract_core_name)
    df_to_process['Key_Pattern'] = df_to_process['Shipper Name'].apply(find_key_pattern)

    # Group by key pattern
    print("Grouping by key company name...")
    groups = df_to_process.groupby('Key_Pattern')

    results = []

    for key_pattern, group_df in groups:
        if not key_pattern:
            continue

        # Get all variations
        variations = group_df['Shipper Name'].tolist()
        addresses = group_df['Shipper Full Address'].tolist()

        # Totals
        total_kg = group_df['KG'].sum()
        total_shipments = group_df['Shipments'].sum()
        total_value = group_df['VALUE (usd)'].sum()

        # Extract address keywords
        address_keywords = set()
        for addr in addresses:
            if pd.notna(addr):
                addr_upper = str(addr).upper()
                # Extract country/city
                if 'MEXICO' in addr_upper: address_keywords.add('MEXICO')
                if 'CANADA' in addr_upper: address_keywords.add('CANADA')
                if 'HOUSTON' in addr_upper: address_keywords.add('HOUSTON')
                if 'BRAZIL' in addr_upper: address_keywords.add('BRAZIL')
                if 'NETHERLANDS' in addr_upper: address_keywords.add('NETHERLANDS')
                if 'PANAMA' in addr_upper: address_keywords.add('PANAMA')
                if 'COLOMBIA' in addr_upper: address_keywords.add('COLOMBIA')
                if 'DUBAI' in addr_upper: address_keywords.add('DUBAI')

        # Build match keywords - just the key pattern
        match_keywords = key_pattern

        results.append({
            'Canonical_Name': key_pattern,
            'Match_Keywords': match_keywords,
            'Address_Keywords': '|'.join(sorted(address_keywords)) if address_keywords else '',
            'Total_KG': total_kg,
            'Total_Shipments': total_shipments,
            'Total_Value_USD': total_value,
            'Variations_Count': len(variations),
            'Sample_Variations': '; '.join(variations[:3]),
            'All_Variations': ' || '.join(variations)
        })

    # Create output
    output_df = pd.DataFrame(results)
    output_df = output_df.sort_values('Total_KG', ascending=False)
    output_df.insert(0, 'Rank', range(1, len(output_df) + 1))

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(Config.OUTPUT_DIR, f"shipper_dictionary_ALL_ABOVE_10MT_{timestamp}.csv")
    output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"✓ Dictionary saved: {output_file}")
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Unique companies found: {len(output_df)}")
    print()
    print("TOP 20 BY VOLUME:")
    print("-" * 80)
    for i, row in output_df.head(20).iterrows():
        print(
            f"{row['Rank']:2d}. {row['Canonical_Name']:<30} {row['Total_KG']:>15,.0f} kg  ({row['Variations_Count']} variations)")
    print()
    print("=" * 80)
    print("DONE - Review the output CSV and adjust canonical names as needed")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())