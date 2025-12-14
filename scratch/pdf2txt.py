import os
from pathlib import Path
from tkinter import Tk, filedialog
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


def select_folder():
    Tk().withdraw()
    return filedialog.askdirectory(title="Select folder containing PDFs")


def extract_text_pdfminer(pdf_path):
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"PDFMiner failed on {pdf_path}: {e}")
        return ""


def extract_text_ocr(pdf_path):
    print(f"Running OCR on {pdf_path}")
    text = ""
    try:
        images = convert_from_path(pdf_path)
        for image in images:
            text += pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"OCR failed on {pdf_path}: {e}")
        return ""


def process_pdf(pdf_path: Path):
    print(f"Processing: {pdf_path.name}")
    text = extract_text_pdfminer(pdf_path)

    if not text:
        text = extract_text_ocr(pdf_path)

    if text:
        txt_path = pdf_path.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved: {txt_path.name}")
    else:
        print(f"Failed to extract text from: {pdf_path.name}")


def main():
    folder = select_folder()
    if not folder:
        print("No folder selected. Exiting.")
        return

    pdf_files = list(Path(folder).rglob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return

    for pdf in pdf_files:
        process_pdf(pdf)

    print("\nAll done.")


if __name__ == "__main__":
    main()
