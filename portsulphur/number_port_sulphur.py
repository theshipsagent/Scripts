import os
import re

# === CONFIG ===
BASE_DIR = r"C:\Users\wsd3\Zotero\obsidian\river_terminals\Port Sulphur"
PREFIX_PATTERN = r"^\d+(\.\d+)?_"

def strip_prefix(name: str) -> str:
    """Remove any leading numeric prefix like '1.0_' or '2.3_'."""
    return re.sub(PREFIX_PATTERN, "", name)

def rename_path(old_path: str, new_name: str) -> str:
    """Rename a file or folder and return the new path."""
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    if old_path != new_path:
        os.rename(old_path, new_path)
    return new_path

def main():
    # --- STEP 1: Get first-level subfolders ---
    subfolders = [f.path for f in os.scandir(BASE_DIR) if f.is_dir()]
    subfolders.sort()

    print(f"🚀 Starting two-level numbering (ALL files) in: {BASE_DIR}")

    for folder_index, folder in enumerate(subfolders, start=1):
        folder_name = os.path.basename(folder)
        clean_name = strip_prefix(folder_name)
        new_folder_name = f"{folder_index}.0_{clean_name}"
        new_folder_path = rename_path(folder, os.path.join(BASE_DIR, new_folder_name))
        print(f"📁 {folder_name} → {new_folder_name}")

        # --- STEP 2: Rename *all* files inside this folder ---
        files = [f.path for f in os.scandir(new_folder_path) if f.is_file()]
        files.sort()

        file_counter = 1
        for file_path in files:
            filename = os.path.basename(file_path)

            # Skip system files
            if filename.lower() in ["desktop.ini", ".ds_store"]:
                continue

            clean_file = strip_prefix(filename)
            new_filename = f"{folder_index}.{file_counter}_{clean_file}"
            rename_path(file_path, os.path.join(new_folder_path, new_filename))
            print(f"   📝 {filename} → {new_filename}")
            file_counter += 1

    print("✅ Done! All top-level folders and ALL files inside them are now numbered.")

if __name__ == "__main__":
    main()
