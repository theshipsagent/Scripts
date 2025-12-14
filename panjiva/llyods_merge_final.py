"""
Lloyds Dataset Merger - FIXED FINAL VERSION
===========================================
Reads Excel files (.xls, .xlsx, .xlsm)
Skips title rows ("Report produced by...")
Deduplicates by hash
Tracks source file name
Creates logs & duplicates folders automatically
"""

import os
import pandas as pd
import glob
import logging
import hashlib
from datetime import datetime
import sys

class MatrixStyle:
    @staticmethod
    def header(text):
        print(f"\n{'=' * 80}\n{text.center(80)}\n{'=' * 80}\n")

    @staticmethod
    def section(text):
        print(f"\n{'-' * 80}\n> {text}\n{'-' * 80}")

    @staticmethod
    def info(label, value):
        print(f"  {label:<30} {value}")

    @staticmethod
    def success(msg): print(f"  [OK] {msg}")
    @staticmethod
    def warning(msg): print(f"  [WARN] {msg}")
    @staticmethod
    def error(msg): print(f"  [ERROR] {msg}")
    @staticmethod
    def progress(cur, total, name=''):
        pct = (cur/total)*100 if total>0 else 0
        print(f"\r  [{cur}/{total}] {pct:.1f}% {name}", end='', flush=True)
        if cur == total: print()

class Config:
    SOURCE_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\Llyods"
    OUTPUT_FILENAME_PREFIX = "llyods_merged_FINAL"
    DUPLICATES_FOLDER = "duplicates_review"
    LOGS_FOLDER = "merge_logs"
    DATETIME_FORMAT = "%Y%m%d_%H%M"

def setup_logging(log_dir):
    ts = datetime.now().strftime(Config.DATETIME_FORMAT)
    log_path = os.path.join(log_dir, f"merge_log_{ts}.log")
    fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh = logging.FileHandler(log_path, encoding='utf-8'); fh.setLevel(logging.DEBUG); fh.setFormatter(fmt)
    ch = logging.StreamHandler(); ch.setLevel(logging.WARNING); ch.setFormatter(fmt)
    logger = logging.getLogger('Merger'); logger.setLevel(logging.DEBUG); logger.addHandler(fh); logger.addHandler(ch)
    return logger, log_path

def ensure_dirs(base):
    dup_dir = os.path.join(base, Config.DUPLICATES_FOLDER)
    log_dir = os.path.join(base, Config.LOGS_FOLDER)
    os.makedirs(dup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    return dup_dir, log_dir

def create_row_hash(row):
    return hashlib.md5('|'.join(str(x) for x in row.values).encode()).hexdigest()

class CSVMerger:
    def __init__(self, src):
        self.source_dir = src
        self.logger = None
        self.duplicates_dir = None
        self.logs_dir = None

    def initialize(self):
        MatrixStyle.header("LLOYDS DATA MERGER - FINAL VERSION")
        MatrixStyle.section("INITIALIZATION")
        self.duplicates_dir, self.logs_dir = ensure_dirs(self.source_dir)
        self.logger, log_file = setup_logging(self.logs_dir)
        MatrixStyle.info("Source Directory", self.source_dir)
        MatrixStyle.info("Duplicates Folder", self.duplicates_dir)
        MatrixStyle.info("Logs Folder", self.logs_dir)
        MatrixStyle.success("Initialization complete")

    def find_excel_files(self):
        MatrixStyle.section("SCANNING FOR EXCEL FILES")
        self.source_dir = os.path.abspath(self.source_dir.strip().strip('"'))
        pattern = os.path.join(self.source_dir, "*.xls*")
        excel_files = glob.glob(pattern)
        excel_files = [f for f in excel_files if 'merged' not in os.path.basename(f).lower()]
        if not excel_files:
            MatrixStyle.error(f"No Excel files found in: {self.source_dir}")
            for item in os.listdir(self.source_dir):
                MatrixStyle.info("Found", item)
        else:
            MatrixStyle.info("Excel Files Found", len(excel_files))
        return excel_files

    def read_excel_smart(self, file_path):
        fn = os.path.basename(file_path)
        try:
            df_peek = pd.read_excel(file_path, nrows=2, header=None)
            first_cell = str(df_peek.iloc[0, 0]) if len(df_peek) > 0 else ""
            has_title = any(x in first_cell for x in ["Report produced", "Ship Results"])
            if has_title:
                df = pd.read_excel(file_path, skiprows=1, header=0)
            else:
                df = pd.read_excel(file_path, header=0)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df['_source_file'] = fn
            return df
        except Exception as e:
            MatrixStyle.error(f"Failed to read {fn}: {e}")
            return None

    def merge_files(self, files):
        all_dfs = []
        for i, f in enumerate(files, 1):
            MatrixStyle.progress(i-1, len(files), f"Loading: {os.path.basename(f)}")
            df = self.read_excel_smart(f)
            if df is not None and not df.empty:
                all_dfs.append(df)
        MatrixStyle.progress(len(files), len(files))
        if not all_dfs:
            MatrixStyle.error("No data loaded.")
            return None
        merged = pd.concat(all_dfs, ignore_index=True, sort=False)
        MatrixStyle.info("Rows Combined", len(merged))
        return merged

    def handle_duplicates(self, df):
        MatrixStyle.section("DE-DUPLICATION")
        df['_row_hash'] = df.drop(columns=['_source_file']).apply(create_row_hash, axis=1)
        grouped = df.groupby('_row_hash').agg(lambda x: x.iloc[0]).reset_index(drop=True)
        MatrixStyle.info("Original Rows", len(df))
        MatrixStyle.info("Unique Rows", len(grouped))
        MatrixStyle.success("Duplicates removed")
        return grouped

if __name__ == "__main__":
    merger = CSVMerger(Config.SOURCE_DIR)
    merger.initialize()
    files = merger.find_excel_files()
    if not files:
        print("\n⚠️ No Excel files found, exiting.")
        sys.exit(1)
    merged = merger.merge_files(files)
    if merged is None:
        print("\n❌ Merge failed.")
        sys.exit(1)
    deduped = merger.handle_duplicates(merged)
    output_name = f"{Config.OUTPUT_FILENAME_PREFIX}_{datetime.now().strftime(Config.DATETIME_FORMAT)}.csv"
    out_path = os.path.join(Config.SOURCE_DIR, output_name)
    deduped.to_csv(out_path, index=False)
    MatrixStyle.success(f"Saved merged CSV: {out_path}")
