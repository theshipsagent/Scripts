import os
import pandas as pd
import traceback
from datetime import datetime

# Hardcoded paths
INPUT_DIR = r"/Input"
OUTPUT_DIR = r"/Output"

# Ensure dirs exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Vessel names to exclude (case-insensitive)
EXCLUDE_NAMES = {
    "allisonk", "allins k", "keeneland", "chesapeake bay", "jadwin discharge",
    "dixie raider", "mack b", "texas star", "dodge island", "ginny lab",
    "kennington", "randy martin", "white star"
}

def stamp(message: str):
    """Print timestamped messages to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_all_files():
    """Load and concatenate all CSV files from INPUT_DIR."""
    all_dfs = []
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".csv")]
    stamp(f"Found {len(files)} CSV files in {INPUT_DIR}")

    for file in files:
        file_path = os.path.join(INPUT_DIR, file)
        try:
            df = pd.read_csv(file_path, dtype=str)  # keep all as string
            df["SourceFile"] = file
            all_dfs.append(df)
            stamp(f"Loaded {file}: {len(df)} rows")
        except Exception as e:
            stamp(f"ERROR reading {file}: {e}")
            traceback.print_exc()

    merged_df = pd.concat(all_dfs, ignore_index=True)
    stamp(f"Total merged rows: {len(merged_df)}")
    return merged_df

def standardize_data(df):
    """Standardize IMO and Name, apply exclusions."""
    df = df.copy()
    df["IMO"] = df["IMO"].astype(str).str[:7]       # IMO always 7 chars
    df["Name"] = df["Name"].astype(str).str.strip() # remove leading/trailing spaces

    # Exclusion (case-insensitive)
    df["NameLower"] = df["Name"].str.lower()
    before = len(df)
    df = df[~df["NameLower"].isin(EXCLUDE_NAMES)].copy()
    after = len(df)
    stamp(f"Excluded {before - after} rows based on vessel exclusion list")

    return df

def save_output(merged_df):
    suffix = datetime.now().strftime("%m%d%y%H%M")
    raw_path = os.path.join(OUTPUT_DIR, f"merged_raw_v2_{suffix}.csv")
    merged_df.to_csv(raw_path, index=False)
    stamp(f"Raw merged file saved: {raw_path}")

def main():
    stamp("=== Starting Merge Script (Step 1) ===")
    raw_df = load_all_files()
    raw_df = standardize_data(raw_df)
    save_output(raw_df)
    stamp("=== Script Complete ===")

if __name__ == "__main__":
    main()
