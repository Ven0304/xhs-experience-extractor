# XHS Experience Extractor Skill

A Windows-only Codex skill for extracting, denoising, and synthesizing Xiaohongshu (XHS) experience posts into reusable methods, checklists, and decision notes.

This repository contains an independently packaged Xiaohongshu workflow extracted from `agent-reach`. The Xiaohongshu OpenCLI guidance that previously lived under `agent-reach` has been copied and rewritten into this skill's own [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md), so the skill no longer needs to read `agent-reach/SKILL.md` or `agent-reach/references/social.md` at runtime.

## Status

- **Primary environment:** Codex on Windows.
- **Compatibility target:** Claude Code on Windows is best-effort and theoretical; use its native file/image attachment path if available.
- **Not supported:** macOS/Linux workflows are out of scope for now.
- **Platform access:** Xiaohongshu access is read-only and goes through the external `opencli xiaohongshu ...` command.
- **Agent Reach dependency:** Not required at runtime. Agent Reach source references are documented for auditability, but the full Agent Reach skill is not part of this standalone package.

## What This Skill Does

Use this skill when the user provides a Xiaohongshu/XHS URL, `xhslink.com` short link, screenshots, OCR text, pasted post text, or asks to search Xiaohongshu for study, career, product, life, finance, travel, or application experience.

The skill is designed to:

- read Xiaohongshu post metadata with OpenCLI;
- preserve signed URLs and `xsec_token` context for `note` and `comments` calls;
- extract carousel image URLs from server-rendered HTML;
- download full-resolution images and generate `manifest.json`;
- guide OCR or visual reading in small batches;
- filter social-media filler, soft ads, and weak claims;
- synthesize reusable methods, evidence gaps, disagreement, and action plans.

## What It Does Not Do

- It does not install OpenCLI.
- It does not require `agent-reach doctor --json`.
- It does not post, comment, like, collect, follow, or perform any write action on Xiaohongshu.
- It does not promise Claude Code parity; Claude Code compatibility depends on the local tool/file/image capabilities available in that agent.
- It does not support macOS/Linux paths or shell examples yet.

## Requirements

- Windows.
- Python 3.10+ recommended for the bundled scripts.
- OpenCLI installed and available on `PATH` for live Xiaohongshu access.
- Chrome with the OpenCLI extension enabled and a valid Xiaohongshu login state for logged-in platform reads.

Check local OpenCLI availability:

```powershell
Get-Command opencli -ErrorAction SilentlyContinue
```

Run a cheap Xiaohongshu smoke test before batch calls:

```powershell
opencli xiaohongshu search "<targeted query>" -f yaml
```

Interpret common results:

| Result | Meaning | Next step |
| --- | --- | --- |
| Normal YAML output | OpenCLI Xiaohongshu is usable | Continue with `search`, `note`, or `comments` |
| `BROWSER_CONNECT` / `Browser Bridge extension not connected` | Chrome or the OpenCLI extension bridge is not connected | Open Chrome, check the extension, retry one single search |
| `AUTH_REQUIRED` | Browser bridge may work, but Xiaohongshu login is missing or expired | Log into Xiaohongshu in Chrome and retry one single search |
| command not found | OpenCLI is missing or not on `PATH` | Install/fix OpenCLI; do not fall back to Agent Reach |

## OpenCLI Xiaohongshu Commands

```powershell
opencli xiaohongshu search "query" -f yaml
opencli xiaohongshu note "NOTE_URL" -f yaml
opencli xiaohongshu comments "NOTE_URL_OR_NOTE_ID" -f yaml
opencli xiaohongshu feed -f yaml
opencli xiaohongshu user USER_ID -f yaml
```

Prefer the full signed URL from search results or browser resolution, especially when `xsec_token` is present. Do not assume a bare note ID is enough for `note` or `comments`.

## Extracting Images

The bundled extractor avoids driving the Xiaohongshu front end when possible. It fetches page HTML, finds `noteDetailMap.*.note.imageList[].urlDefault`, downloads images, and writes a manifest.

```powershell
python "xhs-experience-extractor\scripts\extract_xhs_images.py" "<xhs-url>" --out "xhs-experience-extractor\xhs-note-images" --save-html
```

Expected output includes:

- downloaded image files such as `page01.jpg` or `page01.png`;
- `manifest.json` with source metadata, URL count, downloaded count, image paths, dimensions, and errors;
- optional `source.html` when `--save-html` is used.

## Local Smoke Test

A pure local smoke test is included to verify the extractor without Agent Reach, OpenCLI, Xiaohongshu, or public internet access.

```powershell
python "xhs-experience-extractor\scripts\smoke_extract_xhs_images.py"
```

The test starts a localhost fixture server, serves one simulated Xiaohongshu-like note page plus two fixture images, runs `extract_xhs_images.py`, and verifies that `manifest.json` is generated.

Successful output looks like:

```text
PASS local xhs extractor smoke test
manifest: ...\xhs-experience-extractor\tmp-smoke-output\manifest.json
downloaded_count: 2
```

`tmp-smoke-output/` is generated test output and is not part of the reusable skill source.

## Repository Layout

```text
.
├── README.md
└── xhs-experience-extractor/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   ├── opencli-xhs-usage.md
    │   └── ocr-playbook.md
    └── scripts/
        ├── extract_xhs_images.py
        └── smoke_extract_xhs_images.py
```

## Skill Files

- [`xhs-experience-extractor/SKILL.md`](xhs-experience-extractor/SKILL.md): main skill instructions and workflow.
- [`xhs-experience-extractor/references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md): self-contained Xiaohongshu OpenCLI usage guide extracted from Agent Reach.
- [`xhs-experience-extractor/references/ocr-playbook.md`](xhs-experience-extractor/references/ocr-playbook.md): OCR and long-carousel reading playbook.
- [`xhs-experience-extractor/scripts/extract_xhs_images.py`](xhs-experience-extractor/scripts/extract_xhs_images.py): local extractor for server-rendered HTML image URLs.
- [`xhs-experience-extractor/scripts/smoke_extract_xhs_images.py`](xhs-experience-extractor/scripts/smoke_extract_xhs_images.py): local extractor smoke test.

## Migration Notes

This skill is derived from the Xiaohongshu/OpenCLI portion of Agent Reach, but its runtime path is now independent:

- Agent Reach source line references are preserved in [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md) for auditability.
- Runtime instructions use direct `opencli xiaohongshu ...` commands.
- `agent-reach doctor --json` is not required.
- The local extractor and smoke test do not import or execute Agent Reach code.

## Safety And Evidence Rules

- Treat Xiaohongshu posts as noisy evidence, not authoritative truth.
- Preserve source URLs, manifest paths, page-level notes, and uncertainty labels.
- Mark missing comments, unreadable images, inaccessible short links, and OCR ambiguity as evidence gaps.
- Do not infer consensus from missing or incomplete comments.
- Summarize copyrighted post text instead of quoting long passages.