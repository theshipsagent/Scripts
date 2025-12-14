import os
import json
import datetime
from pathlib import Path

# 📁 Base directory of your vault
BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur")

AUTHOR = "William S. Davis III"
CATEGORY = "Uncategorized"
TAGS = ["due_diligence", "auto_generated"]

def create_metadata(file_path: Path):
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    metadata = {
        "title": file_path.stem,
        "filename": file_path.name,
        "relative_path": str(file_path.relative_to(BASE_DIR)),
        "absolute_path": str(file_path.resolve()),
        "extension": file_path.suffix.lstrip("."),
        "size_bytes": file_path.stat().st_size,
        "last_modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "author": AUTHOR,
        "category": CATEGORY,
        "tags": TAGS,
        "status": "draft",
        "summary": "",
        "indexed_on": now
    }
    return metadata

def main():
    print(f"🚀 Assigning metadata sidecar files for ALL files under: {BASE_DIR}\n")
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            file_path = Path(root) / file
            # skip metadata files themselves if script re-run
            if file_path.suffix == ".json":
                continue

            metadata = create_metadata(file_path)
            metadata_path = file_path.with_suffix(file_path.suffix + ".json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            print(f"✅ Metadata assigned: {metadata_path}")

    print("\n✅ All files now have metadata sidecar files.")

if __name__ == "__main__":
    main()
