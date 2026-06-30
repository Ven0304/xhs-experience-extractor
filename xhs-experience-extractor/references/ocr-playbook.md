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

## Visual Reliability Rules

Treat visual recognition quality as evidence, not as an implicit guarantee. For every page, record both readability and confidence:

- `readable` describes how much of the page can be seen: `yes | partial | no`.
- `confidence` describes how certain the extracted content came from the image rather than inference: `high | medium | low | failed`.
- `confidence_reason` explains uncertainty, such as small text, blur, dense tables, low contrast, cropping, compression, watermark overlap, or only seeing layout/chart type.

Text certainty rule: if the exact text cannot be confirmed, write `无法确认具体文字内容，只能看出大致版式/图表类型` or a similarly explicit uncertainty note. Do not invent plausible wording, numbers, materials, schedules, or method steps to make the page look complete.

Stop reading image text as source evidence when either condition is met:

- 2 consecutive pages are `confidence: low` or `confidence: failed`.
- 3 consecutive pages are `confidence: medium`, `confidence: low`, or `confidence: failed`, and the main conclusion depends on image-body text.

After stopping, use metadata, caption, tags, visible stats, comments, and any high-confidence image elements only. State that the image body could not be reliably extracted. Do not pad the final method with low-confidence image details.

## Quality Checklist

- Use `urlDefault`, not `urlPre`, for readable long images.
- Keep original dimensions for OCR/vision.
- Verify page count against the carousel count or manifest count.
- Record page-by-page notes before final synthesis.
- Record page-level confidence before using image text as evidence.
- Mark low-confidence image-derived claims with `[OCR-low-confidence]`.
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
- confidence: high | medium | low | failed
- confidence_reason: <why this confidence level was assigned>
- text_certainty_rule: if uncertain, say the exact text cannot be confirmed instead of guessing
- extracted_points:
  - <short factual point or method step>
- evidence_grade: direct fact | repeatable method | personal-fit | weak claim | evidence gap | OCR-low-confidence
- follow_up: <crop, reread, verify, or none>

page02
- role:
- readable:
- confidence:
- confidence_reason:
- text_certainty_rule:
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
- recognition_quality: <X/Y high-or-medium confidence, Z low-or-failed, stop rule triggered or not>
```

Use `readable: partial` when the main point is visible but small text, table cells, or screenshots are uncertain. Use `confidence: medium` only when the gist is supported by visible text but exact details may be incomplete. Use `confidence: low` when the page suggests a theme but key text cannot be confirmed. Use `confidence: failed` when no specific content can be extracted.

Put unsupported dramatic outcomes under `weak claim` even if the OCR is clear. If a useful claim relies entirely on low-confidence image recognition, keep it only as `[OCR-low-confidence]` or move it to risks / evidence gaps. A failed page can only support `evidence gap`; it cannot support a concrete method claim.
## Output Notes Template

```markdown
page01: author baseline, score, timeline, thesis
page02: materials/tools
page03: app/workflow details
page04: true-test platform, sequence, constraints
page05-page06: review method/OCR details
page07+: section-specific tips and final caveats
```
