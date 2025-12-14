import os
import shutil
from pathlib import Path
import re
import string

# --- Config ---
SOURCE_DIR = Path(r"C:\Users\wsd3\Proton Drive\wsdavisIII\My files\matching")
DEST_DIR = Path(r"C:\Users\wsd3\Proton Drive\wsdavisIII\My files\Consolidated_Files\Dad")
KEYWORD = "parker"
REPLACEMENT = "zzzz"

os.makedirs(DEST_DIR, exist_ok=True)

# --- Helper: normalize text (lowercase + strip punctuation) ---
def normalize(text: str) -> str:
    return text.lower().translate(str.maketrans('', '', string.punctuation))

# --- Helper: create versioned name if duplicate ---
def get_versioned_filename(dest_path: Path) -> Path:
    if not dest_path.exists():
        return dest_path
    base = dest_path.stem
    ext = dest_path.suffix
    for i in range(2, 100):
        new_path = dest_path.parent / f"{base}_v{i}{ext}"
        if not new_path.exists():
            return new_path
    raise FileExistsError(f"Too many versions for {dest_path.name}")

moved = []

for file in os.listdir(SOURCE_DIR):
    src = SOURCE_DIR / file
    if not src.is_file():
        continue

    # normalize both filename and keyword for matching
    if KEYWORD.lower() in normalize(file):
        # replace keyword (case-insensitive) with replacement
        new_name = re.sub(KEYWORD, REPLACEMENT, file, flags=re.IGNORECASE)
        dest = DEST_DIR / new_name
        dest = get_versioned_filename(dest)

        try:
            shutil.copy2(src, dest)  # copy with metadata
            moved.append((src.name, dest.name))
        except Exception as e:
            print(f"❌ Failed to process {src}: {e}")

print(f"\n✅ Processed {len(moved)} file(s). Saved in: {DEST_DIR}")
if moved:
    print("📋 Sample renamed files:")
    for old, new in moved[:5]:
        print(f" - {old} → {new}")
