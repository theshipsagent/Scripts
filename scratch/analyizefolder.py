import os
from pathlib import Path
from tkinter import Tk, filedialog

# 🖱️ Choose the root folder
Tk().withdraw()
root_folder = filedialog.askdirectory(title="📁 Select the root folder to summarize")

if not root_folder:
    print("❌ No folder selected. Exiting.")
    exit()

root_path = Path(root_folder)

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

print(f"\n📁 SUMMARY FOR: {root_path}\n{'='*60}\n")

# 📂 Walk through all subfolders
for folder, dirs, files in os.walk(root_path):
    folder_path = Path(folder)
    total_size = 0
    file_list = []

    # Collect all files in this folder
    for file in files:
        file_path = folder_path / file
        size = file_path.stat().st_size
        total_size += size
        file_list.append({
            "name": file,
            "size": size,
            "type": file_path.suffix or "[no extension]"
        })

    # 📊 Folder summary
    rel_path = folder_path.relative_to(root_path)
    print(f"📂 Folder: {rel_path if rel_path != Path('') else root_path.name}")
    print(f"   📄 Files: {len(file_list)}")
    print(f"   💾 Total size: {format_size(total_size)}")

    # 📑 Detailed file listing
    for f in sorted(file_list, key=lambda x: x['name'].lower()):
        print(f"      - {f['name']} | {f['type']} | {format_size(f['size'])}")
    print("-" * 60)
