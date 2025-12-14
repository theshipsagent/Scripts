import json
import textwrap
from pathlib import Path
from tkinter import Tk, filedialog

# Files to include
TEXT_EXTENSIONS = {".md", ".txt", ".html", ".htm"}

# Approximate max chars per chunk (you can change this)
CHARS_PER_CHUNK = 4000

def select_folder():
    Tk().withdraw()
    return filedialog.askdirectory(title="Select folder to split and package")

def collect_text_files(folder_path):
    folder = Path(folder_path)
    return [f for f in folder.rglob("*") if f.suffix.lower() in TEXT_EXTENSIONS and f.is_file()]

def chunk_text(text, chunk_size=CHARS_PER_CHUNK):
    # Use textwrap to split text into chunks of ~chunk_size characters
    return textwrap.wrap(text, width=chunk_size, break_long_words=False, break_on_hyphens=False)

def create_chunked_jsonl(files, output_path):
    with open(output_path, "w", encoding="utf-8") as out_file:
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if not content:
                    continue

                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    record = {
                        "path": str(file_path.relative_to(output_path.parent)),
                        "chunk": i + 1,
                        "content": chunk
                    }
                    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"[✓] {file_path.name} → {len(chunks)} chunk(s)")
            except Exception as e:
                print(f"[ERROR] Failed to process {file_path.name}: {e}")

def main():
    folder = select_folder()
    if not folder:
        print("No folder selected. Exiting.")
        return

    files = collect_text_files(folder)
    if not files:
        print("No supported text files found.")
        return

    output_file = Path(folder) / "docs_split.jsonl"
    create_chunked_jsonl(files, output_file)
    print(f"\n✅ All files split and saved to:\n{output_file}")

if __name__ == "__main__":
    main()
