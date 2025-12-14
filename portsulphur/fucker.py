import os, json, datetime
from pathlib import Path

# 📁 CHANGE THIS to your vault path:
BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur")

# 📤 The JSON file will be written here:
OUTPUT_FILE = BASE_DIR / "master_metadata.json"

data = []
now = datetime.datetime.now().strftime("%Y-%m-%d")

print(f"🚀 Scanning all files under: {BASE_DIR}\n")

for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        file_path = Path(root) / file
        data.append({
            "title": file_path.stem,
            "filename": file,
            "relative_path": str(file_path.relative_to(BASE_DIR)),
            "absolute_path": str(file_path.resolve()),
            "extension": file_path.suffix.lower().lstrip("."),
            "size_bytes": file_path.stat().st_size,
            "last_modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "indexed_on": now
        })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"✅ Done! Master JSON created at:\n{OUTPUT_FILE}")
print(f"📊 Total files indexed: {len(data)}")
