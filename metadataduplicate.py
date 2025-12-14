# Import necessary libraries
import os
import shutil
import logging
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from tqdm import tqdm

# Setup logging
def setup_logging(log_dir):
    log_file = os.path.join(log_dir, f"file_consolidator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return log_file

# Main function to consolidate files
def consolidate_files():
    # Select directory via Windows Explorer dialog
    root = tk.Tk()
    root.withdraw()
    source_dir = filedialog.askdirectory(title="Select Source Directory")
    if not source_dir:
        print("No directory selected. Exiting.")
        return

    # Create folders
    consolidated_dir = os.path.join(source_dir, "Consolidated_Files")
    logs_dir = os.path.join(source_dir, "Logs")
    os.makedirs(consolidated_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    log_file = setup_logging(logs_dir)
    print(f"Logging to: {log_file}")

    # Pre-analysis: Count files
    pre_counts = {'total_files': 0}
    for root_dir, _, files in os.walk(source_dir):
        pre_counts['total_files'] += len(files)
    logging.info(f"Pre-analysis: Total files: {pre_counts['total_files']}")

    # Load checkpoint for resume
    checkpoint_file = os.path.join(logs_dir, "consolidator_checkpoint.txt")
    processed_files = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as cf:
            processed_files = set(line.strip() for line in cf)
        print(f"Resuming from {len(processed_files)} processed files.")

    # Collect all files, skipping created folders
    all_files = []
    for root_dir, _, files in os.walk(source_dir):
        if root_dir == consolidated_dir or root_dir == logs_dir:
            continue
        for file in files:
            file_path = os.path.join(root_dir, file)
            if os.path.isfile(file_path):
                all_files.append(file_path)

    moved_count = 0
    error_count = 0
    start_time = time.time()
    timeout_seconds = 3600  # 1 hour timeout

    with tqdm(total=len(all_files), desc="Consolidating Files") as pbar:
        for file_path in all_files:
            if file_path in processed_files:
                pbar.update(1)
                continue

            try:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    logging.warning("Timeout reached. Stopping for resume later.")
                    print("Timeout reached. Run again to resume.")
                    break

                file_name = os.path.basename(file_path)
                dest_path = os.path.join(consolidated_dir, file_name)
                suffix_count = 0

                # Handle filename conflicts with dynamic suffix
                while os.path.exists(dest_path):
                    base, ext = os.path.splitext(file_name)
                    suffix_count += 1
                    dest_path = os.path.join(consolidated_dir, f"{base}_{suffix_count}{ext}")

                shutil.move(file_path, dest_path)
                logging.info(f"Moved: {file_path} -> {dest_path}")
                moved_count += 1

                # Update checkpoint
                with open(checkpoint_file, 'a') as cf:
                    cf.write(f"{file_path}\n")
                processed_files.add(file_path)

            except Exception as e:
                logging.error(f"Error moving {file_path}: {e}")
                error_count += 1

            pbar.update(1)

    # Post-analysis
    post_counts = {'moved': moved_count, 'errors': error_count}
    logging.info(f"Post-analysis: Moved: {post_counts['moved']}, Errors: {post_counts['errors']}")
    print("Consolidation complete. Check logs for details.")

if __name__ == "__main__":
    consolidate_files()