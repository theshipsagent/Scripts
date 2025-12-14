# -*- coding: utf-8 -*-
r"""
Forensic File Inventory -> CSV (Windows)
- Recurses a root and exports detailed metadata for triage/search.
- Fixes:
  * Ensures parent dirs exist for both CSV and LOG (prevents FileNotFoundError)
  * Raw docstring to avoid SyntaxWarning: invalid escape sequence
- Extras:
  * Matrix-green console stamping (colorized logging)
"""

import os
import sys
import csv
import argparse
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Optional deps
HAS_PYWIN32 = False
try:
    import win32security, win32api, win32con, pywintypes
    HAS_PYWIN32 = True
except Exception:
    pass

# Colorized console
HAS_COLOR = False
try:
    from colorama import init as colorama_init
    from colorama import Fore, Style
    colorama_init()
    HAS_COLOR = True
except Exception:
    class _Dummy:
        RESET_ALL = ''
    class _Fore:
        GREEN = ''
        YELLOW = ''
        RED = ''
        CYAN = ''
    class _Style:
        BRIGHT = ''
        RESET_ALL = ''
    Fore, Style = _Fore(), _Style()

import ctypes
from ctypes import wintypes

# ---------- ADS enumeration via WinAPI ----------
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_FindFirstStreamW = getattr(kernel32, "FindFirstStreamW", None)
_FindNextStreamW = getattr(kernel32, "FindNextStreamW", None)
_FindClose = kernel32.FindClose

class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [
        ("StreamSize", ctypes.c_longlong),
        ("cStreamName", ctypes.c_wchar * 296),
    ]

def list_ads(path: str) -> List[str]:
    streams = []
    if not _FindFirstStreamW:
        return streams
    data = WIN32_FIND_STREAM_DATA()
    h = _FindFirstStreamW(wintypes.LPCWSTR(path), 0, ctypes.byref(data), 0)
    if h == ctypes.c_void_p(-1).value or h is None:
        return streams
    try:
        streams.append(data.cStreamName)
        while _FindNextStreamW(h, ctypes.byref(data)) != 0:
            streams.append(data.cStreamName)
    finally:
        _FindClose(h)
    cleaned = []
    for s in streams:
        s = s.strip()
        if s == "::$DATA" or s == "":
            continue
        if s.startswith(":") and s.endswith(":$DATA"):
            s = s[1:-6]
        cleaned.append(s)
    return cleaned

def read_zone_identifier(path: str) -> str:
    zi_path = f"{path}:Zone.Identifier"
    try:
        with open(zi_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("ZoneId="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""

# ---------- Attributes helpers ----------
FILE_ATTRIBUTE_READONLY      = 0x0001
FILE_ATTRIBUTE_HIDDEN        = 0x0002
FILE_ATTRIBUTE_SYSTEM        = 0x0004
FILE_ATTRIBUTE_DIRECTORY     = 0x0010
FILE_ATTRIBUTE_ARCHIVE       = 0x0020
FILE_ATTRIBUTE_ENCRYPTED     = 0x4000
FILE_ATTRIBUTE_COMPRESSED    = 0x0800
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400

def utc_iso(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""

def get_owner(path: str) -> str:
    if not HAS_PYWIN32:
        return ""
    try:
        sd = win32security.GetFileSecurity(path, win32security.OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
        return f"{domain}\\{name}" if domain else name
    except Exception:
        return ""

def get_version_info(path: str) -> Dict[str, str]:
    if not HAS_PYWIN32:
        return {k: "" for k in ("FileVersion","ProductVersion","OriginalFilename","CompanyName","FileDescription")}
    try:
        info = win32api.GetFileVersionInfo(path, "\\")
        trans = info['VarFileInfo']['Translation'][0]
        lang_codepage = f"{trans[0]:04x}{trans[1]:04x}"
        def _q(key):
            try:
                return win32api.VerQueryValue(info, f"\\StringFileInfo\\{lang_codepage}\\{key}")
            except Exception:
                return ""
        return {
            "FileVersion": _q("FileVersion"),
            "ProductVersion": _q("ProductVersion"),
            "OriginalFilename": _q("OriginalFilename"),
            "CompanyName": _q("CompanyName"),
            "FileDescription": _q("FileDescription"),
        }
    except Exception:
        return {k: "" for k in ("FileVersion","ProductVersion","OriginalFilename","CompanyName","FileDescription")}

def hash_file(path: str, algo: str) -> str:
    algo = (algo or "").lower()
    if algo not in ("sha256","md5"):
        return ""
    h = hashlib.sha256() if algo == "sha256" else hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "ERR"

def build_row(path: str, st, args) -> Dict[str, Any]:
    drive, _ = os.path.splitdrive(path)
    name = os.path.basename(path)
    directory = os.path.dirname(path)
    ext = os.path.splitext(name)[1]

    attrs = getattr(st, "st_file_attributes", 0)
    is_readonly   = bool(attrs & FILE_ATTRIBUTE_READONLY)
    is_hidden     = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    is_system     = bool(attrs & FILE_ATTRIBUTE_SYSTEM)
    is_archive    = bool(attrs & FILE_ATTRIBUTE_ARCHIVE)
    is_encrypted  = bool(attrs & FILE_ATTRIBUTE_ENCRYPTED)
    is_compressed = bool(attrs & FILE_ATTRIBUTE_COMPRESSED)
    is_reparse    = bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    rep_tag = ""
    if hasattr(st, "st_reparse_tag"):
        rep_tag = hex(st.st_reparse_tag)

    owner = get_owner(path) if args.owner else ""

    ads_list = ""
    zone_id = ""
    if args.ads:
        try:
            ads = list_ads(path)
            ads_list = ";".join(ads)
            if "Zone.Identifier" in ads:
                zone_id = read_zone_identifier(path)
        except Exception:
            ads_list = "ERR"

    ver = {"FileVersion":"","ProductVersion":"","OriginalFilename":"","CompanyName":"","FileDescription":""}
    if args.version:
        ver = get_version_info(path)

    file_hash = hash_file(path, args.hash)

    return {
        "Drive": drive[:1],
        "FullPath": path,
        "Directory": directory,
        "Name": name,
        "Extension": ext,
        "SizeBytes": int(getattr(st, "st_size", 0)),
        "Attributes": attrs,
        "IsReadOnly": is_readonly,
        "IsHidden": is_hidden,
        "IsSystem": is_system,
        "IsArchive": is_archive,
        "IsEncrypted": is_encrypted,
        "IsCompressed": is_compressed,
        "IsReparsePoint": is_reparse,
        "ReparseTag": rep_tag,
        "CreationTimeUtc": utc_iso(getattr(st, "st_ctime", 0.0)),
        "LastWriteTimeUtc": utc_iso(getattr(st, "st_mtime", 0.0)),
        "LastAccessTimeUtc": utc_iso(getattr(st, "st_atime", 0.0)),
        "Owner": owner,
        "Hash": file_hash,
        "ADSList": ads_list,
        "ZoneId": zone_id,
        "FileVersion": ver["FileVersion"],
        "ProductVersion": ver["ProductVersion"],
        "OriginalFilename": ver["OriginalFilename"],
        "CompanyName": ver["CompanyName"],
        "FileDescription": ver["FileDescription"],
    }

def walk_files(root: str, follow_reparse: bool=False):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if not follow_reparse:
                                try:
                                    if entry.is_symlink():
                                        continue
                                    st = entry.stat(follow_symlinks=False)
                                    attrs = getattr(st, "st_file_attributes", 0)
                                    if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                                        continue
                                except Exception:
                                    pass
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            yield entry.path
                    except Exception:
                        continue
        except Exception:
            continue

# ---------- Matrix-green logging ----------
class MatrixFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lvl = record.levelname
        msg = record.getMessage()
        if HAS_COLOR:
            if record.levelno >= logging.ERROR:
                color = Fore.RED + Style.BRIGHT
            elif record.levelno >= logging.WARN:
                color = Fore.YELLOW + Style.BRIGHT
            else:
                color = Fore.GREEN + Style.BRIGHT  # "matrix green"
            reset = Style.RESET_ALL
            return f"{color}{ts} | {lvl:<7} | {msg}{reset}"
        else:
            return f"{ts} | {lvl:<7} | {msg}"

def ensure_parent(path: str):
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def resolve_desktop_default() -> str:
    # Robust Desktop resolution; fall back to current dir
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")
    return desktop if os.path.isdir(desktop) else os.getcwd()

def main():
    ap = argparse.ArgumentParser(description="Forensic file inventory to CSV (Windows)")
    ap.add_argument("--root", default="C:\\", help="Root folder/drive to scan (default C:\\)")
    ap.add_argument("--out", default=None, help="Output CSV (default Desktop\\forensic_inventory_<ts>.csv)")
    ap.add_argument("--hash", choices=["none","sha256","md5"], default="none", help="File hash to compute")
    ap.add_argument("--owner", action="store_true", help="Include file owner (slower)")
    ap.add_argument("--ads", action="store_true", help="Enumerate ADS & Zone.Identifier")
    ap.add_argument("--version", action="store_true", help="Include VersionInfo (pywin32)")
    ap.add_argument("--batch", type=int, default=2000, help="Rows per CSV write (default 2000)")
    ap.add_argument("--follow-reparse", action="store_true", help="Follow reparse points (may loop)")
    ap.add_argument("--verbose", action="store_true", help="Matrix-green per-file stamping")
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.out:
        out_csv = os.path.expandvars(os.path.expanduser(args.out))
    else:
        out_csv = os.path.join(resolve_desktop_default(), f"forensic_inventory_{ts}.csv")
    log_path = os.path.splitext(out_csv)[0] + ".log"

    # Ensure parent dirs exist BEFORE handlers
    ensure_parent(out_csv)
    ensure_parent(log_path)

    # Build logging with matrix-green console + file
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Remove default handlers if any
    for h in list(logger.handlers):
        logger.removeHandler(h)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(MatrixFormatter())
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(ch)
    logger.addHandler(fh)

    logging.info(f"Start inventory | root={args.root} | out={out_csv} | hash={args.hash} | owner={args.owner} | ads={args.ads} | version={args.version}")

    fieldnames = [
        "Drive","FullPath","Directory","Name","Extension","SizeBytes","Attributes",
        "IsReadOnly","IsHidden","IsSystem","IsArchive","IsEncrypted","IsCompressed",
        "IsReparsePoint","ReparseTag",
        "CreationTimeUtc","LastWriteTimeUtc","LastAccessTimeUtc",
        "Owner","Hash","ADSList","ZoneId",
        "FileVersion","ProductVersion","OriginalFilename","CompanyName","FileDescription"
    ]

    count = 0
    err_count = 0
    batch: List[Dict[str, Any]] = []

    # Open CSV with utf-8-sig so Excel opens cleanly
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for path in walk_files(args.root, follow_reparse=args.follow_reparse):
            try:
                st = os.stat(path, follow_symlinks=False)
                row = build_row(path, st, args)
                batch.append(row)
                count += 1

                if args.verbose:
                    logging.info(f"{path}")

                if len(batch) >= args.batch:
                    writer.writerows(batch)
                    batch.clear()
                    logging.info(f"Progress: {count:,} files...")

            except KeyboardInterrupt:
                logging.warning("Interrupted by user; flushing batch and exiting.")
                if batch:
                    writer.writerows(batch)
                break
            except Exception as e:
                err_count += 1
                logging.error(f"ERROR {path} | {e}")
                continue

        if batch:
            writer.writerows(batch)

    logging.info(f"Done. Files={count:,} | Errors={err_count:,} | CSV={out_csv} | Log={log_path}")
    print(f"\nCSV written: {out_csv}\nLog written: {log_path}")

if __name__ == "__main__":
    main()
