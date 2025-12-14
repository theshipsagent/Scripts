import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import numpy as np

# 1. Columns to keep with their formatting rules
COLUMNS_AND_FORMATS = {
    "Bill of Lading Number": "Text",
    "Arrival Date": "Date",
    "Matching Fields": "general",
    "Consignee": "Text",
    "Consignee Full Address": "Text",
    "Consignee SIC Codes": "Text",
    "Consignee Ultimate Parent": "Text",
    "Shipper": "Text",
    "Shipper Full Address": "Text",
    "Shipper Ultimate Parent": "Text",
    "Carrier": "Text",
    "Notify Party": "Text",
    "Notify Party SCAC": "Text",
    "Shipment Origin": "Text",
    "Shipment Destination": "Text",
    "Shipment Destination Region": "Text",
    "Port of Unlading": "Text",
    "Port of Unlading Region": "Text",
    "Port of Lading": "Text",
    "Port of Lading Region": "Text",
    "Port of Lading Country": "Text",
    "Place of Receipt": "Text",
    "Transport Method": "Text",
    "Vessel": "Text",
    "Vessel Voyage ID": "Text",
    "Vessel IMO": "Text",
    "Quantity": "number",
    "Measurement": "Text",
    "Weight (kg)": "number",
    "Weight (t)": "number",
    "Weight (Original Format)": "number",
    "Value of Goods (USD)": "currency",
    "Industry - GICS": "Text",
    "Industry - GICS Description": "Text",
    "HS Code": "Text",
    "Goods Shipped": "Text",
    "Dangerous Goods": "Text"
}

def format_column(series, fmt):
    """Apply formatting to a column."""
    if fmt == "Text":
        return series.astype(str).fillna("")
    elif fmt == "Date":
        return pd.to_datetime(series, errors='coerce').dt.strftime('%Y-%m-%d')
    elif fmt == "number":
        return pd.to_numeric(series, errors='coerce').round(0).fillna(0).astype(int)
    elif fmt == "currency":
        return pd.to_numeric(series, errors='coerce').round(0).fillna(0).astype(int)
    else:
        return series  # leave as-is

def process_csv_file(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', dtype=str, low_memory=False)

        # Keep only the needed columns
        keep_cols = list(COLUMNS_AND_FORMATS.keys())
        df = df[[col for col in keep_cols if col in df.columns]]

        # Format each column
        for col, fmt in COLUMNS_AND_FORMATS.items():
            if col in df.columns:
                df[col] = format_column(df[col], fmt)

        # Save result
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_formatted.csv"
        df.to_csv(output_path, index=False, encoding='utf-8')

        print(f"[SUCCESS] Processed and saved: {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}:\n{e}")

def run_batch_formatting():
    root = tk.Tk()
    root.withdraw()

    file_paths = filedialog.askopenfilenames(
        title="Select CSV file(s) to format",
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_paths:
        print("No files selected.")
        return

    for file_path in file_paths:
        print(f"[INFO] Processing: {os.path.basename(file_path)}")
        process_csv_file(file_path)

if __name__ == "__main__":
    run_batch_formatting()
