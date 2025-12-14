import os
import json
from pathlib import Path
from docx import Document
from PyPDF2 import PdfReader

folder = Path(r"C:\Users\wsd3\OneDrive\Desktop\WSD_Host\PPU")
output_json = folder / "ppu_combined.json"
data = {}

def read_file(path):
    ext = path.suffix.lower()
    try:
        if ext == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        elif ext == ".docx":
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".pdf":
            text = ""
            reader = PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        else:
            return None
    except Exception as e:
        return f"[Error reading {path.name}: {e}]"

for file in folder.glob("*"):
    if file.is_file():
        text = read_file(file)
        if text:
            data[file.name] = text.strip()

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Combined JSON written to {output_json}")
