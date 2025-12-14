import argparse
import logging
import pathlib
import sys
import time
from urllib.parse import urlparse, urljoin, unquote

import requests
from bs4 import BeautifulSoup

# ---------- Defaults ----------
GALLERY_ROOT = "https://www.brantleyassociation.com/southampton_project/gallery/"
TARGET_DIR_DEFAULT = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Ancestry"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BrantleyGalleryJPGs/1.0"
TIMEOUT = 30
SLEEP = 0.12  # be polite


def ensure_dir(p: pathlib.Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def windows_safe(name: str) -> str:
    return "".join(c for c in name if c not in '<>:"/\\|?*').strip()


def filename_from_url(url: str) -> str:
    path = urlparse(url).path
    fn = unquote(path.split("/")[-1])
    return windows_safe(fn)


def normalize_url(base: str, href: str) -> str:
    return urljoin(base, href).split("#", 1)[0]


def is_html_response(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "").lower()
    return ("text/html" in ctype) or ctype.startswith("text/")


def looks_like_html_page(u: str) -> bool:
    path = urlparse(u).path.lower()
    return (path.endswith("/") or path.endswith(".html") or path.endswith(".htm")
            or path.split("/")[-1].find(".") == -1)


def within_gallery(u: str) -> bool:
    return u.startswith(GALLERY_ROOT)


def is_jpg_url(u: str) -> bool:
    p = urlparse(u).path.lower()
    return p.endswith(".jpg") or p.endswith(".jpeg")


def head_size_if_jpg(session: requests.Session, url: str) -> int:
    try:
        h = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        if h.status_code != 200:
            return -1
        ctype = h.headers.get("Content-Type", "").lower()
        if ("image/jpeg" not in ctype) and (not is_jpg_url(url)):
            return -1
        clen = h.headers.get("Content-Length")
        return int(clen) if clen and clen.isdigit() else -1
    except Exception:
        return -1


def download_image(session: requests.Session, url: str, out_dir: pathlib.Path, expected_size: int | None) -> tuple[pathlib.Path, bool]:
    fn = filename_from_url(url)
    # Keep subfolder structure under gallery/
    parsed = urlparse(url)
    parts = pathlib.PurePosixPath(parsed.path).parts
    try:
        idx = parts.index("gallery")
        subparts = parts[idx + 1:-1]  # subfolders below gallery, excluding file
    except ValueError:
        subparts = []
    out_subdir = out_dir.joinpath(*[windows_safe(unquote(p)) for p in subparts])
    ensure_dir(out_subdir)
    out_path = out_subdir / fn

    if out_path.exists() and out_path.stat().st_size > 0:
        if expected_size is None or out_path.stat().st_size == expected_size:
            logging.info(f"[SKIP] Exists OK: {out_path.relative_to(out_dir)}")
            return out_path, False

    with session.get(url, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        tmp = out_path.with_suffix(out_path.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        tmp.replace(out_path)

    logging.info(f"[OK]   Downloaded: {out_path.relative_to(out_dir)}")
    return out_path, True


def crawl_gallery(write_dir: pathlib.Path, download: bool):
    ensure_dir(write_dir)
    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    to_visit = [GALLERY_ROOT]
    visited = set()
    seen_imgs = set()
    manifest = []

    pages = 0
    downloaded = 0

    while to_visit:
        url = to_visit.pop(0)
        if url in visited or not within_gallery(url):
            continue
        visited.add(url)

        if not looks_like_html_page(url):
            continue

        try:
            resp = session.get(url, timeout=TIMEOUT)
        except Exception as e:
            logging.warning(f"[GET error] {url}: {e}")
            continue

        if resp.status_code != 200 or not is_html_response(resp):
            continue

        pages += 1
        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            absu = normalize_url(url, a["href"])
            if not within_gallery(absu):
                continue

            if is_jpg_url(absu):
                if absu in seen_imgs:
                    continue
                size = head_size_if_jpg(session, absu)
                if size < 0:
                    continue
                seen_imgs.add(absu)
                # store dir (subpath under gallery) for nicer indexing
                rel_dir = "/".join(urlparse(absu).path.split("/")[4:-1])  # after /southampton_project/gallery/
                manifest.append((absu, size, rel_dir))
                if download:
                    try:
                        _, did = download_image(session, absu, write_dir, size)
                        if did:
                            downloaded += 1
                    except Exception as e:
                        logging.error(f"[DL ERR] {absu}: {e}")
                time.sleep(SLEEP)
            else:
                if looks_like_html_page(absu) and absu not in visited:
                    to_visit.append(absu)

        logging.info(f"[PAGE] {url} | queued:{len(to_visit)} imgs:{len(seen_imgs)}")
        time.sleep(SLEEP)

    # Write CSV manifest
    csv_path = write_dir / "_manifest_gallery_jpgs.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("filename,url,size_bytes,subdir\n")
        for u, s, subdir in manifest:
            f.write(f"{filename_from_url(u)},{u},{s},{subdir}\n")

    # Write HTML index (clickable)
    html_path = write_dir / "_index_gallery_jpgs.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset='utf-8'><title>Gallery JPG Index</title>\n")
        f.write("<h1>Southampton Project — Gallery JPGs</h1>\n")
        f.write("<ul>\n")
        for u, s, subdir in manifest:
            name = filename_from_url(u)
            f.write(f"<li><a href='{u}' target='_blank'>{name}</a> "
                    f"({s/1024:.1f} KB) — {subdir}</li>\n")
        f.write("</ul>\n")

    logging.info(f"Pages visited: {pages} | Images found: {len(manifest)} | Manifest: {csv_path}")
    logging.info(f"HTML index: {html_path}")
    if download:
        logging.info(f"Images downloaded: {downloaded} (saved under {write_dir})")

    return 0


def main():
    ap = argparse.ArgumentParser(description="Capture all .jpg/.jpeg from gallery and write index files (CSV + HTML).")
    ap.add_argument("--root", default=TARGET_DIR_DEFAULT, help="Target root directory")
    ap.add_argument("--download", action="store_true", help="Also download images to disk")
    args = ap.parse_args()

    out_dir = pathlib.Path(args.root).resolve() / "gallery"
    ensure_dir(out_dir)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.info(f"Gallery root: {GALLERY_ROOT}")
    logging.info(f"Output dir  : {out_dir} (CSV + HTML index{', plus images' if args.download else ''})")
    return crawl_gallery(out_dir, download=args.download)


if __name__ == "__main__":
    sys.exit(main())
