import os
import json
from pathlib import Path

# --- 📂 Base directory to scan ---
BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur\3.0_Notes")

def folder_to_json(folder: Path):
    """
    Create a JSON file inside a 'json' subfolder of the given folder,
    containing all files (including subfolders) with metadata.
    """
    metadata = []

    for root, _, files in os.walk(folder):
        for file in files:
            p = Path(root) / file
            metadata.append({
                "file_name": file,
                "relative_path": str(p.relative_to(folder)),
                "absolute_path": str(p),
                "extension": p.suffix,
                "size_bytes": p.stat().st_size
            })

    # Make "json" subfolder inside this folder
    json_dir = folder / "json"
    json_dir.mkdir(exist_ok=True)

    # Save JSON inside the json subfolder
    output_path = json_dir / f"{folder.name}_index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ JSON created: {output_path} ({len(metadata)} files)")

def main():
    for item in BASE_DIR.iterdir():
        if item.is_dir():  # Only process folders
            folder_to_json(item)

if __name__ == "__main__":
    main()
