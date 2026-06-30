#!/usr/bin/env python3
"""Extract and download full-resolution images from a Xiaohongshu note page.

This intentionally avoids driving the Xiaohongshu front end. The SSR HTML often
contains noteDetailMap -> note -> imageList with urlDefault fields.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path
from typing import Iterable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def request_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.xiaohongshu.com/",
    }


def fetch_text(url: str) -> tuple[str, dict[str, object]]:
    req = urllib.request.Request(url, headers=request_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        meta = {
            "source_url": url,
            "final_url": resp.geturl(),
            "status": getattr(resp, "status", None),
            "content_type": resp.headers.get("Content-Type"),
            "bytes": len(data),
        }
    return data.decode("utf-8", errors="replace"), meta


def read_html(args: argparse.Namespace) -> tuple[str, dict[str, object]]:
    if args.html_file:
        path = Path(args.html_file)
        text = path.read_text(encoding="utf-8", errors="replace")
        return text, {"source_file": str(path), "bytes": path.stat().st_size}
    html, meta = fetch_text(args.url)
    return html, meta


def normalize_url(raw: str) -> str:
    return unescape(raw).replace("\\u002F", "/").replace("\\/", "/")


def extract_url_defaults(html: str) -> list[str]:
    urls: list[str] = []

    # Fast path for SSR payload fields such as "urlDefault":"http:\u002F..."
    for match in re.finditer(r'"urlDefault"\s*:\s*"(http[^"<]+?)"', html):
        u = normalize_url(match.group(1))
        if "xhscdn.com" in u and u not in urls:
            urls.append(u)

    # Fallback: image scene URLs, keep default-resolution images first.
    for match in re.finditer(r'"url"\s*:\s*"(http[^"<]+?xhscdn\.com[^"<]+?)"', html):
        u = normalize_url(match.group(1))
        if "nd_dft" in u and u not in urls:
            urls.append(u)

    return urls


def extract_hint(html: str, width: int = 1400) -> str:
    image_pos = html.find("imageList")
    if image_pos < 0:
        return "imageList not found"
    return html[max(0, image_pos - 200): image_pos + width]


def image_dimensions(data: bytes) -> dict[str, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return {"width": int.from_bytes(data[16:20], "big"), "height": int.from_bytes(data[20:24], "big")}
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            if i + 2 > len(data):
                break
            length = int.from_bytes(data[i:i + 2], "big")
            if length < 2 or i + length > len(data):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                return {"height": int.from_bytes(data[i + 3:i + 5], "big"), "width": int.from_bytes(data[i + 5:i + 7], "big")}
            i += length
    return None


def extension_from(content_type: str | None, url: str) -> str:
    ct = (content_type or "").lower()
    if "png" in ct or ".png" in url.lower():
        return ".png"
    if "webp" in ct or ".webp" in url.lower():
        return ".webp"
    return ".jpg"


def download(urls: Iterable[str], out_dir: Path, strict: bool = False) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for index, url in enumerate(urls, start=1):
        try:
            req = urllib.request.Request(url, headers=request_headers())
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type")
                final_url = resp.geturl()
            ext = extension_from(content_type, url)
            path = out_dir / f"page{index:02d}{ext}"
            path.write_bytes(data)
            dims = image_dimensions(data)
            row: dict[str, object] = {
                "index": index,
                "path": str(path),
                "bytes": len(data),
                "content_type": content_type,
                "width": dims.get("width") if dims else None,
                "height": dims.get("height") if dims else None,
                "url": url,
                "final_url": final_url,
            }
            rows.append(row)
        except Exception as exc:  # Keep remaining pages recoverable.
            errors.append({"index": index, "url": url, "error": f"{type(exc).__name__}: {exc}"})
            if strict:
                raise
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Xiaohongshu note images from SSR HTML.")
    parser.add_argument("url", nargs="?", help="Full Xiaohongshu note URL, ideally with xsec_token")
    parser.add_argument("--html-file", help="Read saved HTML instead of fetching a URL, useful for tests/debugging")
    parser.add_argument("--out", required=True, help="Output directory for downloaded images")
    parser.add_argument("--manifest", default="manifest.json", help="Manifest filename inside output directory")
    parser.add_argument("--save-html", action="store_true", help="Save fetched/read HTML to source.html inside output directory")
    parser.add_argument("--hint", default="html-hint.txt", help="Hint filename inside output directory when extraction fails")
    parser.add_argument("--strict", action="store_true", help="Fail immediately on the first image download error")
    args = parser.parse_args()

    if not args.url and not args.html_file:
        parser.error("provide a URL or --html-file")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    html, source_meta = read_html(args)
    if args.save_html:
        (out_dir / "source.html").write_text(html, encoding="utf-8")

    urls = extract_url_defaults(html)
    hint = extract_hint(html)
    if not urls:
        (out_dir / args.hint).write_text(hint, encoding="utf-8")
        result = {
            "ok": False,
            "created_at": now_utc(),
            "error": "no image URLs found",
            "source": source_meta,
            "hint_file": str(out_dir / args.hint),
            "hint": hint[:1200],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    rows, errors = download(urls, out_dir, strict=args.strict)
    manifest = {
        "ok": bool(rows),
        "created_at": now_utc(),
        "source": source_meta,
        "url_count": len(urls),
        "downloaded_count": len(rows),
        "error_count": len(errors),
        "images": rows,
        "errors": errors,
    }
    (out_dir / args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if rows else 3


if __name__ == "__main__":
    raise SystemExit(main())