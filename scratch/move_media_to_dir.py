import os
import shutil
from pathlib import Path
import re
from tqdm import tqdm

# === CONFIG ===
STAGING_DIR = Path(r"C:\Users\wsd3\OneDrive\Desktop\dad\staging")
LOG_FILE = STAGING_DIR / "file_move_log.md"

MEDIA_EXTS = ['.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv']

# --- Parse the move log ---
pattern = re.compile(r"- `(.*?)`\s*→ `(.*?)`")
move_map = {}

with open(LOG_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        match = pattern.search(line)
        if match:
            original_path = Path(match.group(1))
            current_path = Path(match.group(2))
            move_map[str(current_path)] = original_path


# --- Create versioned filename if needed ---
def get_versioned_filename(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.stem
    ext = path.suffix
    for i in range(2, 100):
        new_path = path.parent / f"{base}_v{i}{ext}"
        if not new_path.exists():
            return new_path
    raise FileExistsError(f"Too many versions for {path.name}")


# --- Restore files ---
moved = []

print(f"🔍 Found {len(move_map)} entries in the move log.")
print(f"📦 Scanning staging folder for remaining files to restore...")

for current_path_str, original_path in tqdm(move_map.items(), desc="Restoring files"):
    current_path = Path(current_path_str)

    # Skip if file no longer in staging
    if not current_path.exists():
        continue

    # Skip media files already restored
    if current_path.suffix.lower() in MEDIA_EXTS:
        continue

    try:
        original_path.parent.mkdir(parents=True, exist_ok=True)
        final_path = get_versioned_filename(original_path)
        shutil.move(str(current_path), str(final_path))
        moved.append((current_path.name, str(final_path)))
    except Exception as e:
        print(f"❌ Failed to move {current_path.name} → {original_path}: {e}")

# --- Summary ---
print(f"\n✅ Restored {len(moved)} non-media files back to original locations.")
if moved:
    print("📝 Sample restored:")
    for name, path in moved[:5]:
        print(f"   - {name} → {path}")
