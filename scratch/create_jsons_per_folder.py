import json
from pathlib import Path
from tkinter import Tk, filedialog

# File types to include
TEXT_EXTENSIONS = {".md", ".txt", ".html", ".htm", ".rst"}

def select_folder():
    Tk().withdraw()
    return filedialog.askdirectory(title="Select folder to package")

def collect_text_files(folder_path):
    folder = Path(folder_path)
    files = list(folder.rglob("*"))
    return [f for f in files if f.suffix.lower() in TEXT_EXTENSIONS and f.is_file()]

def create_jsonl(file_paths, output_path):
    with open(output_path, "w", encoding="utf-8") as out_file:
        for path in file_paths:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    record = {
                        "path": str(path.relative_to(output_path.parent)),
                        "content": content
                    }
                    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    print(f"[✓] Packed: {record['path']}")
                else:
                    print(f"[!] Empty: {path.name}")
            except Exception as e:
                print(f"[ERROR] {path.name}: {e}")

def main():
    folder = select_folder()
    if not folder:
        print("No folder selected. Exiting.")
        return

    text_files = collect_text_files(folder)
    if not text_files:
        print("No supported text files found.")
        return

    output_path = Path(folder) / "docs.jsonl"
    create_jsonl(text_files, output_path)
    print(f"\n✅ Done! JSONL saved to: {output_path}")

if __name__ == "__main__":
    main()
