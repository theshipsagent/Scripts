import os
import json
from pathlib import Path

BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur")
OUTPUT_FILE = "master_metadata.json"

def main():
    all_metadata = []
    print(f"📦 Building master metadata index from sidecar files...\n")

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".json"):
                sidecar_path = Path(root) / file
                with open(sidecar_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_metadata.append(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(all_metadata, out, indent=2)

    print(f"✅ Master metadata JSON created: {OUTPUT_FILE}")
    print(f"📊 Total files indexed: {len(all_metadata)}")

if __name__ == "__main__":
    main()
