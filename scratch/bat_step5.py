# -*- coding: utf-8 -*-
r"""
bat_step5.py — one-shot Windows cleanup
Default actions (no flags):
  - Empty Recycle Bin (all drives)
  - Clear %TEMP% and C:\Windows\Temp
  - Clear Recent / Quick Access jump lists
  - Clear thumbnail/icon cache
  - Clear Windows Error Reporting (WER) cache

Optional:
  --browsers         Clear Chrome/Edge/Firefox caches (close browsers first)
  --wipe C D ...     Wipe FREE space on the specified drives using 'cipher /w:' (slow)
"""

import os
import sys
import time
import argparse
import ctypes
import subprocess
from datetime import datetime

# ----- Matrix-green console (colorama optional) -----
HAS_COLOR = False
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
    HAS_COLOR = True
except Exception:
    class _Fore:
        GREEN = ''
        YELLOW = ''
        RED = ''
    class _Style:
        BRIGHT = ''
        RESET_ALL = ''
    Fore = _Fore()
    Style = _Style()

def stamp(level, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if HAS_COLOR:
        color = Fore.GREEN + Style.BRIGHT if level == "INFO" else (Fore.YELLOW + Style.BRIGHT if level == "WARN" else Fore.RED + Style.BRIGHT)
        print(f"{color}{ts} | {level:<5} | {msg}{Style.RESET_ALL}")
    else:
        print(f"{ts} | {level:<5} | {msg}")

def warn(msg): stamp("WARN", msg)
def info(msg): stamp("INFO", msg)
def err(msg):  stamp("ERROR", msg)

# ----- Core cleanup helpers -----
def empty_recycle_bin():
    """Empty Recycle Bin on all drives."""
    flags = 0x0001 | 0x0002 | 0x0004  # NOCONFIRMATION | NOPROGRESSUI | NOSOUND
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        info("Recycle Bin emptied.")
    except Exception as e:
        warn(f"Recycle Bin API failed: {e}. Trying fallback delete...")
        try:
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if bitmask & (1 << i):
                    drives.append(f"{chr(65+i)}:")
            for d in drives:
                root = f"{d}\\$Recycle.Bin"
                if os.path.isdir(root):
                    for base, dirs, files in os.walk(root, topdown=False):
                        for n in files:
                            try:
                                os.remove(os.path.join(base, n))
                            except Exception:
                                pass
                        for n in dirs:
                            try:
                                os.rmdir(os.path.join(base, n))
                            except Exception:
                                pass
            info("Recycle Bin fallback purge attempted.")
        except Exception as e2:
            err(f"Recycle Bin fallback failed: {e2}")

def rm_tree(path):
    if not os.path.exists(path):
        return
    for _ in range(2):  # retry once
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                for n in files:
                    try:
                        os.remove(os.path.join(root, n))
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
            return
        except Exception:
            time.sleep(0.2)

def clear_temp():
    targets = []
    env_temp = os.environ.get("TEMP") or os.environ.get("TMP")
    if env_temp:
        targets.append(env_temp)
    windir = os.environ.get("WINDIR", r"C:\Windows")
    targets.append(os.path.join(windir, "Temp"))
    info("Clearing TEMP folders...")
    for p in targets:
        if p and os.path.isdir(p):
            rm_tree(p)

def clear_thumbnails():
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")
    if not base or not os.path.isdir(base):
        return
    info("Clearing thumbnail/icon cache...")
    for name in os.listdir(base):
        nl = name.lower()
        if (nl.startswith("thumbcache") or nl.startswith("iconcache")) and nl.endswith(".db"):
            try:
                os.remove(os.path.join(base, name))
            except Exception:
                pass

def clear_recent():
    app = os.environ.get("APPDATA", "")
    info("Clearing Recent/Quick Access...")
    for sub in (
        r"Microsoft\Windows\Recent",
        r"Microsoft\Windows\Recent\AutomaticDestinations",
        r"Microsoft\Windows\Recent\CustomDestinations",
    ):
        p = os.path.join(app, sub)
        if os.path.isdir(p):
            for n in os.listdir(p):
                try:
                    os.remove(os.path.join(p, n))
                except Exception:
                    pass

def clear_wer():
    info("Clearing Windows Error Reporting cache...")
    for p in (
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\WER"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\WER"),
    ):
        if os.path.isdir(p):
            rm_tree(p)

def clear_browser_caches():
    info("Clearing browser caches (Chrome/Edge/Firefox) — close browsers first.")
    la = os.environ.get("LOCALAPPDATA", "")
    ra = os.environ.get("APPDATA", "")
    chrome = os.path.join(la, r"Google\Chrome\User Data")
    edge   = os.path.join(la, r"Microsoft\Edge\User Data")
    ffbase = os.path.join(ra, r"Mozilla\Firefox\Profiles")

    globs = []
    for base in (chrome, edge):
        if os.path.isdir(base):
            for sub in ("Cache", "Code Cache", "GPUCache", os.path.join("Service Worker", "CacheStorage")):
                globs.append(os.path.join(base, "*", sub))
    if os.path.isdir(ffbase):
        globs += [os.path.join(ffbase, "*", "cache2"), os.path.join(ffbase, "*", "startupCache")]

    import glob
    for g in globs:
        for p in glob.glob(g):
            rm_tree(p)

def wipe_free_space(drives):
    """Use 'cipher /w:<drive>' to wipe FREE space (long-running; admin recommended)."""
    if not drives:
        return
    for d in drives:
        drive = (d.rstrip(":") + ":")
        info(f"Wiping FREE space on {drive} (cipher /w) — can take hours.")
        try:
            subprocess.run(["cmd.exe", "/c", "cipher", f"/w:{drive}"], check=False, creationflags=0x08000000)
        except Exception as e:
            err(f"cipher failed on {drive}: {e}")

# ----- main -----
def main():
    parser = argparse.ArgumentParser(description="One-shot Windows cleanup (no subcommands).")
    parser.add_argument("--browsers", action="store_true", help="Also clear Chrome/Edge/Firefox caches (close browsers first)")
    parser.add_argument("--wipe", nargs="*", metavar="DRIVE", help="Wipe FREE space on drives (e.g., --wipe C D)")
    args = parser.parse_args()

    if os.name != "nt":
        err("This script is Windows-only.")
        sys.exit(1)

    info("Starting cleanup")
    empty_recycle_bin()
    clear_temp()
    clear_recent()
    clear_thumbnails()
    clear_wer()

    if args.browsers:
        clear_browser_caches()

    if args.wipe:
        wipe_free_space(args.wipe)

    info("Cleanup complete.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        warn("Interrupted by user.")
