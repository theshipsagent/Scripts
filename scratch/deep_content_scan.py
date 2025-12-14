import os
import shutil
import string
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from PyPDF2 import PdfReader
from docx import Document
from mutagen import File as MediaFile
import chardet

# === CONFIG ===
SOURCE_DIR = r"C:\Users\wsd3\OneDrive\Desktop\dad\staging"
DEST_DIR = r"C:\Users\wsd3\OneDrive\Desktop\dad\matched"
LOG_FILE = Path(DEST_DIR) / "matched_file_log.md"

os.makedirs(DEST_DIR, exist_ok=True)

KEYWORDS = [
    'host agency',
    'host',
    't parker host',
    'host terminals',
    'amelia maritime'
]
KEYWORDS = [k.lower().translate(str.maketrans('', '', string.punctuation)) for k in KEYWORDS]

OFFICE_EXTS = ['.docx']
PDF_EXTS = ['.pdf']
MEDIA_EXTS = ['.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv']


def clean_text(text):
    return text.lower().translate(str.maketrans('', '', string.punctuation))


def contains_keywords(text):
    text = clean_text(text)
    return any(kw in text for kw in KEYWORDS)


def read_file_content(path: Path):
    try:
        ext = path.suffix.lower()
        if ext in OFFICE_EXTS:
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in PDF_EXTS:
            text = ""
            with open(path, 'rb') as f:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        elif ext in MEDIA_EXTS:
            tags = MediaFile(str(path))
            return str(tags)
        else:
            with open(path, 'rb') as f:
                raw = f.read()
                encoding = chardet.detect(raw)['encoding'] or 'utf-8'
                return raw.decode(encoding, errors='ignore')
    except Exception as e:
        return f"[ERROR] Could not read: {e}"


def log_match(original: Path, dest: Path):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"- `{original}` → `{dest}`\n")


def scan_and_move():
    matched = []

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## Deep Scan Log - {datetime.now()}\n")

    for file in tqdm(os.listdir(SOURCE_DIR), desc="Scanning files for keywords"):
        src_path = Path(SOURCE_DIR) / file
        if not src_path.is_file():
            continue

        content = read_file_content(src_path)

        if isinstance(content, str) and contains_keywords(content):
            dest_path = Path(DEST_DIR) / src_path.name
            if dest_path.exists():
                dest_path = get_versioned_filename(dest_path)
            shutil.move(str(src_path), str(dest_path))
            matched.append(str(dest_path))
            log_match(src_path, dest_path)

    print(f"\n✅ {len(matched)} files matched and moved.")
    print(f"📄 Match log saved to: {LOG_FILE}")


def get_versioned_filename(path: Path) -> Path:
    base = path.stem
    ext = path.suffix
    for i in range(2, 100):
        new_path = path.parent / f"{base}_v{i}{ext}"
        if not new_path.exists():
            return new_path
    raise FileExistsError(f"Too many versions for {path.name}")


if __name__ == "__main__":
    scan_and_move()
