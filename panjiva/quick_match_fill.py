"""
Quick Name Matcher - Fill Blank Fields Only
============================================
Exact name matching to populate SPCIQ ID, MI Key, SIC Codes
Only fills blanks, skips conflicts, all values as text strings

Author: Auto-generated
Date: 2025-10-16
"""

import pandas as pd
from datetime import datetime
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

LOOKUP_FILE = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\cosn_add_back.csv"
MATCH_FILE = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\entity_dictionary.csv"
OUTPUT_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva"

FIELDS_TO_FILL = ['SPCIQ ID', 'MI Key', 'SIC Codes']

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    print("="*80)
    print("QUICK NAME MATCHER - FILL BLANKS ONLY")
    print("="*80)
    print()
    
    # Load files
    print("Loading files...")
    lookup_df = pd.read_csv(LOOKUP_FILE, dtype=str, encoding='utf-8-sig')
    match_df = pd.read_csv(MATCH_FILE, dtype=str, encoding='utf-8-sig')
    
    print(f"  Lookup file: {len(lookup_df)} rows")
    print(f"  Match file:  {len(match_df)} rows")
    print()
    
    # Create lookup dictionary for fast matching
    print("Building lookup dictionary...")
    lookup_dict = {}
    
    for _, row in lookup_df.iterrows():
        name = row['Name']
        if pd.notna(name) and name.strip():
            lookup_dict[name] = {
                'SPCIQ ID': str(row['SPCIQ ID']) if pd.notna(row['SPCIQ ID']) else '',
                'MI Key': str(row['MI Key']) if pd.notna(row['MI Key']) else '',
                'SIC Codes': str(row['SIC Codes']) if pd.notna(row['SIC Codes']) else ''
            }
    
    print(f"  {len(lookup_dict)} unique names in lookup")
    print()
    
    # Statistics
    stats = {
        'rows_checked': 0,
        'names_matched': 0,
        'spciq_filled': 0,
        'mi_key_filled': 0,
        'sic_codes_filled': 0,
        'skipped_has_data': 0
    }
    
    # Process each row in match file
    print("Processing matches...")
    
    for idx, row in match_df.iterrows():
        stats['rows_checked'] += 1
        
        # Get name from match file
        match_name = row['Name']
        
        if pd.isna(match_name) or not str(match_name).strip():
            continue
        
        # Look for exact match
        if match_name in lookup_dict:
            stats['names_matched'] += 1
            lookup_data = lookup_dict[match_name]
            
            # Fill SPCIQ ID if blank
            if pd.isna(row['SPCIQ ID']) or str(row['SPCIQ ID']).strip() == '':
                if lookup_data['SPCIQ ID']:
                    match_df.at[idx, 'SPCIQ ID'] = lookup_data['SPCIQ ID']
                    stats['spciq_filled'] += 1
            else:
                stats['skipped_has_data'] += 1
            
            # Fill MI Key if blank
            if pd.isna(row['MI Key']) or str(row['MI Key']).strip() == '':
                if lookup_data['MI Key']:
                    match_df.at[idx, 'MI Key'] = lookup_data['MI Key']
                    stats['mi_key_filled'] += 1
            else:
                stats['skipped_has_data'] += 1
            
            # Fill SIC Codes if blank
            if pd.isna(row['SIC Codes']) or str(row['SIC Codes']).strip() == '':
                if lookup_data['SIC Codes']:
                    match_df.at[idx, 'SIC Codes'] = lookup_data['SIC Codes']
                    stats['sic_codes_filled'] += 1
            else:
                stats['skipped_has_data'] += 1
        
        # Progress indicator
        if stats['rows_checked'] % 1000 == 0:
            print(f"  Processed {stats['rows_checked']:,} rows...", end='\r')
    
    print(f"  Processed {stats['rows_checked']:,} rows... DONE")
    print()
    
    # Save output
    timestamp = datetime.now().strftime("%m%d%y%H%M")
    output_filename = f"entity_dictionary_{timestamp}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print("Saving output...")
    match_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"  Saved: {output_filename}")
    print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total rows checked:       {stats['rows_checked']:,}")
    print(f"Names matched:            {stats['names_matched']:,}")
    print(f"  SPCIQ ID filled:        {stats['spciq_filled']:,}")
    print(f"  MI Key filled:          {stats['mi_key_filled']:,}")
    print(f"  SIC Codes filled:       {stats['sic_codes_filled']:,}")
    print(f"Fields skipped (has data): {stats['skipped_has_data']:,}")
    print()
    print(f"Output: {output_path}")
    print("="*80)
    print("DONE!")
    print("="*80)


if __name__ == "__main__":
    main()
