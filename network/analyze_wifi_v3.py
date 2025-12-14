import pandas as pd
import os
import logging
import datetime
import sys
import re
try:
    from rapidfuzz import fuzz
except ImportError:
    print("rapidfuzz not found. Install via: pip install rapidfuzz")
    sys.exit(1)
from tkinter import Tk, filedialog

# Setup logging
log_dir = r"C:\Users\wsd3\OneDrive\GRoK\Projects\MANIFEST\Logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f"norm_log_{timestamp}.txt")
analysis_file = os.path.join(log_dir, f"analysis_{timestamp}.txt")

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

def clean_name(name):
    if pd.isna(name):
        return ''
    return re.sub(r'[^\w\s]', '', str(name)).lower().strip()

def build_normalization_map(names, threshold=85):
    unique_names = sorted(set(n for n in names if n), key=len, reverse=True)
    total = len(unique_names)
    logging.info(f"Total unique names to process: {total}")
    clusters = {}
    for i, name in enumerate(unique_names):
        if i % 100 == 0:
            logging.info(f"Processing name {i}/{total}")
        matched = False
        for rep in list(clusters.keys()):
            if fuzz.ratio(name, rep) > threshold:
                clusters[rep].append(name)
                matched = True
                break
        if not matched:
            clusters[name] = [name]
    norm_map = {}
    for rep, group in clusters.items():
        for g in group:
            norm_map[g] = rep
    logging.info(f"Normalization map built with {len(norm_map)} entries.")
    return norm_map

try:
    logging.info("Starting normalization script.")

    # File selection
    root = Tk()
    root.withdraw()
    input_file = filedialog.askopenfilename(title="Select Data File", filetypes=[("Data files", "*.xlsx *.xls *.csv")])
    if not input_file:
        logging.info("No file selected. Exiting.")
        sys.exit()

    input_dir = os.path.dirname(input_file)
    base_name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(input_dir, f"{base_name}_normalized_{timestamp}{ext}")

    logging.info(f"Loading file: {input_file}")
    if ext.lower() == '.csv':
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)

    # Select column
    columns = list(df.columns)
    logging.info(f"Available columns: {columns}")
    print("Available columns:", columns)
    selected_col = input("Enter the column name to normalize: ").strip()
    if selected_col not in columns:
        raise ValueError(f"Column '{selected_col}' not found.")

    new_col = selected_col + '_no'

    # Before analysis
    with open(analysis_file, 'w') as f:
        f.write("Before Normalization:\n")
        f.write(f"Shape: {df.shape}\n")
        f.write(f"Columns: {columns}\n")
        unique_count = df[selected_col].nunique()
        f.write(f"Unique in '{selected_col}': {unique_count}\n")
        top_values = df[selected_col].value_counts().head(5).to_string()
        f.write(f"Top 5 in '{selected_col}':\n{top_values}\n\n")

    logging.info("Building normalization map.")
    cleaned_names = df[selected_col].apply(clean_name)
    norm_map = build_normalization_map(cleaned_names)

    # Apply normalization
    logging.info("Applying normalization.")
    status_list = []
    normalized_list = []
    total_rows = len(df)
    for idx, original in enumerate(df[selected_col]):
        if idx % 1000 == 0:
            logging.info(f"Processing row {idx}/{total_rows}")
        cleaned = clean_name(original)
        normalized = norm_map.get(cleaned, cleaned)
        normalized_list.append(normalized if normalized else original)
        if cleaned:
            ratio = fuzz.ratio(cleaned, normalized)
            confidence = 'high confidence' if ratio >= 95 else 'low confidence' if ratio > 80 else 'unmatched'
        else:
            confidence = 'empty'
        status = confidence if confidence != 'high confidence' and confidence != 'empty' else ''
        status_list.append(status)
    df[new_col] = normalized_list
    df.insert(df.columns.get_loc(selected_col) + 1, 'step 1 status', status_list)
    df.insert(df.columns.get_loc(selected_col) + 1, new_col, df.pop(new_col))

    # After analysis
    with open(analysis_file, 'a') as f:
        f.write("\nAfter Normalization:\n")
        f.write(f"Shape: {df.shape}\n")
        f.write(f"Columns: {list(df.columns)}\n")
        unique_count = df[new_col].nunique()
        f.write(f"Unique in '{new_col}': {unique_count}\n")
        top_values = df[new_col].value_counts().head(5).to_string()
        f.write(f"Top 5 in '{new_col}':\n{top_values}\n\n")
        status_counts = df['step 1 status'].value_counts().to_string()
        f.write(f"Step 1 Status Counts:\n{status_counts}\n")

    logging.info("Normalization completed.")

    # Automatic save to input dir with versioning
    if ext.lower() == '.csv':
        df.to_csv(output_file, index=False)
    else:
        df.to_excel(output_file, index=False)
    logging.info(f"Saved processed file to: {output_file}")

except Exception as e:
    logging.error(f"Error occurred: {str(e)}", exc_info=True)
    raise

logging.info("Script execution completed.")