import os, json, time, logging
from datetime import datetime
from pdfminer.high_level import extract_text
from docx import Document
from tkinter import Tk, filedialog

# === CONFIG ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"convert_run_{timestamp}.log")

# --- Logging setup ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
print(f"\033[92m[INIT] Log file started at {LOG_FILE}\033[0m")

# === SELECT FOLDER ===
Tk().withdraw()
folder = filedialog.askdirectory(title="Select Folder to Convert")
if not folder:
    exit("No folder selected.")

output_md = os.path.join(folder, "LLM_MD")
os.makedirs(output_md, exist_ok=True)
resume_file = os.path.join(folder, "resume_checkpoint.json")

# === Load Resume Checkpoint ===
processed = set()
if os.path.exists(resume_file):
    try:
        with open(resume_file, "r", encoding="utf-8") as r:
            processed = set(json.load(r))
        print(f"\033[94m[RESUME] Loaded checkpoint with {len(processed)} completed files.\033[0m")
    except Exception as e:
        print(f"\033[91m[ERROR] Failed to load resume file: {e}\033[0m")
        logging.error(f"Resume load error: {e}")

dataset = []
files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
total = len(files)
start_time = time.time()

print(f"\033[96m[START] Processing {total} files in {folder}\033[0m\n")

# === MAIN LOOP ===
for i, file in enumerate(files, 1):
    if file in processed:
        continue

    path = os.path.join(folder, file)
    name, ext = os.path.splitext(file)
    ext = ext.lower()
    text = ""

    try:
        print(f"\033[92m[{i}/{total}] Processing {file}...\033[0m")

        # --- Extract text based on type ---
        if ext == ".pdf":
            text = extract_text(path)
        elif ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif ext == ".docx":
            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            print(f"\033[33m[SKIP] Unsupported file type: {file}\033[0m")
            logging.warning(f"Skipped unsupported file: {file}")
            continue

        # --- Save Markdown ---
        md_path = os.path.join(output_md, f"{name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{text.strip()}")

        # --- Append to dataset ---
        dataset.append({
            "id": name,
            "filename": file,
            "content": text.strip()
        })

        processed.add(file)
        with open(resume_file, "w", encoding="utf-8") as r:
            json.dump(list(processed), r, indent=2)

        print(f"\033[94m[OK] {file} converted and checkpoint updated.\033[0m")
        logging.info(f"Converted: {file}")

    except KeyboardInterrupt:
        print("\n\033[91m[STOP] Interrupted by user, saving progress.\033[0m")
        logging.warning("Interrupted by user.")
        break
    except Exception as e:
        print(f"\033[91m[ERROR] {file}: {e}\033[0m")
        logging.error(f"Error processing {file}: {e}")
        continue

# === FINALIZE JSON ===
json_path = os.path.join(folder, "LLM_dataset.json")
try:
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(dataset, jf, indent=2, ensure_ascii=False)
    print(f"\033[96m[COMPLETE] JSON packaged at {json_path}\033[0m")
    logging.info("Dataset JSON saved successfully.")
except Exception as e:
    print(f"\033[91m[ERROR] Could not write final JSON: {e}\033[0m")
    logging.error(f"JSON write error: {e}")

# === SUMMARY ===
runtime = time.time() - start_time
mins, secs = divmod(runtime, 60)
print(f"\n\033[94m[SUMMARY]\033[0m")
print(f"\033[92mTotal files processed: {len(processed)} / {total}\033[0m")
print(f"\033[92mElapsed time: {int(mins)}m {int(secs)}s\033[0m")
print(f"\033[92mLog file: {LOG_FILE}\033[0m")
print(f"\033[92mResume checkpoint: {resume_file}\033[0m")
print("\033[96mRun complete — safe to resume anytime.\033[0m")
