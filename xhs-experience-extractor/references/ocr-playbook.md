# OCR Playbook for Xiaohongshu Long Image Posts

Use this reference when a Xiaohongshu post carries the real article in carousel images.

## Fast Path

1. Read metadata with `opencli xiaohongshu note`.
2. Run `scripts/extract_xhs_images.py` on the full signed URL.
3. Inspect `manifest.json` for image count and file paths.
4. Read images in batches of 3-4 pages, preserving original resolution.
5. Summarize per page before synthesizing the whole post.

## Why This Saves Time

Avoid launching Xiaohongshu's front end. In prior use, browser navigation repeatedly timed out before usable screenshots appeared, while the server-rendered HTML already contained `imageList` with full image URLs.

Avoid broad HTML dumps. Search for `imageList` or use the script; dumping the full page can produce hundreds of thousands of tokens.

Avoid PowerShell `.Split()` mistakes. `.Split('"urlDefault":"')` splits on every character in the string. Use `[string[]]` delimiters or the Python script.

## OCR Options

Prefer local OCR if installed:

```powershell
Get-Command tesseract -ErrorAction SilentlyContinue
```

If no OCR exists, use visual reading in batches:

- 1-3 pages when text is dense or important.
- 3-4 pages when text is large and clean.
- Re-emit or crop only unclear pages.

## Quality Checklist

- Use `urlDefault`, not `urlPre`, for readable long images.
- Keep original dimensions for OCR/vision.
- Verify page count against the carousel count or manifest count.
- Record page-by-page notes before final synthesis.
- Separate method from anecdote and promotional phrasing.
- Do not quote long passages from the post; summarize the advice.


## Standard OCR Evidence Format

Create compact OCR notes before synthesis. Keep the notes close to the image order so later claims remain traceable.

```markdown
# OCR Evidence Notes

source: <note title or URL>
manifest: <manifest path>
coverage: <pages read>/<manifest image count>
quality: good | mixed | poor
missing_or_uncertain: <pages, comments, or metadata not available>

## Page Notes

page01
- role: hook | baseline | method | material | result | caveat
- readable: yes | partial | no
- extracted_points:
  - <short factual point or method step>
- evidence_grade: direct fact | repeatable method | personal-fit | weak claim | evidence gap
- follow_up: <crop, reread, verify, or none>

page02
- role:
- readable:
- extracted_points:
- evidence_grade:
- follow_up:

## Cross-Page Synthesis Inputs

- baseline:
- timeline:
- materials:
- workflow:
- error diagnosis:
- claimed result:
- risks / fit limits:
- uncertain pages:
```

Use `readable: partial` when the main point is clear but small text, table cells, or screenshots are uncertain. Put unsupported dramatic outcomes under `weak claim` even if the OCR is clear.
## Output Notes Template

```markdown
page01: author baseline, score, timeline, thesis
page02: materials/tools
page03: app/workflow details
page04: true-test platform, sequence, constraints
page05-page06: review method/OCR details
page07+: section-specific tips and final caveats
```
