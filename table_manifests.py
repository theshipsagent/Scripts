import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import logging

# Configuration
LOG_DIR = r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST\Logs"
OUTPUT_DIR = r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST\Output"
LOG_FILE = os.path.join(LOG_DIR, "table_log.log")
SUMMARY_FILE = os.path.join(LOG_DIR, "table_summary.txt")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
print(f"Logging initialized at {LOG_FILE}")

def log_summary(message):
    """Append message to summary file."""
    with open(SUMMARY_FILE, "a") as f:
        f.write(f"{datetime.now()}: {message}\n")
    print(f"Summary: {message}")

def select_csv_file():
    """Open file explorer to select a CSV file."""
    root = tk.Tk()
    root.withdraw()
    print("Opening file explorer to select CSV file...")
    file = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV files", "*.csv")],
        initialdir=r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST"
    )
    print(f"Selected file: {file}")
    root.destroy()
    return file if os.path.exists(file) and file.lower().endswith('.csv') else None

def create_tables(filepath):
    """Create a separate table CSV for each unique value with sums of 'count' and 'weight (t)'."""
    print(f"Creating tables for: {os.path.basename(filepath)}")
    logging.info(f"Starting table creation for {os.path.basename(filepath)}")

    try:
        # Read CSV with UTF-8 encoding and specific dtypes
        df = pd.read_csv(filepath, encoding='utf-8', dtype={
            'hs code': str,
            'port of unlading': str,
            'carrier': str,
            'consignee (original format)': str,
            'shipper (original format)': str,
            'notify party': str,
            'count': float,
            'weight (t)': float
        })
        print(f"Columns found: {df.columns.tolist()}")  # Debug: Show all columns
        print(f"Read {len(df)} rows, {len(df.columns)} columns")

        # Columns to analyze
        analysis_columns = [
            'hs code', 'port of unlading', 'carrier',
            'consignee (original format)', 'shipper (original format)', 'notify party'
        ]

        # Check if required columns exist
        missing_cols = [col for col in analysis_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
        if 'count' not in df.columns or 'weight (t)' not in df.columns:
            raise ValueError("Required columns 'count' or 'weight (t)' not found")

        # Create and save a table for each column
        result_dict = {}
        for col in analysis_columns:
            grouped = df.groupby(col).agg({'count': 'sum', 'weight (t)': 'sum'}).reset_index()
            result_dict[col] = grouped

            # Save each table to a separate CSV
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            output_csv = os.path.join(OUTPUT_DIR, f"{base_name}_table_{col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            grouped.to_csv(output_csv, index=False, encoding='utf-8')
            print(f"Saved table for {col} to: {output_csv}")
            logging.info(f"Saved table for {col} to {output_csv}")

        # Generate text analysis summary
        analysis_text = f"Table Summary for {os.path.basename(filepath)} at {datetime.now()}:\n"
        for col, df_group in result_dict.items():
            total_count = df_group['count'].sum()
            total_weight = df_group['weight (t)'].sum()
            analysis_text += f"\n{col}:\n  Unique values: {len(df_group)}\n  Total Count: {total_count}\n  Total Weight (t): {total_weight}\n"

        analysis_txt = os.path.join(LOG_DIR, f"{base_name}_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(analysis_txt, 'w', encoding='utf-8') as f:
            f.write(analysis_text)
        print(f"Saved text summary to: {analysis_txt}")
        logging.info(f"Saved text summary to {analysis_txt}")

        log_summary(f"Created tables for {os.path.basename(filepath)}: {len(df)} rows, {len(analysis_columns)} columns analyzed")

    except Exception as e:
        error_msg = f"Error creating tables for {os.path.basename(filepath)}: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        log_summary(error_msg)

def main():
    """Main function to select and create tables from CSV file."""
    print("Starting table creation process...")
    logging.info("Table creation process started")
    log_summary("Table creation process started")

    filepath = select_csv_file()
    if not filepath:
        msg = "No CSV file selected"
        print(msg)
        logging.warning(msg)
        log_summary(msg)
        return

    create_tables(filepath)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"Script failed: {e}"
        print(msg)
        logging.error(msg)
        with open(SUMMARY_FILE, "a") as f:
            f.write(f"{datetime.now()}: {msg}\n")