---
name: xhs-experience-extractor
description: Extract, denoise, and synthesize Xiaohongshu (XHS) experience posts into reusable Markdown methods, checklists, and decision notes. Use when the user provides a Xiaohongshu/XHS URL, xhslink short link, long image-text post, carousel screenshots/images, OCR text, pasted post text, or asks to search Xiaohongshu for study, career, product, life, finance, travel, or application experience. Handles single-post extraction, multi-post search synthesis, image OCR workflows, soft-ad/noise filtering, claim deduplication, cross-post consensus and disagreement, deleted/inaccessible posts, unreadable or garbled OCR, missing comments, and low-signal promotional content. Includes local OpenCLI Xiaohongshu usage guidance for search, note, comments, browser bridge troubleshooting, and short-link resolution.
---

# XHS Experience Extractor

Target environment: Codex on Windows. Claude Code compatibility is best-effort; do not assume macOS/Linux support.

## Core Rule

Use the local `references/opencli-xhs-usage.md` for Xiaohongshu OpenCLI access. Read that file before web actions when OpenCLI commands, local `opencli` checks, browser bridge troubleshooting, comments, or short-link resolution are relevant.

For shared short links such as `xhslink.com`, first resolve the link to the final full Xiaohongshu URL in the user's logged-in browser context when direct HTTP/OpenCLI resolution fails. Do not search the short-link code and treat a search result as the target note. A search result is only a candidate; if it cannot be verified against the opened short link or the user's supplied page title/topic, stop and ask for the full URL or browser-state access.

Do not rely on the Xiaohongshu browser page for long image-text posts unless simpler routes fail. The front end is slow and token-expensive. Prefer:

1. `opencli xiaohongshu note "<full signed URL>" -f yaml` for title, author, caption, stats, tags.
2. Direct HTML fetch and `imageList[].urlDefault` extraction for carousel images.
3. Batch image download to a temp directory.
4. OCR or visual reading in small batches.
5. Synthesis into method, assumptions, warnings, and an action plan.

## Workflow

### 1. Identify Task Type

- Specific post URL: read that note and extract image text if needed.
- Search request: search Xiaohongshu with 1-3 targeted queries, then read the strongest posts.
- Comparison request: collect multiple posts, group claims by method, and mark repeated advice versus one-off claims.

For searches, prefer concrete keywords like `雅思 听力 精听 经验`, `雅思 阅读 听力 复盘`, or the user-provided niche. Avoid broad endless browsing.

Search planning checklist:

1. Restate the user's target scenario, baseline, and decision need when available.
2. Build 1-3 query families instead of near-duplicate searches:
   - outcome query: target result plus `经验`, `复盘`, or `上岸`.
   - process query: core method/material plus `怎么练`, `避坑`, or `时间线`.
   - contrast query: failure mode, low-baseline case, or alternative method.
3. Prefer posts with concrete baseline, timeline, materials, process screenshots, or detailed failure review. De-prioritize pure resource dumps, vague motivational posts, and posts that only sell a course/tool.
4. Sample for disagreement, not just popularity: include at least one high-result method post, one constraint-heavy post, and one warning/failure post when available.
5. Stop when new posts repeat the same method without adding a new baseline, risk, material, or exception.

Before platform calls, check that `opencli` is available locally:

```powershell
Get-Command opencli -ErrorAction SilentlyContinue
```

If `opencli` is missing, report that OpenCLI is not installed or not on `PATH`; do not fall back to Agent Reach. If `opencli` exists, run one cheap Xiaohongshu smoke test before launching multiple calls:

```powershell
opencli xiaohongshu search "<targeted query>" -f yaml
```

Route the smoke-test result directly: normal YAML output means OpenCLI is usable; `BROWSER_CONNECT` or "Browser Bridge extension not connected" means Chrome or the OpenCLI extension bridge is not connected; `AUTH_REQUIRED` means Xiaohongshu login state is missing or expired. Avoid starting several parallel `opencli xiaohongshu` calls until the smoke test succeeds.

### Failure Routing

Use this routing table before improvising. Prefer the first route that still preserves evidence quality.

| Failure point | Likely cause | Next action | Stop condition |
| --- | --- | --- | --- |
| `opencli xiaohongshu search` returns `BROWSER_CONNECT` or "Browser Bridge extension not connected" | Chrome is closed, the OpenCLI extension is disabled, or the bridge has not connected yet | Check whether Chrome is running. If not, open Chrome or ask the user to open it. Then retry one single search as a smoke test before running more platform calls. If Chrome is running, ask the user to verify the OpenCLI extension is enabled/reconnected. | If the bridge still fails after Chrome is open and one retry, report the browser-bridge blocker and use only non-OpenCLI evidence if available |
| Short link cannot be resolved by HTTP/OpenCLI | `xhslink.com` requires browser or logged-in redirect context | Open the link in the user's logged-in browser context and capture the final full Xiaohongshu URL | If the final URL cannot be verified against the supplied link, title, or topic, ask for the full URL or browser-state access |
| `opencli xiaohongshu note` fails on a bare note id | Missing `xsec_token` or signed URL context | Retry with the full signed URL copied from the resolved page | If only a bare id is available and metadata cannot be fetched, continue only with clearly labeled partial evidence |
| `Get-Command opencli -ErrorAction SilentlyContinue` returns nothing | OpenCLI is not installed or not on `PATH` | Report the local OpenCLI blocker and ask the user to install OpenCLI or expose it on `PATH` | Do not use Agent Reach as a fallback for Xiaohongshu access |
| HTML image extraction returns no URLs | SSR payload changed, login wall, or unsupported page shape | Inspect near `imageList`, then try the PowerShell string-array split fallback | If `imageList` is absent and metadata also failed, use browser screenshots only if the page is accessible |
| Downloaded images are low-resolution or duplicated | Preview URLs, CDN variants, or repeated URL fields | Prefer `urlDefault`; verify manifest count against carousel count; deduplicate URLs before OCR | If readable images cannot be obtained, summarize only text metadata and state the image evidence gap |
| OCR is unavailable or poor | No local OCR engine, dense text, small font, or low contrast | Read images visually in batches of 3-4 pages; crop or zoom only unclear key pages | If key pages remain unreadable, mark the affected conclusions as uncertain |
| Comments fail or are incomplete | Comments endpoint needs signed URL, pagination, or login | Retry comments with the full signed URL; otherwise omit comments from evidence | Do not infer consensus from missing comments |
| Search returns many low-signal posts | Query too broad or platform ranking favors viral content | Narrow query by scenario, baseline, outcome, or material; sample posts with different angles | Stop after enough posts cover repeated advice and meaningful disagreement |

### 2. Read Structured Metadata

Run:

```powershell
opencli xiaohongshu note "<full URL with xsec_token>" -f yaml
```

Capture title, author, publish time if available, caption/desc, likes, collects, comments, and tags.

If comments matter, call comments with the full signed URL, not a bare note id:

```powershell
opencli xiaohongshu comments "<full URL with xsec_token>" -f yaml
```

### 3. Extract Images Without Opening the Front End

Use `scripts/extract_xhs_images.py` to fetch page HTML, extract `noteDetailMap.*.note.imageList[].urlDefault`, and download images.

```powershell
python "<skill-dir>\scripts\extract_xhs_images.py" "<xhs-url>" --out "C:\tmp\xhs-note" --save-html
```

If `C:\tmp` or the chosen temp path is not writable, rerun the script with an output folder inside the current workspace, for example `"$PWD\xhs-note-images"`. On Windows, a `PermissionError` for `C:\tmp\...` can happen even when `C:\tmp` is nominally writable; treat it as a path-permission issue and switch to the workspace output folder. Keep these images as intermediate evidence only; remove or ignore them after producing the requested artifact unless the user wants the images saved.

This avoids the main time sink observed in practice: loading Xiaohongshu's heavy browser front end, waiting for scripts, then timing out before screenshots are usable.

If the script fails, fallback order:

1. Fetch HTML with `Invoke-WebRequest` and inspect near `imageList`.
2. Split on `"urlDefault":"` using string-array split in PowerShell, not `.Split()` with a plain string argument.
3. Use browser screenshots only after HTML/image extraction fails.

PowerShell trap:

```powershell
$parts = $html.Split([string[]]@('"urlDefault":"'), [System.StringSplitOptions]::None)
```

Do not use `$html.Split('"urlDefault":"')`; PowerShell treats it as a character set and explodes the page into huge output.

### 4. OCR / Image Reading Strategy

Goal: preserve OCR quality while controlling context.

Use this order:

1. Check local OCR availability: `Get-Command tesseract -ErrorAction SilentlyContinue`.
2. Optionally check Python OCR packages if useful: `python -c "import importlib.util as u; print({m: bool(u.find_spec(m)) for m in ['pytesseract','easyocr','paddleocr','rapidocr_onnxruntime']})"`.
3. If OCR is available, run OCR on downloaded images, then visually spot-check low-confidence or key pages.
4. If OCR is not available, read local image files in batches of 3-4 pages with the current agent's native image-viewing or image-attachment capability. In Codex, use the built-in local image viewing tool with absolute Windows paths to the downloaded files, for example `C:\tmp\xhs-note\page01.jpg`, or workspace-local paths when `C:\tmp` is not writable. In Claude Code, use its available image/file attachment path if present; if no reliable image-viewing mechanism is available, report the blocker instead of inventing a code emitter. Do not send all images at once unless there are only a few.
5. If image viewing is blocked by desktop, agent, or Windows sandbox restrictions, report the blocker and ask the user to provide screenshots/images directly or approve an accessible workspace output path. Do not invent alternate image-emission code or rely on unverified REPL/image-emitter APIs.
6. Before synthesis, create page-by-page OCR evidence notes with `readable`, `confidence`, `confidence_reason`, extracted points, and follow-up needs. Use `confidence: high | medium | low | failed` to show how certain the extracted content came from the image rather than inference.
7. Stop reading image text as source evidence if 2 consecutive pages are `confidence: low/failed`, or if 3 consecutive pages are `confidence: medium/low/failed` and the main conclusion depends on image-body text. After stopping, use only metadata, caption, tags, visible stats, comments, and high-confidence image elements; state that the image body could not be reliably extracted.
8. For long carousels, write a compact per-page note while reading.

Suggested per-page note format:

- `page01`: identity/context and top-level thesis
- `page02-03`: resources/tools
- `page04-06`: workflow/process
- `page07+`: section-specific tips, caveats, final advice

OCR quality guardrails:

- Prefer `urlDefault` over preview images.
- Preserve original resolution; do not crop unless the image is too large or contains irrelevant margins.
- If a page contains dense tables or small text, zoom/crop that page only and reread it.
- If exact text cannot be confirmed, write that it cannot be confirmed; do not invent plausible wording, numbers, materials, schedules, or method steps.
- Do not pad an actionable method with low-confidence image details just to make the output feel complete.
- Do not quote long copyrighted text verbatim; summarize and use short excerpts only when necessary.

### 5. Filter Noise Before Extracting Experience

Treat Xiaohongshu posts as noisy source material. Extract useful information; do not preserve the post's social-media style.

Drop or compress these as noise unless the user explicitly asks for style analysis:

- Greeting, hype, and community filler: `姐妹们`, `家人们`, `绝绝子`, `狠狠爱了`, generic encouragement, repeated emojis, and dramatic title phrasing.
- Low-information claims: `亲测有效`, `闭眼入`, `一定要看`, `救命`, `逆袭`, or `保姆级` when no concrete process follows.
- Repeated narrative padding: emotional backstory, anxiety venting, victory laps, and long setup that does not change the method or applicability.
- Pure resource dumps: tool/course/book lists with no sequence, usage method, selection logic, or result context.

Keep and prioritize these as signal:

- Specific steps: ordered workflow, daily schedule, review loop, search/query method, scripts/tools setup, or decision rules.
- Concrete parameters: duration, frequency, score/baseline, cost, number of mocks/questions/pages, product model/version, location, deadline, or constraints.
- Error and avoidance details: what failed, why it failed, what changed, and what warning signs to check.
- Fit conditions: who the method fits, prerequisites, time/budget limits, region/platform constraints, and cases where the author says it did not work.
- Evidence anchors: screenshots, before/after metrics, comment disagreement, repeated claims across posts, or page-level OCR notes.

Flag these instead of silently trusting them:

- Soft-ad indicators: affiliate links, discount codes, course enrollment prompts, repeated brand mentions, identical product phrasing across posts, private-message bait, or claims that a paid tool is mandatory.
- Unsupported outcomes: dramatic score jumps, guaranteed results, extreme timelines, or methods that omit baseline and workload.
- Ambiguous OCR: garbled text, unclear table cells, cropped screenshots, low-confidence visual reading, or pages where the main claim depends on unreadable details. Mark low-confidence image-derived claims with `[OCR-low-confidence]`.

When writing the final answer, do not summarize discarded noise. If a noisy phrase points to a real method, rewrite it as the underlying action. Example: convert `姐妹们这个方法真的绝绝子` into the actual method, evidence, and fit condition; if none exist, omit it.

### 6. Extract Experience, Not Just Text

For each post, produce:

- **Who / baseline**: author's background, score, timeline, constraints.
- **Materials**: books, websites, apps, channels, courses.
- **Method**: the actual repeatable process.
- **Error diagnosis**: what problems the method targets.
- **Section/task breakdown**: if the post is exam-related.
- **Claims to trust cautiously**: unsupported score jumps, extreme timelines, promotional tools, personal-fit caveats.
- **Actionable version for the user**: a practical plan or checklist.

Do not over-credit viral phrasing. Separate evidence-backed, repeated, or logically sound advice from personal anecdote.

### 7. Grade Evidence Before Synthesizing

For experience posts, grade claims by evidence strength instead of treating all advice equally:

- **Direct post facts**: author baseline, timeline, materials, stated result, constraints, and visible screenshots. Use these as context, not universal proof.
- **Repeatable method**: concrete steps another person can follow, such as schedule, review loop, tool setup, mistake log, or material sequence.
- **Cross-post consensus**: advice repeated across multiple independent posts or supported by comments and examples.
- **Personal-fit advice**: advice tied to the author's baseline, school, job, exam score, budget, region, or time constraint.
- **Weak or risky claims**: dramatic score jumps, guaranteed outcomes, extreme timelines, vague "must use" tools, affiliate links, course promotion, or claims without process details.
- **Evidence gap**: missing image pages, unreadable OCR, inaccessible comments, unresolved short links, unclear author baseline, or pages with `confidence: failed`.

Apply an OCR reliability discount before promoting any image-derived claim:

- Claims fully dependent on `confidence: low` visual/OCR reading must be downgraded or labeled `[OCR-low-confidence]`, even if they look like a repeatable method.
- `confidence: medium` image content may be used as a method clue, but do not promote it to cross-post consensus unless high-confidence images, caption, comments, metadata, or independent posts support it.
- `confidence: failed` pages can only support an `evidence gap`; do not extract concrete body-text claims from them.
- Keep OCR risk visible in aggregation tables and `谨慎对待`; do not mix low-confidence image claims with high-confidence evidence without labeling the difference.

When advice is useful but weakly supported, keep it but label the condition: "worth trying if...", "only fits...", or "do not generalize from this alone." Do not turn one viral anecdote into a general rule.

### 8. Aggregate Multiple Posts By Claim

For multi-post tasks, do not summarize posts one by one unless the user explicitly asks for a per-post digest. Aggregate at the claim/action level.

Use this procedure:

1. Create one compact extraction record per post: `post_id`, `baseline`, `scenario`, `claim`, `action/method`, `result`, `risk`, `soft_ad_flag`, and `evidence_gap`.
2. Normalize equivalent claims before counting them. Merge wording variants such as `精听`, `听写复盘`, and `逐句听写` when they describe the same action loop. Keep separate claims that differ in material, frequency, baseline, or goal.
3. Cluster records by theme: method, product/tool, material, timeline, mistake, cost, prerequisite, or warning.
4. Count support and disagreement inside each cluster: `supports`, `opposes`, `conditional`, and `unclear`. Use post counts, not likes or saves, as the default evidence unit.
5. Mark the reason for disagreement when visible: different baseline, different budget, outdated version, region/platform difference, exam section, workload, or hidden paid-course dependency.
6. Promote a claim to consensus only when it appears across independent posts or is strongly supported by process detail. Label single-post claims as `single-source` even if they sound convincing.
7. Deduplicate repeated product or method mentions. Write one consolidated conclusion with representative evidence instead of repeating the same advice five times.
8. Preserve minority warnings when they reveal a real failure mode, even if most posts are positive.

Use this compact aggregation table when helpful:

| normalized claim | support | disagreement | best-fit user | risk / caveat |
| --- | --- | --- | --- | --- |
| <method/product/action> | <n supports, n conditional> | <n oppose or warning> | <baseline/scenario> | <soft-ad, workload, OCR gap, etc.> |
## Output Shape

Choose the output mode by the user's goal. Default to a reusable method document, not a decorative summary.

- **Study / exam strategy**: output baseline assumptions, stage plan, daily/weekly actions, materials sequence, review loop, metrics to track, and common mistakes.
- **Product / tool decision**: output use case, who should use it, who should avoid it, setup or buying checklist, repeated pros/cons, alternatives, and soft-ad risk.
- **Career / application experience**: output timeline, target profile, materials, outreach/interview steps, screening criteria, failure points, and reusable templates/checklists when appropriate.
- **Life / travel / local services**: output decision criteria, cost/time/location constraints, booking or execution steps, red flags, and alternatives.
- **Quick scan**: output only the useful claims, repeated advice, disagreements, and risks. Skip metadata-heavy sections unless they affect trust.
- **Deep research**: include sample scope, query strategy, aggregation table, evidence gaps, and an action plan.
For a single post:

```markdown
**帖子信息**
Title, author, stats, URL.

**作者背景**
Short factual baseline.

**识别质量说明**
共 X 页，Y 页高/中置信，Z 页低置信或无法确认；相关结论已标注 `[OCR-low-confidence]`。如果图片正文不可可靠读取，写明：该帖子图片正文因视觉识别质量不足未能完整提取，以下结论仅基于标题/简介/评论/可确认的图片元素。

**核心观点**
1-3 bullets.

**可复用方法**
Concrete workflow.

**细节拆解**
By material, daily practice, review, common mistakes.

**我的判断**
What is useful, what is risky, what to adapt.
```

For multiple posts, use this synthesis shape:

```markdown
**样本范围**
Queries used, number of posts read, selection logic, and evidence gaps.

**识别质量说明**
Summarize OCR/visual coverage across sampled posts, for example: 共 X 页，Y 页高/中置信，Z 页低置信或无法确认；低置信图片结论已标注 `[OCR-low-confidence]` 并放入 `谨慎对待`。

**共识结论**
Advice repeated across multiple posts, with the conditions where it applies.

**分歧点**
Where posts disagree, grouped by baseline, timeline, budget, tool/material, or goal.

**方法流派**
Distinct workflows or strategies, each with suitable user profiles and failure modes.

**证据分级表**
| theme | stronger evidence | weaker / anecdotal evidence | risk |
| --- | --- | --- | --- |

**可执行版本**
A practical plan, checklist, or decision rule adapted to the user's situation.

**谨慎对待**
Promotional claims, extreme outcomes, missing context, `[OCR-low-confidence]` image-derived claims, or advice that does not fit the user.
```

If the request is only a quick scan, compress the structure but still preserve `共识结论`, `分歧点`, and `谨慎对待`.

## Bundled Resources

- `references/opencli-xhs-usage.md`: local Xiaohongshu OpenCLI usage guide, including local `opencli` checks, smoke-test routing, signed URL rules, Browser Bridge troubleshooting, short-link handling, and read-only scope.
- `scripts/extract_xhs_images.py`: download full-resolution images from a Xiaohongshu note URL by parsing server-rendered HTML; optionally save HTML/debug hints and image metadata in `manifest.json`.
- `scripts/smoke_extract_xhs_images.py`: pure local smoke test for the extractor. It starts a localhost fixture server, reads one simulated note, downloads fixture images, and verifies `manifest.json` without Agent Reach, OpenCLI, Xiaohongshu, or public internet access.
- `references/ocr-playbook.md`: detailed OCR and batching playbook. Read it when image OCR quality or long carousels are central to the request.






