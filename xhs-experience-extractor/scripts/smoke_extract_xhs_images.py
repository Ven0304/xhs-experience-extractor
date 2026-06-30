#!/usr/bin/env python3
"""Local smoke test for extract_xhs_images.py.

This test does not call agent-reach, OpenCLI, Xiaohongshu, or the public
internet. It starts a localhost HTTP server that serves a minimal SSR-like note
HTML page plus two image files, then verifies that the extractor can read the
note URL, download images, and write a manifest.
"""

from __future__ import annotations

import argparse
import http.server
import json
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import ClassVar

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1x1 PNG with a valid IHDR so the extractor can detect dimensions.
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a"
    "0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c6360f8cf000003010100c9fe92ef"
    "0000000049454e44ae426082"
)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def build_html(base_url: str) -> str:
    # Keep the shape close to Xiaohongshu SSR payloads: imageList -> urlDefault.
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Local XHS Smoke Note</title></head>
<body>
<script id="__INITIAL_STATE__" type="application/json">
{{"noteDetailMap":{{"local-note":{{"note":{{"imageList":[
  {{"urlDefault":"{base_url}/images/xhscdn.com/page01.png"}},
  {{"urlDefault":"{base_url}/images/xhscdn.com/page02.png"}}
]}}}}}}}}
</script>
</body></html>
"""


class SmokeHandler(http.server.BaseHTTPRequestHandler):
    base_url: ClassVar[str]

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path.startswith("/note"):
            body = build_html(self.base_url).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path in {"/images/xhscdn.com/page01.png", "/images/xhscdn.com/page02.png"}:
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG_1X1)))
            self.end_headers()
            self.wfile.write(PNG_1X1)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def run_smoke(out: str | None = None) -> int:
    script_dir = Path(__file__).resolve().parent
    extractor = script_dir / "extract_xhs_images.py"
    if not extractor.exists():
        print(f"extractor not found: {extractor}", file=sys.stderr)
        return 1

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    SmokeHandler.base_url = base_url
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), SmokeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if out:
        out_dir = Path(out).resolve()
    else:
        out_dir = script_dir.parent / "tmp-smoke-output"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = [
            sys.executable,
            str(extractor),
            f"{base_url}/note?xsec_token=local-smoke",
            "--out",
            str(out_dir),
            "--save-html",
            "--strict",
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", timeout=30)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            return proc.returncode

        manifest_path = out_dir / "manifest.json"
        if not manifest_path.exists():
            print(f"manifest missing: {manifest_path}", file=sys.stderr)
            return 1

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        images = manifest.get("images", [])
        checks = [
            (manifest.get("ok") is True, "manifest ok is not true"),
            (manifest.get("url_count") == 2, "url_count is not 2"),
            (manifest.get("downloaded_count") == 2, "downloaded_count is not 2"),
            (manifest.get("error_count") == 0, "error_count is not 0"),
            (len(images) == 2, "images length is not 2"),
            (all(Path(row.get("path", "")).exists() for row in images), "downloaded image file missing"),
            (all(row.get("width") == 1 and row.get("height") == 1 for row in images), "image dimensions not detected"),
            ((out_dir / "source.html").exists(), "source.html missing"),
        ]
        failures = [message for passed, message in checks if not passed]
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}", file=sys.stderr)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 1

        print("PASS local xhs extractor smoke test")
        print(f"manifest: {manifest_path}")
        print(f"downloaded_count: {manifest['downloaded_count']}")
        print(f"output_dir: {out_dir}")
        return 0
    finally:
        server.shutdown()
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local smoke test for extract_xhs_images.py")
    parser.add_argument("--keep-output", action="store_true", help="Keep the workspace-local output directory")
    parser.add_argument("--out", help="Write smoke-test output to this directory")
    args = parser.parse_args()
    return run_smoke(out=args.out)


if __name__ == "__main__":
    raise SystemExit(main())