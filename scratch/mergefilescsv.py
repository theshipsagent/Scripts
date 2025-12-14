import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os

def merge_csv_files():
    root = tk.Tk()
    root.withdraw()

    # Step 1: Select CSV files
    file_paths = filedialog.askopenfilenames(
        title="Select CSV files to merge",
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_paths:
        messagebox.showinfo("No Selection", "No CSV files were selected.")
        return

    merged_rows = []
    header = None

    try:
        for i, file_path in enumerate(file_paths):
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                file_header = next(reader)
                if i == 0:
                    header = file_header
                    merged_rows.append(header)
                elif file_header != header:
                    messagebox.showerror("Header Mismatch", f"Header mismatch in file: {os.path.basename(file_path)}")
                    return
                merged_rows.extend(reader)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV files:\n{e}")
        return

    # Step 2: Ask where to save the merged file
    save_path = filedialog.asksaveasfilename(
        title="Save Merged CSV File As",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")]
    )

    if not save_path:
        messagebox.showinfo("Canceled", "Save operation canceled.")
        return

    try:
        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(merged_rows)
        messagebox.showinfo("Success", f"CSV files merged and saved to:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write merged CSV:\n{e}")

if __name__ == "__main__":
    merge_csv_files()
