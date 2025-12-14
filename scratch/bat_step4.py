# -*- coding: utf-8 -*-
"""
Aggressive Office metadata scrubber (FINAL)
- Cleans modern Office files IN PLACE (docx/xlsx/pptx + macro variants)
- Moves legacy formats to a flat "DEPRECIATED" subfolder (timestamps preserved)
- Resets timestamps on cleaned files to randomized values AFTER 2025-05-15,
  biased toward the last 30–90 days for a natural footprint
- GUI folder picker (tkinter), print-stamped logs, robust error handling
- Atomic writes: cleaned content written to temp, then replaces original

Tested on Windows. Requires no external libs for OOXML. Optional pywin32 improves Created-time reset.
"""

import os
import io
import sys
import time
import shutil
import zipfile
import logging
import traceback
import random
from datetime import datetime, timedelta
from tkinter import Tk, filedialog

# -------------------- SETTINGS (you can tweak safely) --------------------
DEPRECIATED_FOLDER_NAME = "DEPRECIATED"   # Subfolder created in the chosen root
BIAS_SCALE_DAYS = 45.0                    # Smaller => more bias toward recent (30–90 days typical)
EARLIEST_ALLOWED = datetime(2025, 5, 16)  # Must be AFTER May 15, 2025, per your requirement
RANDOMIZE_WITHIN_DAY = True               # Random seconds within the chosen day
LOG_LEVEL = logging.INFO                  # INFO or WARNING for less chatter
# ------------------------------------------------------------------------

# Extensions
OOXML_EXTS = {".docx", ".docm", ".xlsx", ".xlsm", ".pptx", ".pptm"}
LEGACY_EXTS = {".doc", ".dot", ".xls", ".xlt", ".ppt", ".pot", ".pps"}

# OOXML metadata paths
CORE_XML_PATH = "docProps/core.xml"
APP_XML_PATH = "docProps/app.xml"
CUSTOM_XML_PATH = "docProps/custom.xml"
THUMBNAIL_PATH = "docProps/thumbnail.jpeg"

# Minimal metadata payloads (strip identifiers, authors, etc.)
_MIN_CORE_XML = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
</cp:coreProperties>
"""

_MIN_APP_XML = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application></Application>
  <Company></Company>
  <TotalTime>0</TotalTime>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
</Properties>
"""

# Optional: pywin32 for Created-time reset
try:
    import pywintypes, win32file
    HAS_WIN32FILE = True
except Exception:
    HAS_WIN32FILE = False

# Logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

def choose_root_folder():
    Tk().withdraw()
    root_dir = filedialog.askdirectory(title="Select ROOT folder to scrub Office files (FINAL)")
    return root_dir

# -------------------- Timestamp utilities --------------------

def _random_timestamp_after(min_dt: datetime) -> datetime:
    """
    Pick a random datetime in [min_dt, now], biased toward recent dates using an exponential draw.
    Bias scale ~45 days → most picks fall within ~30–90 days of now, but always >= min_dt.
    """
    now = datetime.now()
    if min_dt >= now:
        # Edge case: if min_dt is in the future (shouldn't happen), just use now
        return now

    span_days = (now - min_dt).days
    if span_days <= 1:
        chosen = now
    else:
        # Exponential draw in days, biased toward 0 (now), clamp to span
        # expovariate takes rate λ = 1/scale
        days_back = int(min(random.expovariate(1.0 / BIAS_SCALE_DAYS), span_days))
        chosen = now - timedelta(days=days_back)

    if RANDOMIZE_WITHIN_DAY:
        # Randomize within the chosen day to avoid identical hh:mm:ss
        rand_seconds = random.randint(0, 23*3600 + 59*60 + 59)
        chosen = chosen.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=rand_seconds)

    # Make sure we never go earlier than min_dt
    if chosen < min_dt:
        chosen = min_dt + timedelta(seconds=random.randint(0, 23*3600 + 59*60 + 59)) if RANDOMIZE_WITHIN_DAY else min_dt
    # And never later than now
    now = datetime.now()
    if chosen > now:
        chosen = now

    return chosen

def _reset_times_all(path: str, target_dt: datetime):
    """
    Reset Modified/Accessed via os.utime; on Windows also reset Created time if pywin32 is available.
    """
    ts = target_dt.timestamp()
    try:
        os.utime(path, (ts, ts))  # access, modified
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
            ft = pywintypes.Time(target_dt)
            win32file.SetFileTime(handle, ft, ft, ft)  # created, accessed, modified
            handle.close()
        except Exception as e:
            logging.debug(f"SetFileTime failed for {path}: {e}")

# -------------------- OOXML scrubbing --------------------

def _scrub_ooxml_to_bytes(src_path: str) -> bytes:
    """
    Read an OOXML package and return scrubbed bytes:
      - Replace core/app with minimal placeholders
      - Drop custom.xml and thumbnail.jpeg
      - Preserve all content parts unchanged
    """
    with zipfile.ZipFile(src_path, "r") as zin:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            have_core = False
            have_app = False

            for item in zin.infolist():
                name = item.filename

                # Drop sensitive parts
                if name in (CUSTOM_XML_PATH, THUMBNAIL_PATH):
                    continue

                # Replace metadata parts
                if name == CORE_XML_PATH:
                    zout.writestr(CORE_XML_PATH, _MIN_CORE_XML)
                    have_core = True
                    continue
                if name == APP_XML_PATH:
                    zout.writestr(APP_XML_PATH, _MIN_APP_XML)
                    have_app = True
                    continue

                # Copy everything else (content)
                data = zin.read(name)
                zout.writestr(item, data)

            # If missing, add minimal placeholders
            if not have_core:
                zout.writestr(CORE_XML_PATH, _MIN_CORE_XML)
            if not have_app:
                zout.writestr(APP_XML_PATH, _MIN_APP_XML)

        return buf.getvalue()

def _atomic_replace(path: str, new_bytes: bytes):
    """
    Safely replace a file by writing to a temp neighbor and then os.replace().
    """
    dirp, base = os.path.split(path)
    temp_path = os.path.join(dirp, f".~tmp_{base}")
    with open(temp_path, "wb") as f:
        f.write(new_bytes)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, path)

# -------------------- Legacy handling --------------------

def _ensure_depreciated(root: str) -> str:
    dst = os.path.join(root, DEPRECIATED_FOLDER_NAME)
    os.makedirs(dst, exist_ok=True)
    return dst

def _move_to_depreciated(root: str, src_path: str, rel: str):
    """
    Move a legacy file into root/DEPRECIATED (flat). If name collision, append a numeric suffix.
    Preserve original timestamps (move does that on same volume by default).
    """
    dep_dir = _ensure_depreciated(root)
    fname = os.path.basename(src_path)
    base, ext = os.path.splitext(fname)

    candidate = os.path.join(dep_dir, fname)
    if not os.path.exists(candidate):
        shutil.move(src_path, candidate)
        return candidate

    # Collision: append _2, _3, ...
    n = 2
    while True:
        alt = os.path.join(dep_dir, f"{base}_{n}{ext}")
        if not os.path.exists(alt):
            shutil.move(src_path, alt)
            return alt
        n += 1

# -------------------- Main walk --------------------

def main():
    root = choose_root_folder()
    if not root:
        logging.error("No folder selected. Exiting.")
        return

    dep_dir = _ensure_depreciated(root)

    logging.info("====================================================")
    logging.info("FINAL Office Scrubber")
    logging.info(f"Root: {root}")
    logging.info(f"Legacy files will be MOVED to: {dep_dir} (flat)")
    logging.info(f"OOXML files cleaned IN PLACE (aggressive metadata strip)")
    logging.info("Timestamps on cleaned files randomized AFTER 2025-05-15, biased recent")
    logging.info("====================================================")

    total = 0
    cleaned = 0
    moved_legacy = 0
    skipped = 0
    failed = 0

    t0 = time.time()

    # Walk the tree, but do not recurse into DEPRECIATED to avoid loops
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip the DEPRECIATED folder itself
        if os.path.abspath(dirpath) == os.path.abspath(dep_dir):
            continue

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in OOXML_EXTS and ext not in LEGACY_EXTS:
                continue

            total += 1
            src_path = os.path.join(dirpath, fname)
            rel = os.path.relpath(src_path, root)

            try:
                print(f"[{cleaned + moved_legacy + skipped + failed + 1}] {rel}")

                if ext in LEGACY_EXTS:
                    # Move legacy into DEPRECIATED (flat)
                    new_loc = _move_to_depreciated(root, src_path, rel)
                    moved_legacy += 1
                    logging.info(f"LEGACY moved -> {os.path.relpath(new_loc, root)}")
                    continue

                # OOXML: clean in place
                new_bytes = _scrub_ooxml_to_bytes(src_path)
                _atomic_replace(src_path, new_bytes)

                # Randomized timestamp (after cutoff, biased recent)
                target_dt = _random_timestamp_after(EARLIEST_ALLOWED)
                _reset_times_all(src_path, target_dt)

                cleaned += 1
                logging.info(f"OOXML cleaned: {rel}")

            except KeyboardInterrupt:
                raise
            except zipfile.BadZipFile:
                failed += 1
                logging.error(f"FAILED (corrupt OOXML?): {rel}")
                logging.debug(traceback.format_exc())
            except PermissionError as e:
                failed += 1
                logging.error(f"FAILED (permission): {rel} | {e}")
            except Exception as e:
                failed += 1
                logging.error(f"FAILED: {rel} | {e}")
                logging.debug(traceback.format_exc())

    dt = time.time() - t0
    logging.info("====================================================")
    logging.info(f"Done. Elapsed: {dt:0.1f}s")
    logging.info(f"Total matched: {total} | Cleaned (OOXML): {cleaned} | Moved legacy: {moved_legacy} | Failed: {failed} | Skipped: {skipped}")
    logging.info("====================================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
