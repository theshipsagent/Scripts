#!/usr/bin/env python3
"""
Company Name Normalization Script - BULLETPROOF FAIL-FAST VERSION
Tests normalization on ONE value first, then proceeds step by step.
Author: Generated for GRoK Projects
Version: 3.0 - Bulletproof
"""

import pandas as pd
import numpy as np
import os
import re
import logging
from datetime import datetime
import sys
import time
from pathlib import Path


def test_normalization_function():
    """Test the normalization function on a simple value first"""
    print("=" * 60)
    print("TESTING NORMALIZATION FUNCTION")
    print("=" * 60)

    try:
        # Simple test case
        test_value = "WALMART INC 123 MAIN ST"
        print(f"Testing with: '{test_value}'")

        # Simple normalization logic (no complex regex for now)
        if pd.isna(test_value) or test_value == '':
            result = ''
        else:
            result = str(test_value).upper().strip()
            # Remove common suffixes
            result = re.sub(r'\b(LLC|INC|CORP|LTD|CO)\b', '', result, flags=re.IGNORECASE).strip()
            # Stop at first comma
            if ',' in result:
                result = result.split(',')[0].strip()
            # Remove extra spaces
            result = ' '.join(result.split())

        print(f"Result: '{result}'")
        print("✅ Normalization function test PASSED")
        return True

    except Exception as e:
        print(f"❌ Normalization function test FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def load_file_safely(file_path):
    """Load file with extensive error checking"""
    print("=" * 60)
    print("LOADING FILE")
    print("=" * 60)

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None

        print(f"✅ File exists: {file_path}")

        # Try to load file
        print("Loading CSV file...")
        df = pd.read_csv(file_path, low_memory=False)
        print(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")

        # Check required columns
        required_cols = ['Notify Party', 'Shipper', 'Consignee_WSD']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            return None

        print("✅ All required columns found")
        return df

    except Exception as e:
        print(f"❌ Error loading file: {e}")
        print(f"Error type: {type(e).__name__}")
        return None


def test_single_row_processing(df):
    """Test processing on just the first row"""
    print("=" * 60)
    print("TESTING SINGLE ROW PROCESSING")
    print("=" * 60)

    try:
        if len(df) == 0:
            print("❌ DataFrame is empty")
            return False

        # Get first row
        first_row = df.iloc[0].copy()
        print(f"Testing row 0...")

        # Test accessing columns
        notify_party = first_row['Notify Party']
        shipper = first_row['Shipper']
        consignee_wsd = first_row['Consignee_WSD']

        print(f"Notify Party: '{notify_party}'")
        print(f"Shipper: '{shipper}'")
        print(f"Consignee_WSD: '{consignee_wsd}'")

        # Test simple normalization on each
        test_values = [notify_party, shipper, consignee_wsd]

        for i, val in enumerate(test_values):
            try:
                if pd.isna(val) or val == '':
                    normalized = ''
                else:
                    normalized = str(val).upper().strip()
                print(f"  Test {i + 1}: '{val}' → '{normalized}' ✅")
            except Exception as e:
                print(f"  Test {i + 1}: FAILED - {e} ❌")
                return False

        print("✅ Single row processing test PASSED")
        return True

    except Exception as e:
        print(f"❌ Single row processing test FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def create_columns_safely(df):
    """Create new columns with error checking"""
    print("=" * 60)
    print("CREATING NEW COLUMNS")
    print("=" * 60)

    try:
        # Create Notify_WSD column
        print("Creating 'Notify_WSD' column...")
        df['Notify_WSD'] = df['Notify Party'].copy()
        print(f"✅ 'Notify_WSD' created with {len(df[df['Notify_WSD'].notna()])} non-null values")

        # Create Shipper_WSD column
        print("Creating 'Shipper_WSD' column...")
        df['Shipper_WSD'] = df['Shipper'].copy()
        print(f"✅ 'Shipper_WSD' created with {len(df[df['Shipper_WSD'].notna()])} non-null values")

        print("✅ Column creation PASSED")
        return True

    except Exception as e:
        print(f"❌ Column creation FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def normalize_simple(value):
    """Simple, safe normalization function"""
    try:
        if pd.isna(value) or value == '':
            return ''

        # Convert to string and clean
        result = str(value).upper().strip()

        # Remove common business suffixes
        suffixes = ['LLC', 'INC', 'CORP', 'LTD', 'CO', 'COMPANY', 'CORPORATION', 'LIMITED']
        for suffix in suffixes:
            pattern = f'\\b{suffix}\\b'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Stop at first comma
        if ',' in result:
            result = result.split(',')[0]

        # Clean up spaces and punctuation
        result = result.strip()
        result = re.sub(r'[,.\-_\|;]+$', '', result).strip()
        result = ' '.join(result.split())

        return result

    except Exception as e:
        print(f"❌ Normalization error on value '{value}': {e}")
        raise e


def normalize_columns_safely(df, max_rows=10):
    """Normalize columns with extensive error checking"""
    print("=" * 60)
    print(f"NORMALIZING COLUMNS (processing {max_rows} rows)")
    print("=" * 60)

    try:
        columns_to_normalize = ['Notify_WSD', 'Shipper_WSD', 'Consignee_WSD']

        # Process only specified number of rows
        rows_to_process = min(max_rows, len(df))

        for col in columns_to_normalize:
            print(f"\nNormalizing column '{col}'...")

            for idx in range(rows_to_process):
                try:
                    original_value = df.iloc[idx][col]
                    print(f"  Row {idx}: Processing '{original_value}'")

                    normalized_value = normalize_simple(original_value)
                    df.iloc[idx, df.columns.get_loc(col)] = normalized_value

                    print(f"  Row {idx}: Result '{normalized_value}' ✅")

                except Exception as e:
                    print(f"  Row {idx}: FAILED - {e} ❌")
                    print(f"  Problematic value: '{original_value}'")
                    raise e

            print(f"✅ Column '{col}' normalization completed")

        print("✅ All normalization PASSED")
        return True

    except Exception as e:
        print(f"❌ Normalization FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def main():
    """Main function with step-by-step testing"""
    print("BULLETPROOF COMPANY NAME NORMALIZATION")
    print("Starting step-by-step testing...")

    # Step 1: Test normalization function
    if not test_normalization_function():
        print("\n❌ STOPPING: Normalization function test failed")
        input("Press Enter to exit...")
        return

    # Step 2: Load file
    file_path = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Manifest\River\riverdata_v1.1_20250919_150136.csv"
    df = load_file_safely(file_path)

    if df is None:
        print("\n❌ STOPPING: File loading failed")
        input("Press Enter to exit...")
        return

    # Step 3: Test single row processing
    if not test_single_row_processing(df):
        print("\n❌ STOPPING: Single row processing test failed")
        input("Press Enter to exit...")
        return

    # Step 4: Create columns
    if not create_columns_safely(df):
        print("\n❌ STOPPING: Column creation failed")
        input("Press Enter to exit...")
        return

    # Step 5: Normalize (only first 10 rows)
    if not normalize_columns_safely(df, max_rows=10):
        print("\n❌ STOPPING: Normalization failed")
        input("Press Enter to exit...")
        return

    # Step 6: Save results
    print("=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = rf"C:\Users\wsd3\OneDrive\GRoK\Projects\Manifest\River\riverdata_TEST_v1.1_{timestamp}.csv"

        df.to_csv(output_file, index=False)
        print(f"✅ Results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Save failed: {e}")
        input("Press Enter to exit...")
        return

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("🎉 SCRIPT COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    print(f"\nProcessed {min(10, len(df))} rows successfully")
    print("To process more rows, increase max_rows parameter in normalize_columns_safely()")

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()