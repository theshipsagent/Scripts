import argparse
import logging
import pathlib
import sys
import time
from urllib.parse import urlparse, urljoin, unquote

import requests
from bs4 import BeautifulSoup

# ---------- Defaults ----------
START_URL = "https://www.brantleyassociation.com/southampton_project/index/"
TARGET_DIR_DEFAULT = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Ancestry"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BrantleyPDF/1.0"
TIMEOUT = 30
SLEEP = 0.15  # be polite


def ensure_dir(p: pathlib.Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def windows_safe(name: str) -> str:
    # strip characters illegal on Windows
    return "".join(c for c in name if c not in '<>:"/\\|?*').strip()


def filename_from_url(url: str) -> str:
    path = urlparse(url).path
    fn = unquote(path.split("/")[-1])
    return windows_safe(fn)


def get_pdf_links(session: requests.Session, index_url: str) -> list[str]:
    """Return absolute URLs of PDFs linked on the index page."""
    r = session.get(index_url, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = set()

    # Typical Apache/autoindex and hand-authored pages both use <a href=...>
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absu = urljoin(index_url, href)
        if absu.lower().endswith(".pdf"):
            links.add(absu)

    return sorted(links)


def head_size_if_pdf(session: requests.Session, url: str) -> int:
    """Return Content-Length if HEAD says it's a PDF; else -1."""
    try:
        h = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        if h.status_code != 200:
            return -1
        ctype = h.headers.get("Content-Type", "").lower()
        if "application/pdf" not in ctype and not url.lower().endswith(".pdf"):
            return -1
        clen = h.headers.get("Content-Length")
        return int(clen) if clen and clen.isdigit() else -1
    except Exception:
        return -1


def download_pdf(session: requests.Session, url: str, out_dir: pathlib.Path, expected_size: int | None) -> tuple[pathlib.Path, bool]:
    """Download URL to out_dir; skip if exists with matching size. Returns (path, downloaded?)."""
    fn = filename_from_url(url)
    out_path = out_dir / fn
    ensure_dir(out_dir)

    if out_path.exists() and out_path.stat().st_size > 0:
        if expected_size is None or out_path.stat().st_size == expected_size:
            logging.info(f"[SKIP] Exists OK: {out_path.name}")
            return out_path, False

    with session.get(url, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        tmp = out_path.with_suffix(out_path.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        tmp.replace(out_path)
    logging.info(f"[OK]   Downloaded: {out_path.name}")
    return out_path, True


def main():
    ap = argparse.ArgumentParser(description="Download all PDFs from /southampton_project/index/")
    ap.add_argument("--root", default=TARGET_DIR_DEFAULT, help="Target root directory")
    ap.add_argument("--dry-run", action="store_true", help="Only print manifest (do not download)")
    ap.add_argument("--timeout", type=int, default=TIMEOUT, help="HTTP timeout seconds")
    args = ap.parse_args()

    target_root = pathlib.Path(args.root).resolve()
    out_dir = target_root / "index"
    ensure_dir(out_dir)

    # logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    logging.info(f"Crawl:  {START_URL}")
    logging.info(f"Output: {out_dir}")

    # 1) discover PDFs
    pdf_urls = get_pdf_links(session, START_URL)
    if not pdf_urls:
        logging.warning("No PDFs found on the index page.")
        return 1

    # 2) HEAD for sizes and verify content-type
    manifest = []
    total_bytes = 0
    for u in pdf_urls:
        size = head_size_if_pdf(session, u)
        if size < 0:
            logging.warning(f"[HEAD?] Skipping non-PDF or unknown size: {u}")
            continue
        manifest.append((u, size))
        total_bytes += size
        time.sleep(SLEEP)

    count = len(manifest)
    logging.info(f"Found {count} PDFs | Total size ~ {total_bytes/1024/1024:.2f} MB")

    # 3) write manifest CSV next to outputs
    manifest_path = out_dir / "_manifest_index_pdfs.csv"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("filename,url,size_bytes\n")
        for u, s in manifest:
            f.write(f"{filename_from_url(u)},{u},{s}\n")
    logging.info(f"Manifest: {manifest_path}")

    if args.dry_run:
        logging.info("Dry-run: not downloading files.")
        return 0

    # 4) download
    downloaded = 0
    for u, s in manifest:
        try:
            _, did = download_pdf(session, u, out_dir, s)
            if did:
                downloaded += 1
        except Exception as e:
            logging.error(f"[ERR] {u}: {e}")
        time.sleep(SLEEP)

    logging.info(f"Done. PDFs discovered: {count}, downloaded: {downloaded}, skipped(existing): {count - downloaded}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
