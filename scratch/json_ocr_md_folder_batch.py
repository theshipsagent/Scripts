import os
import json
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from tkinter import Tk, filedialog
from pdfminer.high_level import extract_text

# Ensure Tesseract is available (adjust path if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Step 1: Select folder ---
Tk().withdraw()
folder = filedialog.askdirectory(title="Select Folder to Process")
if not folder:
    exit("No folder selected.")

out_pdf = os.path.join(folder, "LLM_OCR_PDF")
out_md = os.path.join(folder, "LLM_MD")
out_json = os.path.join(folder, "LLM_JSON")

for out in [out_pdf, out_md, out_json]:
    os.makedirs(out, exist_ok=True)

# --- Step 2: Process files ---
for file in os.listdir(folder):
    filepath = os.path.join(folder, file)
    name, ext = os.path.splitext(file)
    if not os.path.isfile(filepath):
        continue

    # --- OCR and make readable PDF ---
    if ext.lower() in [".pdf", ".jpg", ".jpeg", ".png", ".tiff"]:
        try:
            if ext.lower() == ".pdf":
                pages = convert_from_path(filepath, 300)
            else:
                pages = [Image.open(filepath)]
            pdf_text = ""
            pdf_out = os.path.join(out_pdf, f"{name}_ocr.pdf")
            for page in pages:
                text = pytesseract.image_to_string(page)
                pdf_text += text + "\n"
            with open(pdf_out.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
                f.write(pdf_text)
        except Exception as e:
            print(f"OCR failed for {file}: {e}")

    # --- Markdown & JSON conversion ---
    try:
        text = ""
        if ext.lower() == ".pdf":
            text = extract_text(filepath)
        elif ext.lower() in [".txt", ".md"]:
            with open(filepath, encoding="utf-8") as f:
                text = f.read()
        else:
            continue

        # Markdown version
        md_path = os.path.join(out_md, f"{name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{text}")

        # JSON version
        json_path = os.path.join(out_json, f"{name}.json")
        json.dump({"title": name, "content": text}, open(json_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Conversion failed for {file}: {e}")

print("✅ Conversion complete. Originals retained.")
