import os
import pandas as pd
import logging
from datetime import datetime

# Configuration
MERGED_FILE = r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST\Output\master_manifest_20250702_001134_cfc876db.csv"
INPUT_DIR = r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST\Input"
LOG_DIR = r"C:\Users\wsd3\OneDrive\Desktop\MANIFEST\Logs"
LOG_FILE = os.path.join(LOG_DIR, "comparison_log.log")
SUMMARY_FILE = os.path.join(LOG_DIR, "comparison_summary.txt")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

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

def compare_data():
    """Compare merged file with input CSVs and analyze dates."""
    print("Starting comparison...")
    logging.info("Comparison started")
    log_summary("Comparison started")

    try:
        # Read merged file
        merged_df = pd.read_csv(MERGED_FILE)
        print(f"Read merged file: {len(merged_df)} rows")
        merged_df.columns = merged_df.columns.str.strip().str.lower()

        # Read all input CSVs
        input_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
        if not input_files:
            msg = f"No CSV files found in {INPUT_DIR}"
            print(msg)
            logging.warning(msg)
            log_summary(msg)
            return

        print(f"Found {len(input_files)} input CSVs: {', '.join(input_files)}")
        input_dfs = []
        for file in input_files:
            try:
                df = pd.read_csv(os.path.join(INPUT_DIR, file))
                df.columns = df.columns.str.strip().str.lower()
                input_dfs.append(df)
                print(f"Read {file}: {len(df)} rows")
            except Exception as e:
                msg = f"Error reading {file}: {e}"
                print(msg)
                logging.error(msg)
                log_summary(msg)

        # Concatenate input CSVs
        combined_input_df = pd.concat(input_dfs, ignore_index=True)
        print(f"Combined input: {len(combined_input_df)} rows")

        # Compare row counts
        if len(merged_df) != len(combined_input_df):
            msg = f"Row count mismatch: Merged ({len(merged_df)}) vs Input ({len(combined_input_df)})"
            print(msg)
            logging.error(msg)
            log_summary(msg)
        else:
            log_summary("Row counts match")

        # Compare data
        merged_df_sorted = merged_df.sort_values(by=merged_df.columns.tolist()).reset_index(drop=True)
        combined_input_sorted = combined_input_df.sort_values(by=combined_input_df.columns.tolist()).reset_index(drop=True)
        if not merged_df_sorted.equals(combined_input_sorted):
            msg = "Data mismatch between merged file and input files"
            print(msg)
            logging.error(msg)
            log_summary(msg)
        else:
            log_summary("Data matches between merged and input files")

        # Analyze dates
        if "arrival date" in merged_df.columns:
            merged_df["arrival date"] = pd.to_datetime(merged_df["arrival date"], errors="coerce")
            valid_dates = merged_df["arrival date"].dropna()
            if not valid_dates.empty:
                start_date = valid_dates.min()
                end_date = valid_dates.max()
                date_range = pd.date_range(start=start_date, end=end_date, freq="MS")
                data_months = valid_dates.dt.to_period("M").unique()
                expected_months = [d.to_period("M") for d in date_range]
                missing_months = [m for m in expected_months if m not in data_months]

                summary = (
                    f"Date range: {start_date.date()} to {end_date.date()}\n"
                    f"Missing months: {missing_months if missing_months else 'None'}"
                )
                print(summary)
                logging.info(summary)
                log_summary(summary)
            else:
                msg = "No valid dates found in 'arrival date' column"
                print(msg)
                logging.warning(msg)
                log_summary(msg)
        else:
            msg = "'arrival date' column not found"
            print(msg)
            logging.warning(msg)
            log_summary(msg)

    except Exception as e:
        msg = f"Comparison failed: {e}"
        print(msg)
        logging.error(msg)
        log_summary(msg)

if __name__ == "__main__":
    try:
        compare_data()
    except Exception as e:
        msg = f"Script failed: {e}"
        print(msg)
        logging.error(msg)
        with open(SUMMARY_FILE, "a") as f:
            f.write(f"{datetime.now()}: {msg}\n")