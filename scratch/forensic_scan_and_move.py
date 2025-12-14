import os
import shutil
import time
import string
import logging
import threading
import traceback
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from PyPDF2 import PdfReader
from docx import Document
from mutagen import File as MediaFile
import chardet

# === Configuration ===
DEST_DIR = r"C:\Users\wsd3\OneDrive\Desktop\dad"
LOG_FILE = os.path.join(DEST_DIR, "forensic_summary.md")
KEYWORDS = ['host agency', 'host', 't parker host', 'host terminals', 'amelia maritime']
KEYWORDS = [k.lower().translate(str.maketrans('', '', string.punctuation)) for k in KEYWORDS]
OFFICE_EXTS = ['.docx', '.doc', '.pptx', '.xlsx']
MEDIA_EXTS = ['.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv']
SCAN_EXTS = OFFICE_EXTS + MEDIA_EXTS + ['.pdf']
SCAN_TIMEOUT = 120  # seconds

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="\033[92m[%(asctime)s]\033[0m %(message)s", datefmt='%H:%M:%S')


def get_folder_from_user():
    path = input("Enter path to scan (or drag folder here): ").strip('" ')
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    return path


def read_file_content(filepath):
    ext = filepath.suffix.lower()
    try:
        if ext in ['.docx']:
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == '.pdf':
            text = ""
            with open(filepath, 'rb') as f:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        elif ext in MEDIA_EXTS:
            tags = MediaFile(str(filepath))
            return str(tags)
        else:
            with open(filepath, 'rb') as f:
                raw = f.read()
                encoding = chardet.detect(raw)['encoding'] or 'utf-8'
                return raw.decode(encoding, errors='ignore')
    except Exception as e:
        logging.error(f"Failed to read content from {filepath}: {e}")
        return ""


def contains_keyword(text):
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    return any(keyword in text for keyword in KEYWORDS)


def scan_folder(folder_path, move_matches=False):
    moved_files = []
    scanned = 0
    matched = 0
    errors = []

    logging.info(f"Scanning: {folder_path}")
    for root, _, files in os.walk(folder_path):
        for file in tqdm(files, desc="Scanning Files", leave=False):
            try:
                scanned += 1
                filepath = Path(root) / file
                if filepath.suffix.lower() not in SCAN_EXTS:
                    continue

                content = read_file_content(filepath)
                if contains_keyword(content):
                    matched += 1
                    if move_matches:
                        dest_path = Path(DEST_DIR) / filepath.name
                        shutil.copy2(filepath, dest_path)
                        moved_files.append(str(dest_path))
            except Exception as e:
                errors.append((file, str(e)))
                logging.error(f"Error on file: {file} -> {e}")

    return moved_files, scanned, matched, errors


def write_summary(moved_files, scanned, matched, errors):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Forensic Scan Summary - {datetime.now()}\n")
        f.write(f"**Total files scanned**: {scanned}\n")
        f.write(f"**Files matched and moved**: {matched}\n")
        f.write(f"**Destination**: `{DEST_DIR}`\n\n")
        f.write("## Moved Files:\n")
        for file in moved_files:
            f.write(f"- `{file}`\n")
        if errors:
            f.write("\n## Errors:\n")
            for file, err in errors:
                f.write(f"- `{file}`: {err}\n")
    logging.info(f"Summary written to: {LOG_FILE}")


def run_with_timeout(target, args=(), timeout=SCAN_TIMEOUT):
    thread = threading.Thread(target=target, args=args)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("Scan operation timed out.")


def main():
    try:
        source_dir = get_folder_from_user()

        def task():
            moved_files, scanned, matched, errors = scan_folder(source_dir, move_matches=True)
            write_summary(moved_files, scanned, matched, errors)

        run_with_timeout(task)

        logging.info("\033[92mALL DONE ✅\033[0m")
    except Exception as e:
        logging.error("\n\033[91mERROR:\033[0m " + traceback.format_exc())


if __name__ == "__main__":
    main()
