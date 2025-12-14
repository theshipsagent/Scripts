# -*- coding: utf-8 -*-
"""
Legacy Office metadata scrubber (DOC/XLS/PPT family)
- Targets: .doc, .dot, .xls, .xlt, .ppt, .pot, .pps
- Cleans IN PLACE using Microsoft Office COM automation
- On success: reset Created/Modified/Accessed timestamps to a randomized value AFTER 2025-05-15,
  biased toward the last 30–90 days
- On failure (locked/corrupt/password/COM error): MOVE file to a flat "ERROR" folder under the selected root
- If Office/COM is unavailable: move ALL legacy files to "ERROR"

Windows only (COM). Install of Microsoft Office required for cleaning.
"""

import os
import sys
import time
import shutil
import random
import logging
import traceback
from datetime import datetime, timedelta
from tkinter import Tk, filedialog

# -------------------- SETTINGS --------------------
ERROR_FOLDER_NAME = "ERROR"
EARLIEST_ALLOWED = datetime(2025, 5, 16)  # must be AFTER May 15, 2025
BIAS_SCALE_DAYS = 45.0                    # smaller -> stronger bias toward recent days
RANDOMIZE_WITHIN_DAY = True               # add random hh:mm:ss within chosen day
LOG_LEVEL = logging.INFO
# --------------------------------------------------

LEGACY_EXTS = {".doc", ".dot", ".xls", ".xlt", ".ppt", ".pot", ".pps"}

# Optional timestamp reset on Windows via pywin32
try:
    import pywintypes, win32file
    HAS_WIN32FILE = True
except Exception:
    HAS_WIN32FILE = False

# COM / Office
try:
    import win32com.client as win32
    import pythoncom
    HAS_COM = True
except Exception:
    HAS_COM = False

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

def choose_root_folder():
    Tk().withdraw()
    return filedialog.askdirectory(title="Select ROOT folder for LEGACY Office scrub")

def _ensure_error(root: str) -> str:
    dst = os.path.join(root, ERROR_FOLDER_NAME)
    os.makedirs(dst, exist_ok=True)
    return dst

def _move_to_error(root: str, src_path: str):
    """Move file into root/ERROR (flat). If name collision, append _2, _3, ..."""
    err_dir = _ensure_error(root)
    base = os.path.basename(src_path)
    name, ext = os.path.splitext(base)
    target = os.path.join(err_dir, base)
    if not os.path.exists(target):
        shutil.move(src_path, target)
        return target
    n = 2
    while True:
        candidate = os.path.join(err_dir, f"{name}_{n}{ext}")
        if not os.path.exists(candidate):
            shutil.move(src_path, candidate)
            return candidate
        n += 1

# -------------------- Timestamp helpers --------------------

def _random_timestamp_after(min_dt: datetime) -> datetime:
    """Random datetime in [min_dt, now], biased toward recent dates via exponential draw."""
    now = datetime.now()
    if min_dt >= now:
        return now
    span_days = (now - min_dt).days
    if span_days <= 1:
        chosen = now
    else:
        days_back = int(min(random.expovariate(1.0 / BIAS_SCALE_DAYS), span_days))
        chosen = now - timedelta(days=days_back)
    if RANDOMIZE_WITHIN_DAY:
        seconds = random.randint(0, 23*3600 + 59*60 + 59)
        chosen = chosen.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=seconds)
    if chosen < min_dt:
        chosen = min_dt
    if chosen > now:
        chosen = now
    return chosen

def _reset_times_all(path: str, target_dt: datetime):
    """Reset Modified/Accessed via os.utime; on Windows also Created if pywin32 present."""
    ts = target_dt.timestamp()
    try:
        os.utime(path, (ts, ts))
    except Exception as e:
        logging.debug(f"utime failed for {path}: {e}")
    if HAS_WIN32FILE and os.name == "nt":
        try:
            handle = win32file.CreateFile(
                path,
                win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            ft = pywintypes.Time(target_dt)
            win32file.SetFileTime(handle, ft, ft, ft)
            handle.close()
        except Exception as e:
            logging.debug(f"SetFileTime failed for {path}: {e}")

# -------------------- COM cleaning --------------------

class OfficeCleaner:
    """
    Reuses a single COM instance per app for speed.
    Falls back to moving files to ERROR on per-file exceptions.
    """
    def __init__(self):
        self.word = None
        self.excel = None
        self.ppt = None
        self.ok = HAS_COM

    def __enter__(self):
        if not self.ok:
            return self
        try:
            pythoncom.CoInitialize()
            # Lazily create apps on first need
            return self
        except Exception:
            self.ok = False
            return self

    def _ensure_word(self):
        if self.word is None:
            self.word = win32.Dispatch("Word.Application")
            self.word.Visible = False

    def _ensure_excel(self):
        if self.excel is None:
            self.excel = win32.Dispatch("Excel.Application")
            self.excel.Visible = False
            # Avoid dialogs
            self.excel.DisplayAlerts = False

    def _ensure_ppt(self):
        if self.ppt is None:
            self.ppt = win32.Dispatch("PowerPoint.Application")
            # No window
            # No explicit Visible property in PPT; control via WithWindow=False on Open

    def clean_doc_or_dot(self, path: str):
        self._ensure_word()
        # 99 = wdRDIAll (remove all doc info)
        wdRDIAll = 99
        doc = self.word.Documents.Open(path, ReadOnly=False)
        try:
            try:
                doc.RemoveDocumentInformation(wdRDIAll)
            except Exception:
                # Best-effort; some docs may not support full RDI
                pass
            doc.Save()
        finally:
            doc.Close(False)

    def clean_xls_or_xlt(self, path: str):
        self._ensure_excel()
        wb = self.excel.Workbooks.Open(path, ReadOnly=False)
        try:
            try:
                wb.RemovePersonalInformation = True
            except Exception:
                pass
            wb.Save()
        finally:
            wb.Close(SaveChanges=False)

    def clean_ppt_like(self, path: str):
        self._ensure_ppt()
        pres = self.ppt.Presentations.Open(path, WithWindow=False)
        try:
            # Remove common categories; PowerPoint doesn't support the 99 code
            for code in (1, 2, 3, 4, 5, 6, 7, 8):
                try:
                    pres.RemoveDocumentInformation(code)
                except Exception:
                    pass
            pres.Save()
        finally:
            pres.Close()

    def clean(self, path: str, ext_lower: str):
        if not self.ok:
            raise RuntimeError("COM/Office not available")
        if ext_lower in (".doc", ".dot"):
            self.clean_doc_or_dot(path)
        elif ext_lower in (".xls", ".xlt"):
            self.clean_xls_or_xlt(path)
        elif ext_lower in (".ppt", ".pot", ".pps"):
            self.clean_ppt_like(path)
        else:
            raise ValueError("Unsupported legacy extension for cleaner")

    def __exit__(self, exc_type, exc, tb):
        # Gracefully close apps
        try:
            if self.word is not None:
                self.word.Quit()
        except Exception:
            pass
        try:
            if self.excel is not None:
                self.excel.Quit()
        except Exception:
            pass
        try:
            if self.ppt is not None:
                self.ppt.Quit()
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

# -------------------- Main --------------------

def main():
    root = choose_root_folder()
    if not root:
        logging.error("No folder selected. Exiting.")
        return

    err_dir = _ensure_error(root)

    logging.info("====================================================")
    logging.info("Legacy Office Scrubber (COM)")
    logging.info(f"Root: {root}")
    logging.info(f"Error bucket: {err_dir} (flat)")
    logging.info(f"Office COM available: {HAS_COM}")
    logging.info("====================================================")

    total = 0
    cleaned = 0
    moved_error = 0
    failed = 0

    t0 = time.time()

    # If COM not available, move everything to ERROR per your B policy.
    if not HAS_COM:
        logging.warning("COM/Office not available. Moving ALL legacy files to ERROR.")
        for dirpath, _, filenames in os.walk(root):
            # don't descend into ERROR itself
            if os.path.abspath(dirpath) == os.path.abspath(err_dir):
                continue
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in LEGACY_EXTS:
                    continue
                total += 1
                src = os.path.join(dirpath, fname)
                print(f"[{moved_error + failed + 1}] -> ERROR: {os.path.relpath(src, root)}")
                try:
                    _move_to_error(root, src)
                    moved_error += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"FAILED to move (no COM): {os.path.relpath(src, root)} | {e}")
                    logging.debug(traceback.format_exc())

        dt = time.time() - t0
        logging.info("====================================================")
        logging.info(f"Done (NO COM). Elapsed: {dt:0.1f}s | Total legacy: {total} | Moved to ERROR: {moved_error} | Failed: {failed}")
        logging.info("====================================================")
        return

    with OfficeCleaner() as cleaner:
        for dirpath, _, filenames in os.walk(root):
            # Skip ERROR folder itself
            if os.path.abspath(dirpath) == os.path.abspath(err_dir):
                continue

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in LEGACY_EXTS:
                    continue

                total += 1
                src = os.path.join(dirpath, fname)
                rel = os.path.relpath(src, root)

                try:
                    print(f"[{cleaned + moved_error + failed + 1}] Cleaning: {rel}")
                    cleaner.clean(src, ext)
                    # Randomized timestamp after cutoff
                    target_dt = _random_timestamp_after(EARLIEST_ALLOWED)
                    _reset_times_all(src, target_dt)
                    cleaned += 1
                    logging.info(f"Cleaned: {rel}")
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logging.warning(f"Cleaning failed, moving to ERROR: {rel} | {e}")
                    try:
                        _move_to_error(root, src)
                        moved_error += 1
                    except Exception as m:
                        failed += 1
                        logging.error(f"FAILED to move to ERROR: {rel} | {m}")
                        logging.debug(traceback.format_exc())

    dt = time.time() - t0
    logging.info("====================================================")
    logging.info(f"Done. Elapsed: {dt:0.1f}s | Total legacy: {total} | Cleaned: {cleaned} | Moved to ERROR: {moved_error} | Failed: {failed}")
    logging.info("====================================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
