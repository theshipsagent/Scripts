import os
import re
import tkinter as tk
from tkinter import filedialog
from openpyxl import load_workbook
from openpyxl.packaging.core import DocumentProperties

# Domains to scrub from metadata
TARGET_DOMAINS = ["tparkerhost.com", "hostagency.com"]

def strip_domains(value: str):
    if not value:
        return None
    for domain in TARGET_DOMAINS:
        value = re.sub(domain, "[REDACTED]", value, flags=re.IGNORECASE)
    return value

def clean_metadata(file_path: str):
    try:
        wb = load_workbook(file_path, data_only=True)
        props: DocumentProperties = wb.properties

        # --- Clear standard metadata ---
        props.creator = None
        props.last_modified_by = None
        props.title = None
        props.subject = None
        props.description = None
        props.keywords = None
        props.category = None
        props.content_status = None
        props.identifier = None
        props.language = None
        props.revision = None
        props.version = None
        props.created = None
        props.modified = None
        props.last_printed = None

        # --- Scrub domains from metadata fields ---
        for attr in ["comments", "description", "keywords", "identifier"]:
            if hasattr(props, attr):
                setattr(props, attr, strip_domains(getattr(props, attr)))

        # --- Try to remove any external connections referencing old domains ---
        try:
            if hasattr(wb, "_external_links"):
                wb._external_links = []
        except Exception:
            pass

        # --- Scrub defined name comments ---
        for dn in wb.defined_names.definedName:
            if any(domain in (dn.comment or "") for domain in TARGET_DOMAINS):
                dn.comment = "[REDACTED]"

        wb.save(file_path)
        print(f"✅ Cleaned: {file_path}")
    except Exception as e:
        print(f"⚠️ Skipped {file_path} (error: {e})")

def scrub_folder(root_folder: str):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith((".xlsx", ".xlsm")):
                clean_metadata(os.path.join(root, file))

if __name__ == "__main__":
    # Hide Tkinter main window
    root = tk.Tk()
    root.withdraw()

    print("📂 Select the folder to clean Excel files...")
    folder = filedialog.askdirectory(title="Select root folder for Excel scrub")

    if not folder:
        print("❌ No folder selected. Exiting.")
    else:
        print(f"🚀 Starting metadata scrub for all Excel files under:\n{folder}\n")
        scrub_folder(folder)
        print("\n✅ Done! All Excel files cleaned.")
