import os, hashlib, shutil, re, uuid, json, sys, time
from colorama import init, Fore, Style
from datetime import datetime
from tkinter import Tk, filedialog

init(autoreset=True)

CHECKPOINT_FILE = "_checkpoint.json"
ERROR_LOG = "_error.log"

def hash_file(path, block_size=65536):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            h.update(chunk)
    return h.hexdigest()

def normalize_name(name):
    name = re.sub(r'\s*\(# Delete conflict [^)]+#\)\s*', '', name)
    name = re.sub(r'_v\d+', '', name)
    name = re.sub(r'_{2,}', '_', name)
    return name.strip()

def shorten_name(name, max_len=60):
    base, ext = os.path.splitext(name)
    if len(base) > max_len:
        base = base[:max_len]
    uid = uuid.uuid4().hex[:8]
    return f"{base}_{uid}{ext}"

def save_checkpoint(done):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done), f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def log_error(path, err):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": ts, "file": path, "error": str(err)}) + "\n")
    print(Fore.RED + f"[ERROR] {path}\n       └─ {err}")

def matrix_print(msg):
    sys.stdout.write(Fore.GREEN + msg + "\n")
    sys.stdout.flush()

def main():
    Tk().withdraw()
    folder = filedialog.askdirectory(title="Select Folder to Clean")
    if not folder:
        print(Fore.RED + "No folder selected.")
        return

    print(Fore.GREEN + f"\n>>> INITIALIZING MATRIX CLEANER <<<\n")
    print(Fore.GREEN + f"TARGET: {folder}\n")

    seen_hashes = {}
    processed = load_checkpoint()
    duplicates_dir = os.path.join(folder, "_Duplicates")
    os.makedirs(duplicates_dir, exist_ok=True)

    start_time = time.time()
    total, renamed, moved = 0, 0, 0

    try:
        for root, _, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)
                if root.endswith("_Duplicates") or path in processed:
                    continue

                try:
                    file_hash = hash_file(path)
                    if file_hash in seen_hashes:
                        dup_target = os.path.join(duplicates_dir, os.path.basename(path))
                        shutil.move(path, dup_target)
                        matrix_print(f"[DUPLICATE] → {os.path.basename(path)}")
                        moved += 1
                    else:
                        seen_hashes[file_hash] = path
                        norm_name = normalize_name(file)
                        new_name = shorten_name(norm_name)
                        new_path = os.path.join(root, new_name)
                        if new_name != file:
                            os.rename(path, new_path)
                            matrix_print(f"[RENAMED]   → {file} → {new_name}")
                            renamed += 1

                    total += 1
                    processed.add(path)
                    if total % 50 == 0:
                        save_checkpoint(processed)

                except Exception as e:
                    log_error(path, e)
                    save_checkpoint(processed)
                    print(Fore.RED + f"\n⛔ HALTING — error occurred. Resume later.\n")
                    sys.exit(1)

        save_checkpoint(processed)
        elapsed = time.time() - start_time
        print(Fore.BLUE + Style.BRIGHT +
              f"\n=== CLEANUP COMPLETE ===\n"
              f"Files scanned: {total}\n"
              f"Renamed: {renamed}\n"
              f"Duplicates moved: {moved}\n"
              f"Elapsed: {elapsed:.2f}s\n"
              f"Checkpoint: {CHECKPOINT_FILE}\n"
              f"Error log: {ERROR_LOG if os.path.exists(ERROR_LOG) else 'None'}\n")

    except KeyboardInterrupt:
        save_checkpoint(processed)
        print(Fore.RED + "\n⛔ INTERRUPTED — checkpoint saved. Resume anytime.\n")

if __name__ == "__main__":
    main()
