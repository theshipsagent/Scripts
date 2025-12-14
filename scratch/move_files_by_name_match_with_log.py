import os
import shutil
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# === Keywords to match in filenames (case-insensitive) ===
KEYWORDS = [
    'agency', 'host', 'terminal', 'terminals',
    'agent', 'avondale', 'tpa', 'tradepoint'
]

# === Prompt for source and destination ===
SOURCE_DIR = input("Enter source folder to scan: ").strip('" ')
DEST_DIR = input("Enter destination folder for matched files: ").strip('" ')

SOURCE_DIR = Path(SOURCE_DIR)
DEST_DIR = Path(DEST_DIR)
os.makedirs(DEST_DIR, exist_ok=True)

# === Create log file ===
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = DEST_DIR / f"file_move_log_{timestamp}.md"

def write_log_entry(original: Path, destination: Path):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"- `{original}` → `{destination}`  \n")

# === Helper to get versioned filename if conflict ===
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

# === Scan and move files ===
moved = []

print("\n🔍 Scanning and moving files that match keywords...")
for root, _, files in os.walk(SOURCE_DIR):
    for file in files:
        filename = file.lower()
        if any(keyword in filename for keyword in KEYWORDS):
            src_path = Path(root) / file
            dest_path = DEST_DIR / file
            dest_path = get_versioned_filename(dest_path)
            try:
                shutil.move(str(src_path), str(dest_path))
                moved.append((src_path, dest_path))
                write_log_entry(src_path, dest_path)
            except Exception as e:
                print(f"❌ Failed to move {file}: {e}")

# === Summary ===
print(f"\n✅ Moved {len(moved)} file(s) matching keyword(s) to: {DEST_DIR}")
print(f"📝 Log saved to: {log_file}")
if moved:
    print("📋 Sample moved files:")
    for src, dest in moved[:5]:
        print(f" - {src.name} → {dest}")
