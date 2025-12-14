import os
import json
from pathlib import Path

# --- 📂 Base directory containing all topic folders ---
BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur\3.0_Notes")

def read_file_content(file_path: Path):
    """Read text from .md/.txt/.json, mark binaries with placeholder."""
    try:
        if file_path.suffix.lower() in [".md", ".txt", ".json"]:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        else:
            return f"[BINARY or NON-TEXT FILE: {file_path.name}]"
    except Exception as e:
        return f"[ERROR reading file: {e}]"

def build_json_package(folder: Path):
    """Create one combined JSON package for all files in a folder (recursive)."""
    metadata = {
        "root_folder": str(folder),
        "total_files": 0,
        "files": []
    }

    for root, _, files in os.walk(folder):
        for file in files:
            # skip our own JSON outputs
            if "json" in root and file.endswith(".json"):
                continue

            p = Path(root) / file
            metadata["files"].append({
                "relative_path": str(p.relative_to(folder)),
                "name": file,
                "extension": p.suffix,
                "size_bytes": p.stat().st_size,
                "content": read_file_content(p)
            })
            metadata["total_files"] += 1

    # make a json subfolder in this folder
    json_dir = folder / "json"
    json_dir.mkdir(exist_ok=True)

    # write package
    output_path = json_dir / f"{folder.name}_combined.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON created for {folder.name}: {output_path} ({metadata['total_files']} files)")

def main():
    for item in BASE_DIR.iterdir():
        if item.is_dir():  # only process folders
            build_json_package(item)

if __name__ == "__main__":
    main()
