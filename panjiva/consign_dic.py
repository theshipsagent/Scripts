import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os

# Path to dictionary file
DICT_PATH = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Manifest\River\consign_dic.csv"

def main():
    root = tk.Tk()
    root.withdraw()

    # Step 1: Select input CSV
    input_path = filedialog.askopenfilename(
        title="Select input CSV file",
        filetypes=[("CSV files", "*.csv")]
    )

    if not input_path:
        print("[ERROR] No input file selected.")
        return

    # Step 2: Select save location
    save_path = filedialog.asksaveasfilename(
        title="Save updated CSV file as",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")]
    )

    if not save_path:
        print("[ERROR] No save path provided.")
        return

    try:
        # Step 3: Read input file and dictionary
        df = pd.read_csv(input_path, encoding='utf-8', dtype=str)
        dictionary = pd.read_csv(DICT_PATH, encoding='utf-8', dtype=str).fillna("nan")

        print(f"[INFO] Loaded input file: {input_path}")
        print(f"[INFO] Loaded dictionary from: {DICT_PATH}")

        # Step 4: Check Consignee column exists
        if 'Consignee' not in df.columns:
            print("[ERROR] 'Consignee' column not found in input file.")
            return

        # Step 5: Copy Consignee → Consignee_WSD
        df['Consignee_WSD'] = df['Consignee']

        # Step 6: Insert new columns and fill 'nan'
        new_cols = ['Type', 'Group', 'Cargo Class', 'Cargo']
        for col in new_cols:
            df[col] = 'nan'

        # Step 7: Handle duplicate Consignee values in dictionary
        if dictionary['Consignee'].duplicated().any():
            dupes = dictionary[dictionary['Consignee'].duplicated(keep=False)]
            print(f"[WARN] Duplicate Consignee entries found in dictionary. Using first occurrence only:\n{dupes['Consignee'].unique()}")

        # Step 8: Create lookup dictionary (safe for duplicates)
        dictionary_unique = dictionary.drop_duplicates(subset='Consignee', keep='first')
        lookup_dict = dictionary_unique.set_index('Consignee').to_dict(orient='index')

        # Step 9: Populate new columns from dictionary
        matched = 0
        for idx, row in df.iterrows():
            consignee = row['Consignee']
            if consignee in lookup_dict:
                match = lookup_dict[consignee]
                df.at[idx, 'Type'] = match.get('Type', 'nan')
                df.at[idx, 'Group'] = match.get('Group', 'nan')
                df.at[idx, 'Cargo Class'] = match.get('Cargo Class', 'nan')
                df.at[idx, 'Cargo'] = match.get('Cargo', 'nan')
                matched += 1

        print(f"[INFO] Finished processing. {matched} rows matched to dictionary.")

        # Step 10: Save updated file
        df.to_csv(save_path, index=False, encoding='utf-8')
        print(f"[SUCCESS] Updated CSV saved to: {save_path}")

    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}")

if __name__ == "__main__":
    main()
