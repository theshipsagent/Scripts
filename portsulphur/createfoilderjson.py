import os
import json
from pathlib import Path

# === CONFIG ===
BASE_DIR = Path(r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur\3.0_Notes")
OUTPUT_DIR = BASE_DIR.parent / "json_exports"
OUTPUT_DIR.mkdir(exist_ok=True)
PREVIEW_CHARS = 1500  # adjust preview length here

def get_file_preview(path: Path, max_chars=1500):
    """Reads a text preview from markdown, txt, or JSON files."""
    if path.suffix.lower() in [".md", ".txt", ".json"]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars)
        except:
            return ""
    return ""

def export_folder(folder_path: Path):
    data = {
        "folder_name": folder_path.name,
        "folder_path": str(folder_path),
        "files": []
    }

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(BASE_DIR)
            size_bytes = file_path.stat().st_size
            preview = get_file_preview(file_path, PREVIEW_CHARS)

            data["files"].append({
                "file_name": file,
                "relative_path": str(rel_path),
                "absolute_path": str(file_path),
                "extension": file_path.suffix,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2),
                "content_preview": preview
            })

    json_path = OUTPUT_DIR / f"{folder_path.name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported {json_path}")

# === MAIN ===
for item in BASE_DIR.iterdir():
    if item.is_dir():
        export_folder(item)

print("\n🎉 All folder JSONs created in:", OUTPUT_DIR)
