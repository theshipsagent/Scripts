# Import necessary libraries
import os
import shutil
import hashlib
import logging
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import exifread
from tqdm import tqdm

# Setup logging
def setup_logging(log_dir):
    log_file = os.path.join(log_dir, f"duplicate_remover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return log_file

# Calculate file hash
def calculate_hash(file_path, hash_algo='sha256'):
    hash_func = hashlib.new(hash_algo)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# Extract metadata for images
def extract_metadata(file_path):
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                return {k: str(v) for k, v in tags.items() if 'Date' in k or 'Make' in k}
        return {}
    except Exception as e:
        logging.error(f"Metadata extraction failed for {file_path}: {e}")
        return {}

# Main function to handle duplicates
def remove_duplicates():
    # Select directory via Windows Explorer dialog
    root = tk.Tk()
    root.withdraw()
    source_dir = filedialog.askdirectory(title="Select Consolidated Media Directory")
    if not source_dir:
        print("No directory selected. Exiting.")
        return

    # Create archive folder and logs
    archive_dir = os.path.join(os.path.dirname(source_dir), "Archive_Duplicates")
    logs_dir = os.path.join(os.path.dirname(source_dir), "Logs")
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    log_file = setup_logging(logs_dir)
    print(f"Logging to: {log_file}")

    # Supported media extensions
    media_extensions = ('.jpeg', '.jpg', '.wmv', '.mp4', '.png', '.avi', '.mov')

    # Pre-analysis: Count files
    pre_counts = {'media_files': 0}
    media_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.lower().endswith(media_extensions)]
    pre_counts['media_files'] = len(media_files)
    logging.info(f"Pre-analysis: Media files: {pre_counts['media_files']}")

    # Load checkpoint for resume
    checkpoint_file = os.path.join(logs_dir, "dedup_checkpoint.txt")
    processed_files = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as cf:
            processed_files = set(line.strip() for line in cf)
        print(f"Resuming from {len(processed_files)} processed files.")

    # Hash tracker
    file_hashes = {}
    duplicate_count = 0
    error_count = 0
    start_time = time.time()
    timeout_seconds = 3600  # 1 hour timeout

    with tqdm(total=len(media_files), desc="Processing Duplicates") as pbar:
        for file_path in media_files:
            if file_path in processed_files:
                pbar.update(1)
                continue

            try:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    logging.warning("Timeout reached. Stopping for resume later.")
                    print("Timeout reached. Run again to resume.")
                    break

                file_hash = calculate_hash(file_path)
                file_name = os.path.basename(file_path)

                if file_hash in file_hashes:
                    # Duplicate found; check metadata
                    existing_path = file_hashes[file_hash]
                    existing_meta = extract_metadata(existing_path)
                    new_meta = extract_metadata(file_path)
                    if existing_meta == new_meta or not existing_meta:
                        # True duplicate; move to archive
                        archive_path = os.path.join(archive_dir, file_name)
                        if os.path.exists(archive_path):
                            archive_path = os.path.join(archive_dir, f"dup_{duplicate_count}_{file_name}")
                        shutil.move(file_path, archive_path)
                        logging.info(f"Duplicate archived: {file_path} -> {archive_path}")
                        duplicate_count += 1
                    else:
                        # Different metadata; keep both
                        logging.info(f"Keeping distinct file (metadata differs): {file_path}")
                else:
                    file_hashes[file_hash] = file_path

                # Update checkpoint
                with open(checkpoint_file, 'a') as cf:
                    cf.write(f"{file_path}\n")
                processed_files.add(file_path)

            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                error_count += 1

            pbar.update(1)

    # Post-analysis
    post_counts = {'duplicates': duplicate_count, 'errors': error_count, 'remaining': len(media_files) - duplicate_count - error_count}
    logging.info(f"Post-analysis: Duplicates archived: {post_counts['duplicates']}, Errors: {post_counts['errors']}, Remaining: {post_counts['remaining']}")
    print("Duplicate removal complete. Check logs for details.")

if __name__ == "__main__":
    remove_duplicates()