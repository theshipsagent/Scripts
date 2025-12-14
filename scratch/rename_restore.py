import os
import shutil
from pathlib import Path
import re

# === Configuration ===
MATCH_DIR = Path(r"C:\Users\wsd3\Proton Drive\wsdavisIII\My files\matching")
LOG_FILE = sorted(MATCH_DIR.glob("file_move_log_*.md"))[-1]  # Use the latest log file

# === Keywords to rename in filenames ===
KEYWORDS = [
    'parker' 
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# === Parse log file (markdown format) ===
move_pattern = re.compile(r"- `(.*?)`\s*→ `(.*?)`")
moved_files = []

with open(LOG_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        match = move_pattern.search(line)
        if match:
            original_path = Path(match.group(1))
            moved_path = Path(match.group(2))
            moved_files.append((original_path, moved_path))

print(f"🔍 Processing {len(moved_files)} moved files...")

renamed = []

for original_path, moved_path in moved_files:
    if not moved_path.exists():
        continue

    filename_lower = moved_path.name.lower()
    if any(keyword in filename_lower for keyword in KEYWORDS):
        new_filename = moved_path.name
        for keyword in KEYWORDS:
            new_filename = re.sub(keyword, 'zzzz', new_filename, flags=re.IGNORECASE)

        new_path = original_path.parent / new_filename

        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(moved_path), str(new_path))
            renamed.append((moved_path.name, new_path))
        except Exception as e:
            print(f"❌ Error moving {moved_path.name}: {e}")

# === Summary ===
print(f"\n✅ Renamed and restored {len(renamed)} files.")
if renamed:
    print("📋 Sample renamed:")
    for old_name, new_path in renamed[:5]:
        print(f" - {old_name} → {new_path.name}")
