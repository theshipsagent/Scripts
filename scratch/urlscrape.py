import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

URL_PATTERN = re.compile(r'https?://[^\s)>\]}\'"]+', re.IGNORECASE)
SKIP_EXT = {".exe", ".dll", ".bin", ".jpg", ".png", ".gif", ".zip", ".7z", ".mp4", ".mov", ".iso"}

def select_folder():
    return filedialog.askdirectory(title="Select a folder to scan for URLs")

def select_save_location():
    return filedialog.asksaveasfilename(
        title="Save extracted URLs as...",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

def extract_urls_from_file(file_path):
    urls = set()
    try:
        with open(file_path, "r", errors="ignore") as f:
            content = f.read()
            urls.update(URL_PATTERN.findall(content))
    except Exception:
        try:
            with open(file_path, "rb") as f:
                content = f.read().decode(errors="ignore")
                urls.update(URL_PATTERN.findall(content))
        except Exception:
            pass
    return urls

def main():
    root = tk.Tk()
    root.withdraw()

    folder = select_folder()
    if not folder:
        print("[❌] No folder selected. Exiting.")
        return

    print(f"[📁] Scanning folder: {folder}")
    all_urls = set()
    scanned = 0

    for root_dir, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root_dir, file)
            ext = os.path.splitext(file_path)[1].lower()
            scanned += 1

            if ext in SKIP_EXT:
                print(f"[⏩] Skipping binary: {file}")
                continue

            print(f"[🔍] Scanning: {file_path}")
            urls = extract_urls_from_file(file_path)
            if urls:
                print(f"   ↳ Found {len(urls)} URLs")
                all_urls.update(urls)

    print(f"\n[✅] Scanned {scanned} files. Found {len(all_urls)} unique URLs.")

    if not all_urls:
        messagebox.showinfo("No URLs Found", "No URLs were found.")
        return

    save_path = select_save_location()
    if not save_path:
        print("[❌] No save location chosen. Exiting.")
        return

    with open(save_path, "w", encoding="utf-8") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print(f"[💾] URLs saved to: {save_path}")
    messagebox.showinfo("Success", f"Extracted {len(all_urls)} URLs.\nSaved to: {save_path}")

if __name__ == "__main__":
    main()
