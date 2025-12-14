# -*- coding: utf-8 -*-
"""
Aggressive PDF metadata scrubber (Windows/macOS/Linux)

Features:
- GUI folder picker (tkinter)
- Recursively cleans PDFs:
  * Strips XMP & /Info metadata
  * Removes JavaScript (/Names/JavaScript, /OpenAction, /AA)  [toggle]
  * Removes annotations (/Annots)                             [toggle]
  * Removes embedded files (/Names/EmbeddedFiles)             [toggle]
  * Regenerates document IDs
- Timestamp reset to "today" by default
- Writes clean copies to <root>/_CLEAN (set OVERWRITE=True for in-place)

Dependencies:
  pip install pikepdf
Optional (Windows created-time reset):
  pip install pywin32
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from tkinter import Tk, filedialog

# -------------------- SETTINGS --------------------
OVERWRITE = False           # True = modify files in place; False = write to <root>/_CLEAN
RESET_TIMESTAMPS = True     # Reset Modified/Accessed (and Created on Windows if pywin32 available)
REMOVE_ANNOTATIONS = True   # Remove all page annotations
REMOVE_ATTACHMENTS = True   # Remove all embedded files/attachments
REMOVE_JAVASCRIPT = True    # Remove JS actions (Names/JavaScript, OpenAction, AA)
LINEARIZE = False           # Web-optimize output; keep False for speed
LOG_LEVEL = logging.INFO
# --------------------------------------------------

# Dependencies
try:
    import pikepdf
    HAS_PIKEPDF = True
except Exception:
    HAS_PIKEPDF = False

# Optional Windows "created time" reset
try:
    import pywintypes, win32file
    HAS_WIN32FILE = True
except Exception:
    HAS_WIN32FILE = False

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

def _reset_times(path: str, dt: datetime = None) -> None:
    """Reset Modified/Accessed via os.utime; on Windows also Created if pywin32 present."""
    if dt is None:
        dt = datetime.now()
    ts = dt.timestamp()
    try:
        os.utime(path, (ts, ts))
    except Exception as e:
        logging.debug(f"utime failed for {path}: {e}")
    if HAS_WIN32FILE and os.name == "nt":
        try:
            handle = win32file.CreateFile(
                path,
                win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            ft = pywintypes.Time(dt)
            win32file.SetFileTime(handle, ft, ft, ft)  # created, accessed, modified
            handle.close()
        except Exception as e:
            logging.debug(f"SetFileTime failed for {path}: {e}")

def _strip_metadata_with_pikepdf(src_path: str, dst_path: str) -> None:
    """Open with pikepdf and aggressively drop metadata/JS/annots/attachments, then save."""
    with pikepdf.open(src_path, allow_overwriting_input=True) as pdf:
        root = pdf.Root  # NOTE: capital R (pikepdf catalog)

        # 1) Drop XMP metadata stream
        try:
            if getattr(root, "Metadata", None) is not None:
                root.Metadata = None
        except Exception:
            pass

        # 2) Clear classic DocInfo
        try:
            pdf.docinfo.clear()
        except Exception:
            pass

        # 3) Remove JavaScript hooks
        if REMOVE_JAVASCRIPT:
            try:
                if getattr(root, "Names", None):
                    names = root.Names
                    if getattr(names, "JavaScript", None):
                        del names.JavaScript
                        # If Names now empty, remove it
                        if len(names.keys()) == 0:
                            del root.Names
                if getattr(root, "OpenAction", None):
                    del root.OpenAction
                if getattr(root, "AA", None):
                    del root.AA
            except Exception:
                pass

        # 4) Remove attachments
        if REMOVE_ATTACHMENTS:
            try:
                if getattr(root, "Names", None) and getattr(root.Names, "EmbeddedFiles", None):
                    del root.Names.EmbeddedFiles
                    if len(root.Names.keys()) == 0:
                        del root.Names
            except Exception:
                pass

        # 5) Remove annotations on each page
        if REMOVE_ANNOTATIONS:
            for page in pdf.pages:
                try:
                    if "/Annots" in page.obj:
                        page.obj["/Annots"] = pikepdf.Array([])
                except Exception:
                    pass

        # 6) Save (toggle LINEARIZE for speed/size tradeoff) and regenerate IDs
        try:
            pdf.save(dst_path, static_id=False, preserve_pdfa=False, linearize=LINEARIZE)
        except Exception:
            pdf.save(dst_path, static_id=False, preserve_pdfa=False)

def process_pdf(src_path: str, dst_path: str) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    _strip_metadata_with_pikepdf(src_path, dst_path)
    if RESET_TIMESTAMPS:
        _reset_times(dst_path)

def main() -> None:
    if not HAS_PIKEPDF:
        logging.error("Missing dependency: pikepdf. Install with: pip install pikepdf")
        sys.exit(1)

    Tk().withdraw()
    root_dir = filedialog.askdirectory(title="Select ROOT folder to scrub PDFs")
    if not root_dir:
        logging.error("No folder selected. Exiting.")
        return

    out_root = root_dir if OVERWRITE else os.path.join(root_dir, "_CLEAN")

    logging.info("====================================================")
    logging.info("Aggressive PDF Metadata Scrubber")
    logging.info(f"Root: {root_dir}")
    logging.info(f"Mode: {'OVERWRITE in-place' if OVERWRITE else f'WRITE CLEAN COPIES under {out_root}'}")
    logging.info(f"Reset timestamps: {'Yes' if RESET_TIMESTAMPS else 'No'}")
    logging.info(f"Remove annotations: {'Yes' if REMOVE_ANNOTATIONS else 'No'}")
    logging.info(f"Remove attachments: {'Yes' if REMOVE_ATTACHMENTS else 'No'}")
    logging.info(f"Remove JavaScript: {'Yes' if REMOVE_JAVASCRIPT else 'No'}")
    logging.info(f"Linearize: {'Yes' if LINEARIZE else 'No (faster)'}")
    logging.info("====================================================")

    total = 0
    cleaned = 0
    failed = 0
    skipped = 0
    t0 = time.time()

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Avoid reprocessing the output folder
        if not OVERWRITE and os.path.abspath(dirpath).startswith(os.path.abspath(out_root)):
            continue

        for fname in filenames:
            if not fname.lower().endswith(".pdf"):
                continue

            total += 1
            src = os.path.join(dirpath, fname)
            rel = os.path.relpath(src, root_dir)
            dst = src if OVERWRITE else os.path.join(out_root, rel)

            try:
                print(f"[{cleaned + skipped + failed + 1}] Processing: {rel}")
                process_pdf(src, dst)
                cleaned += 1
                logging.info(f"PDF cleaned: {rel}")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                failed += 1
                logging.error(f"FAILED: {rel} | {e}")
                logging.debug(traceback.format_exc())

    dt = time.time() - t0
    logging.info("====================================================")
    logging.info(f"Done. Elapsed: {dt:0.1f}s | Total PDFs: {total} | Cleaned: {cleaned} | Failed: {failed} | Skipped: {skipped}")
    if not OVERWRITE:
        logging.info(f"Clean copies written under: {out_root}")
    logging.info("====================================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
