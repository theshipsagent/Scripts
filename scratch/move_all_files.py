import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def select_directory(title="Select Folder"):
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def move_contents(src_dir, dest_dir):
    src = Path(src_dir)
    dest = Path(dest_dir)

    if not src.exists() or not src.is_dir():
        print(f"[ERROR] Source directory '{src}' does not exist or is not a directory.")
        return

    if not dest.exists():
        dest.mkdir(parents=True)

    for root, dirs, files in os.walk(src):
        rel_path = Path(root).relative_to(src)
        dest_subdir = dest / rel_path
        dest_subdir.mkdir(parents=True, exist_ok=True)

        # Move files
        for file_name in files:
            src_file = Path(root) / file_name
            dest_file = dest_subdir / file_name

            try:
                if dest_file.exists():
                    # Attempt overwrite
                    dest_file.unlink()
                shutil.move(str(src_file), str(dest_file))
                print(f"[MOVED] {src_file} -> {dest_file}")

            except Exception as e:
                # If overwrite fails, keep error copy
                error_file = dest_subdir / f"{dest_file.stem}_error{dest_file.suffix}"
                shutil.move(str(src_file), str(error_file))
                print(f"[CONFLICT] Saved as {error_file}")

    print("\n✅ All files moved successfully.")

def cleanup_system_cache():
    """Optional: Clears Windows temp/cache files to free space after heavy moves."""
    print("\n[INFO] Running optional cleanup...")
    os.system("del /q/f/s %TEMP%\\* >nul 2>&1")
    os.system("rd /s/q %TEMP% >nul 2>&1")
    os.system("ie4uinit.exe -ClearIconCache >nul 2>&1")
    os.system("taskkill /f /im explorer.exe >nul 2>&1 && start explorer.exe")
    print("[DONE] Temp and icon cache cleared. Explorer restarted.")

if __name__ == "__main__":
    print("📁 Select SOURCE directory to move from:")
    source = select_directory("Select source folder")
    print("📂 Select DESTINATION directory to move to:")
    destination = select_directory("Select destination folder")

    move_contents(source, destination)

    # Uncomment the line below if you want to automatically run cleanup after moves
    # cleanup_system_cache()
