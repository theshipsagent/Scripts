#!/usr/bin/env python3
"""
Production ETL for Import Data Processing
Balanced between simplicity and functionality
"""

import os
import sys
import json
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
import warnings

warnings.filterwarnings('ignore')


def load_config():
    config_file = 'config.json'
    default_config = {
        "paths": {
            "input": r"C:\\Users\\wsd3\\OneDrive\\Takoradi\\Scripts\\Input",
            "output": r"C:\\Users\\wsd3\\OneDrive\\Takoradi\\Scripts\\Output",
            "processed": r"C:\\Users\\wsd3\\OneDrive\\Takoradi\\Scripts\\Processed",
            "logs": r"C:\\Users\\wsd3\\OneDrive\\Takoradi\\Scripts\\logs"
        },
        "processing": {
            "move_to_processed": True,
            "remove_duplicates": True,
            "filter_cruise_lines": True,
            "min_weight_tons": 1.0,
            "combine_files": True
        },
        "columns_to_clean": ["Quantity", "Weight (kg)", "Weight (t)", "Value of Goods (USD)"],
        "date_columns": ["Arrival Date"],
        "entity_columns": ["Shipper", "Consignee", "Notify Party"],
        "cruise_lines": [
            "ROYAL CARIBBEAN", "CARNIVAL", "NCL", "CELEBRITY",
            "PRINCESS CRUISES", "VIRGIN VOYAGES", "DISNEY CRUISE"
        ]
    }
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                for key in default_config:
                    if key in user_config:
                        if isinstance(default_config[key], dict):
                            default_config[key].update(user_config[key])
                        else:
                            default_config[key] = user_config[key]
                return default_config
        except Exception as e:
            print(f"Error loading config.json: {e}")
            print("Using default configuration")
    else:
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Created config.json - you can edit this file to change settings")
    return default_config


CONFIG = load_config()


def setup_logging():
    log_dir = CONFIG['paths']['logs']
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def safe_input(prompt):
    try:
        return input(prompt)
    except Exception:
        return None


class DataProcessor:
    def __init__(self, logger):
        self.logger = logger
        self.stats = {
            'files_processed': 0,
            'total_rows_input': 0,
            'total_rows_output': 0,
            'files_failed': []
        }

    def clean_numeric(self, value):
        if pd.isna(value):
            return np.nan
        try:
            str_val = str(value).replace(',', '').replace('$', '')
            import re
            numbers = re.findall(r'-?\d+\.?\d*', str_val)
            if numbers:
                return float(numbers[0])
            return np.nan
        except Exception:
            return np.nan

    def process_file(self, file_path):
        try:
            self.logger.info(f"Processing: {os.path.basename(file_path)}")
            try:
                df = pd.read_csv(file_path, low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1', low_memory=False)
            initial_rows = len(df)
            self.stats['total_rows_input'] += initial_rows
            df.columns = df.columns.str.strip()
            for col in CONFIG['columns_to_clean']:
                if col in df.columns:
                    df[col] = df[col].apply(self.clean_numeric)
            for col in CONFIG['date_columns']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            if CONFIG['processing']['filter_cruise_lines']:
                for entity_col in CONFIG['entity_columns']:
                    if entity_col in df.columns:
                        for cruise in CONFIG['cruise_lines']:
                            mask = df[entity_col].str.contains(cruise, case=False, na=False)
                            df = df[~mask]
            if 'Weight (t)' in df.columns and CONFIG['processing']['min_weight_tons']:
                df = df[df['Weight (t)'] >= CONFIG['processing']['min_weight_tons']]
            if any(c in df.columns for c in CONFIG['entity_columns']):
                def get_primary_entity(row):
                    for c in CONFIG['entity_columns']:
                        if c in row and pd.notna(row[c]) and str(row[c]).strip():
                            return str(row[c]).strip().upper()
                    return 'UNKNOWN'
                df['Primary_Entity'] = df.apply(get_primary_entity, axis=1)
            final_rows = len(df)
            self.logger.info(f"  Input rows: {initial_rows}, Output rows: {final_rows}")
            self.stats['files_processed'] += 1
            self.stats['total_rows_output'] += final_rows
            return df
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {str(e)}")
            self.stats['files_failed'].append(os.path.basename(file_path))
            return None

    def process_all_files(self):
        input_dir = CONFIG['paths']['input']
        output_dir = CONFIG['paths']['output']
        processed_dir = CONFIG['paths']['processed']
        for dir_path in [input_dir, output_dir, processed_dir]:
            os.makedirs(dir_path, exist_ok=True)
        csv_files = list(Path(input_dir).glob('*.csv'))
        if not csv_files:
            self.logger.warning(f"No CSV files found in {input_dir}")
            return None
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        all_dataframes = []
        for file_path in csv_files:
            df = self.process_file(str(file_path))
            if df is not None:
                all_dataframes.append(df)
                if CONFIG['processing']['move_to_processed']:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_name = f"{timestamp}_{file_path.name}"
                    new_path = Path(processed_dir) / new_name
                    try:
                        shutil.move(str(file_path), str(new_path))
                    except Exception as e:
                        self.logger.error(f"Failed to move {file_path} to processed: {e}")
                    else:
                        self.logger.info(f"  Moved to: {new_name}")
        combined_df = None
        if all_dataframes:
            if CONFIG['processing']['combine_files'] and len(all_dataframes) > 1:
                self.logger.info("Combining all processed files...")
                combined_df = pd.concat(all_dataframes, ignore_index=True)
                if CONFIG['processing']['remove_duplicates']:
                    before = len(combined_df)
                    combined_df.drop_duplicates(inplace=True)
                    after = len(combined_df)
                    self.logger.info(f"Removed {before - after} duplicate rows")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = Path(output_dir) / f'combined_output_{timestamp}.csv'
                combined_df.to_csv(output_file, index=False)
                self.logger.info(f"Saved combined output: {output_file}")
                for i, dfi in enumerate(all_dataframes):
                    individual_file = Path(output_dir) / f'processed_{i + 1}_{timestamp}.csv'
                    dfi.to_csv(individual_file, index=False)
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                for i, dfi in enumerate(all_dataframes):
                    output_file = Path(output_dir) / f'processed_{i + 1}_{timestamp}.csv'
                    dfi.to_csv(output_file, index=False)
                    self.logger.info(f"Saved: {output_file}")
            return combined_df if (combined_df is not None and CONFIG['processing']['combine_files']) else all_dataframes
        return None


def quick_analysis(df):
    print("\n" + "=" * 60)
    print("QUICK ANALYSIS")
    print("=" * 60)
    print(f"\nDataset Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    if date_cols:
        for col in date_cols:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                print(f"\n{col} Range:")
                print(f"  From: {df[col].min()}")
                print(f"  To:   {df[col].max()}")
    if 'Primary_Entity' in df.columns:
        print("\nTop 10 Entities:")
        top_entities = df['Primary_Entity'].value_counts().head(10)
        for entity, count in top_entities.items():
            print(f"  {entity[:40]:40} {count:,}")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print("\nNumeric Column Summaries:")
        for col in numeric_cols[:5]:
            if df[col].notna().any():
                print(f"\n  {col}:")
                print(f"    Mean: {df[col].mean():,.2f}")
                print(f"    Total: {df[col].sum():,.2f}")
                print(f"    Non-null: {df[col].notna().sum():,}")


def main():
    print("=" * 60)
    print("ETL PRODUCTION PIPELINE")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Config: {os.path.abspath('config.json')}")
    logger = setup_logging()
    processor = DataProcessor(logger)
    result = processor.process_all_files()
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Files Processed: {processor.stats['files_processed']}")
    print(f"Files Failed: {len(processor.stats['files_failed'])}")
    if processor.stats['files_failed']:
        print(f"Failed Files: {', '.join(processor.stats['files_failed'])}")
    print(f"Total Input Rows: {processor.stats['total_rows_input']:,}")
    print(f"Total Output Rows: {processor.stats['total_rows_output']:,}")
    print(f"Rows Filtered: {processor.stats['total_rows_input'] - processor.stats['total_rows_output']:,}")
    if result is not None:
        if isinstance(result, pd.DataFrame):
            quick_analysis(result)
        elif isinstance(result, list) and len(result) > 0:
            print("\nProcessed multiple files separately")
            print(f"Total files: {len(result)}")
    print("\n" + "=" * 60)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Logs saved to: {CONFIG['paths']['logs']}")
    print(f"Output saved to: {CONFIG['paths']['output']}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
        safe_input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        safe_input("\nPress Enter to exit...")
        sys.exit(1)
