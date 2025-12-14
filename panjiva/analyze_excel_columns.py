"""
Excel Column Structure Analyzer
================================
Analyzes all Excel files to identify column mismatches and header issues.
"""

import os
import pandas as pd
import glob
from collections import defaultdict

# Configuration
SOURCE_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\Llyods"

def analyze_excel_file(file_path):
    """Analyze a single Excel file structure"""
    filename = os.path.basename(file_path)
    
    try:
        # Read first few rows to check structure
        df = pd.read_excel(file_path, engine='openpyxl', nrows=5)
        
        # Get column information
        columns = list(df.columns)
        num_columns = len(columns)
        
        # Check if first row looks like a header or data
        first_row_values = df.iloc[0].tolist() if len(df) > 0 else []
        
        # Detect if there's a title row (like "Report produced by...")
        has_title_row = False
        title_text = None
        if columns[0] and isinstance(columns[0], str) and 'Report produced' in str(columns[0]):
            has_title_row = True
            title_text = columns[0]
        
        return {
            'filename': filename,
            'num_columns': num_columns,
            'columns': columns[:10],  # First 10 columns
            'has_title_row': has_title_row,
            'title_text': title_text,
            'first_data_row': first_row_values[:5],
            'success': True,
            'error': None
        }
    
    except Exception as e:
        return {
            'filename': filename,
            'num_columns': 0,
            'columns': [],
            'has_title_row': False,
            'title_text': None,
            'first_data_row': [],
            'success': False,
            'error': str(e)
        }


def main():
    """Main analysis function"""
    
    print("="*80)
    print("EXCEL FILE COLUMN STRUCTURE ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing files in: {SOURCE_DIR}\n")
    
    # Find all Excel files
    pattern = os.path.join(SOURCE_DIR, "*.xlsx")
    excel_files = glob.glob(pattern)
    
    # Exclude the merged CSV if it exists as xlsx
    excel_files = [f for f in excel_files if 'merged' not in os.path.basename(f).lower()]
    
    print(f"Found {len(excel_files)} Excel files\n")
    
    # Analyze each file
    results = []
    for file_path in sorted(excel_files):
        result = analyze_excel_file(file_path)
        results.append(result)
    
    # Group files by column count
    column_groups = defaultdict(list)
    for result in results:
        if result['success']:
            column_groups[result['num_columns']].append(result)
    
    # Print summary
    print("="*80)
    print("COLUMN COUNT DISTRIBUTION")
    print("="*80)
    
    for num_cols in sorted(column_groups.keys()):
        files = column_groups[num_cols]
        print(f"\n{num_cols} columns ({len(files)} files):")
        for result in files[:5]:  # Show first 5
            print(f"  - {result['filename']}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    # Identify files with title rows
    print("\n" + "="*80)
    print("FILES WITH TITLE/HEADER ROWS (PROBLEMATIC)")
    print("="*80)
    
    title_row_files = [r for r in results if r['success'] and r['has_title_row']]
    if title_row_files:
        print(f"\nFound {len(title_row_files)} files with title rows:\n")
        for result in title_row_files[:10]:  # Show first 10
            print(f"  X {result['filename']}")
            print(f"    Title: {result['title_text'][:60]}...")
        if len(title_row_files) > 10:
            print(f"\n  ... and {len(title_row_files) - 10} more files with title rows")
    else:
        print("\nNo files with title rows detected.")
    
    # Show sample column structures
    print("\n" + "="*80)
    print("SAMPLE COLUMN STRUCTURES")
    print("="*80)
    
    # Get most common column count
    if column_groups:
        most_common_count = max(column_groups.keys(), key=lambda k: len(column_groups[k]))
        
        print(f"\nMost common structure ({most_common_count} columns):")
        sample = column_groups[most_common_count][0]
        print(f"File: {sample['filename']}")
        print(f"Columns: {sample['columns'][:5]}")
    
    # Summary recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if title_row_files:
        print(f"""
The merge failed because {len(title_row_files)} files have title rows that pandas
is treating as column headers (like "Report produced by S&P Global on...").

SOLUTION: Use the FIXED merger script (csv_merger_llyods_FIXED.py) which
automatically detects and skips these title rows.
""")
    else:
        print("\nAll files appear to have consistent column structure.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
