import os
import pandas as pd
import traceback
from datetime import datetime

# Hardcoded paths
DATA_DIR = r"/Input"
LOG_DIR = r"C:\Users\wsd3\OneDrive\GRoK\Logs"

# Ensure log dir exists
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
CONSISTENCY_REPORT = os.path.join(LOG_DIR, "consistency_report.csv")
RUN_LOG = os.path.join(LOG_DIR, "script_run.log")

def log_message(message: str):
    """Write timestamped messages to console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def analyze_files():
    log_message("=== Starting Consistency Check ===")

    results = []
    master_columns = set()

    try:
        files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
        log_message(f"Found {len(files)} CSV files in {DATA_DIR}")

        for file in files:
            file_path = os.path.join(DATA_DIR, file)
            log_message(f"Processing file: {file}")

            try:
                df = pd.read_csv(file_path, dtype=str)  # Force all as string to preserve values
                row_count = len(df)
                columns = df.columns.tolist()

                # Collect null percentages
                null_pct = (df.isna().sum() / len(df) * 100).round(2).to_dict()

                # Store result
                results.append({
                    "File": file,
                    "RowCount": row_count,
                    "Columns": ", ".join(columns),
                    **{f"Null%_{col}": null_pct.get(col, 0) for col in columns}
                })

                master_columns.update(columns)
                log_message(f" - Rows: {row_count}, Columns: {len(columns)}")

            except Exception as e:
                err_msg = f"ERROR reading {file}: {e}"
                log_message(err_msg)
                traceback.print_exc()

        # Build consistency DataFrame
        report_df = pd.DataFrame(results)
        report_df.to_csv(CONSISTENCY_REPORT, index=False)
        log_message(f"Consistency report saved to {CONSISTENCY_REPORT}")

        log_message(f"Master column set across all files: {sorted(master_columns)}")

    except Exception as e:
        err_msg = f"FATAL ERROR: {e}"
        log_message(err_msg)
        traceback.print_exc()

    log_message("=== Consistency Check Complete ===")

if __name__ == "__main__":
    analyze_files()
