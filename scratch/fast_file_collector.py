import os
import shutil
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# --- Config ---
SOURCE_DIR = input("Enter path to scan: ").strip('" ')
DEST_DIR = r"C:\Users\wsd3\OneDrive\Desktop\dad\staging"
LOG_FILE = Path(DEST_DIR) / "file_move_log.md"

# File types to include
EXTS = ['.docx', '.doc', '.pptx', '.xlsx', '.pdf', '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv']

# Create staging folder if needed
os.makedirs(DEST_DIR, exist_ok=True)
moved = []


def get_versioned_filename(path: Path) -> Path:
    """
    If path exists, return a versioned copy like file_v2.ext, file_v3.ext, etc.
    """
    if not path.exists():
        return path

    base = path.stem
    ext = path.suffix
    parent = path.parent

    for i in range(2, 100):  # up to _v99
        new_name = f"{base}_v{i}{ext}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path

    raise FileExistsError(f"Too many versions for {path.name}")


def log_move(original: Path, dest: Path, log_file: Path):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"- `{original}` → `{dest}`  \n")


# Log header
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(f"\n\n## File Move Log - {datetime.now()}\n")

# Scan and move
for root, _, files in os.walk(SOURCE_DIR):
    for file in tqdm(files, desc="Moving files with versioning"):
        src_path = Path(root) / file
        if src_path.suffix.lower() in EXTS:
            try:
                dest_path = Path(DEST_DIR) / src_path.name
                dest_path = get_versioned_filename(dest_path)

                shutil.move(str(src_path), str(dest_path))
                moved.append(str(dest_path))

                log_move(src_path, dest_path, LOG_FILE)

            except Exception as e:
                print(f"❌ Failed to move {src_path.name}: {e}")

print(f"\n✅ {len(moved)} files moved to {DEST_DIR}")
print(f"📄 Move log written to: {LOG_FILE}")
