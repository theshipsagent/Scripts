import os
import shutil

# Define source and destination
SOURCE_DIR = r"C:\Users\wsd3\Proton Drive\wsdavisIII\My files\Consolidated_Files"
DEST_DIR = r"C:\Users\wsd3\Proton Drive\wsdavisIII\My files\Consolidated_Files\Media"

# Ensure destination exists
os.makedirs(DEST_DIR, exist_ok=True)

# File extensions to move (lowercase, without dot)
MEDIA_EXTS = {"m4p", "wmv", "itc2", "avi", "m4v"}

def move_media_files():
    count = 0
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            ext = file.split(".")[-1].lower()
            if ext in MEDIA_EXTS:
                src_path = os.path.join(root, file)
                dest_path = os.path.join(DEST_DIR, file)

                # Handle duplicates by renaming
                if os.path.exists(dest_path):
                    base, ext_full = os.path.splitext(file)
                    i = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(DEST_DIR, f"{base}_{i}{ext_full}")
                        i += 1

                shutil.move(src_path, dest_path)
                count += 1
                print(f"Moved: {src_path} -> {dest_path}")

    print(f"✅ Done! {count} media files moved to {DEST_DIR}")

if __name__ == "__main__":
    move_media_files()
