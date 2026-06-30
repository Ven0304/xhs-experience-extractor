# XHS Experience Extractor Skill

[English](#english) | [中文](#中文)

<a id="english"></a>

## English

A Windows-only Codex skill for extracting, denoising, and synthesizing Xiaohongshu (XHS) experience posts into reusable methods, checklists, and decision notes.

This repository contains an independently packaged Xiaohongshu workflow extracted from `agent-reach`. The Xiaohongshu OpenCLI guidance that previously lived under `agent-reach` has been copied and rewritten into this skill's own [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md), so the skill no longer needs to read `agent-reach/SKILL.md` or `agent-reach/references/social.md` at runtime.

### Status

- **Primary environment:** Codex on Windows.
- **Compatibility target:** Claude Code on Windows is best-effort and theoretical; use its native file/image attachment path if available.
- **Not supported:** macOS/Linux workflows are out of scope for now.
- **Platform access:** Xiaohongshu access is read-only and goes through the external `opencli xiaohongshu ...` command.
- **Agent Reach dependency:** Not required at runtime. Agent Reach source references are documented for auditability, but the full Agent Reach skill is not part of this standalone package.

### What This Skill Does

Use this skill when the user provides a Xiaohongshu/XHS URL, `xhslink.com` short link, screenshots, OCR text, pasted post text, or asks to search Xiaohongshu for study, career, product, life, finance, travel, or application experience.

The skill is designed to:

- read Xiaohongshu post metadata with OpenCLI;
- preserve signed URLs and `xsec_token` context for `note` and `comments` calls;
- extract carousel image URLs from server-rendered HTML;
- download full-resolution images and generate `manifest.json`;
- guide OCR or visual reading in small batches;
- record page-level recognition confidence and OCR uncertainty;
- filter social-media filler, soft ads, weak claims, and low-confidence visual claims;
- synthesize reusable methods, evidence gaps, disagreement, and action plans.

### What It Does Not Do

- It does not install OpenCLI.
- It does not require `agent-reach doctor --json`.
- It does not post, comment, like, collect, follow, or perform any write action on Xiaohongshu.
- It does not promise Claude Code parity; Claude Code compatibility depends on the local tool/file/image capabilities available in that agent.
- It does not support macOS/Linux paths or shell examples yet.

### Requirements

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

### OpenCLI Xiaohongshu Commands

```powershell
opencli xiaohongshu search "query" -f yaml
opencli xiaohongshu note "NOTE_URL" -f yaml
opencli xiaohongshu comments "NOTE_URL_OR_NOTE_ID" -f yaml
opencli xiaohongshu feed -f yaml
opencli xiaohongshu user USER_ID -f yaml
```

Prefer the full signed URL from search results or browser resolution, especially when `xsec_token` is present. Do not assume a bare note ID is enough for `note` or `comments`.

### Extracting Images

The bundled extractor avoids driving the Xiaohongshu front end when possible. It fetches page HTML, finds `noteDetailMap.*.note.imageList[].urlDefault`, downloads images, and writes a manifest.

```powershell
python "xhs-experience-extractor\scripts\extract_xhs_images.py" "<xhs-url>" --out "xhs-experience-extractor\xhs-note-images" --save-html
```

Expected output includes:

- downloaded image files such as `page01.jpg` or `page01.png`;
- `manifest.json` with source metadata, URL count, downloaded count, image paths, dimensions, and errors;
- optional `source.html` when `--save-html` is used.

### OCR And Visual Reliability

For carousel posts whose main text lives in images, the skill treats recognition quality as an explicit evidence variable instead of assuming OCR or vision is reliable.

- Each page should record both `readable: yes | partial | no` and `confidence: high | medium | low | failed`.
- Low-confidence image-derived claims should be labeled `[OCR-low-confidence]` and kept separate from stronger evidence.
- If consecutive pages cannot be read reliably, the workflow stops extracting image-body details and falls back to metadata, caption, tags, stats, comments, and clearly visible high-confidence elements.
- Final single-post and multi-post outputs should include a short recognition quality note, such as how many pages were clear and which conclusions are uncertain.

### Local Smoke Test

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

### Repository Layout

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

### Skill Files

- [`xhs-experience-extractor/SKILL.md`](xhs-experience-extractor/SKILL.md): main skill instructions and workflow.
- [`xhs-experience-extractor/references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md): self-contained Xiaohongshu OpenCLI usage guide extracted from Agent Reach.
- [`xhs-experience-extractor/references/ocr-playbook.md`](xhs-experience-extractor/references/ocr-playbook.md): OCR and long-carousel reading playbook.
- [`xhs-experience-extractor/scripts/extract_xhs_images.py`](xhs-experience-extractor/scripts/extract_xhs_images.py): local extractor for server-rendered HTML image URLs.
- [`xhs-experience-extractor/scripts/smoke_extract_xhs_images.py`](xhs-experience-extractor/scripts/smoke_extract_xhs_images.py): local extractor smoke test.

### Migration Notes

This skill is derived from the Xiaohongshu/OpenCLI portion of Agent Reach, but its runtime path is now independent:

- Agent Reach source line references are preserved in [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md) for auditability.
- Runtime instructions use direct `opencli xiaohongshu ...` commands.
- `agent-reach doctor --json` is not required.
- The local extractor and smoke test do not import or execute Agent Reach code.

### Safety And Evidence Rules

- Treat Xiaohongshu posts as noisy evidence, not authoritative truth.
- Preserve source URLs, manifest paths, page-level notes, confidence labels, and uncertainty labels.
- Mark missing comments, unreadable images, inaccessible short links, OCR ambiguity, and failed visual recognition as evidence gaps.
- Do not promote medium-confidence image text to cross-post consensus unless independent evidence supports it.
- Do not turn low-confidence OCR or visual guesses into actionable methods.
- Do not infer consensus from missing or incomplete comments.
- Summarize copyrighted post text instead of quoting long passages.

### License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

[Back to top](#xhs-experience-extractor-skill)

---

<a id="中文"></a>

## 中文

一个仅面向 Windows 的 Codex skill，用于把小红书（Xiaohongshu / XHS）经验帖提取、降噪并整理成可复用的方法、清单和决策笔记。

这个仓库是从 `agent-reach` 中的小红书 OpenCLI 工作流提取出来并独立封装的版本。原本放在 `agent-reach` 里的小红书 OpenCLI 用法，已经复制并重写到本 skill 自己的 [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md) 中，因此运行时不再需要读取 `agent-reach/SKILL.md` 或 `agent-reach/references/social.md`。

### 当前状态

- **主要运行环境：** Windows 上的 Codex。
- **兼容目标：** 理论上尽量兼容 Windows 上的 Claude Code；如果 Claude Code 提供可用的文件/图片附件能力，可以按其机制处理图片。
- **暂不支持：** 暂不考虑 macOS/Linux 工作流。
- **平台访问：** 小红书访问只做只读操作，并通过外部命令 `opencli xiaohongshu ...` 完成。
- **Agent Reach 依赖：** 运行时不依赖 Agent Reach。文档中保留 Agent Reach 来源行号，仅用于迁移核对。

### 这个 Skill 能做什么

适用于用户提供小红书/XHS 链接、`xhslink.com` 短链、截图、OCR 文本、粘贴的帖子正文，或希望搜索小红书上的学习、求职、产品、生活、金融、旅行、申请等经验内容的场景。

它主要用于：

- 通过 OpenCLI 读取小红书帖子元数据；
- 保留 signed URL 和 `xsec_token` 上下文，用于 `note` 和 `comments` 调用；
- 从服务端渲染 HTML 中提取轮播图 URL；
- 下载原图并生成 `manifest.json`；
- 指导 OCR 或分批视觉阅读；
- 记录逐页识别置信度和 OCR 不确定性；
- 过滤社交平台口水话、软广、弱证据 claims 和低置信视觉结论；
- 汇总可复用方法、证据缺口、分歧点和行动方案。

### 它不做什么

- 不负责安装 OpenCLI。
- 不要求运行 `agent-reach doctor --json`。
- 不在小红书上发帖、评论、点赞、收藏、关注，也不做任何写操作。
- 不承诺 Claude Code 完全等价支持；Claude Code 可用性取决于该环境下实际存在的本地文件/图片能力。
- 暂不提供 macOS/Linux 路径或 shell 示例。

### 环境要求

- Windows。
- 建议 Python 3.10+，用于运行内置脚本。
- 实时访问小红书时，需要安装 OpenCLI，并确保 `opencli` 在 `PATH` 中。
- Chrome 中需要启用 OpenCLI 扩展，并保持有效的小红书登录状态。

检查本地是否能找到 OpenCLI：

```powershell
Get-Command opencli -ErrorAction SilentlyContinue
```

批量调用前先做一次低成本小红书 smoke test：

```powershell
opencli xiaohongshu search "<targeted query>" -f yaml
```

常见结果解释：

| 结果 | 含义 | 下一步 |
| --- | --- | --- |
| 正常 YAML 输出 | OpenCLI 小红书通道可用 | 继续执行 `search`、`note` 或 `comments` |
| `BROWSER_CONNECT` / `Browser Bridge extension not connected` | Chrome 或 OpenCLI 扩展桥接未连接 | 打开 Chrome，检查扩展，然后只重试一次 search |
| `AUTH_REQUIRED` | 浏览器桥可能已连接，但小红书登录态缺失或过期 | 在 Chrome 登录小红书后，只重试一次 search |
| command not found | OpenCLI 未安装或不在 `PATH` 中 | 安装/修复 OpenCLI，不回退到 Agent Reach |

### OpenCLI 小红书命令

```powershell
opencli xiaohongshu search "query" -f yaml
opencli xiaohongshu note "NOTE_URL" -f yaml
opencli xiaohongshu comments "NOTE_URL_OR_NOTE_ID" -f yaml
opencli xiaohongshu feed -f yaml
opencli xiaohongshu user USER_ID -f yaml
```

优先使用搜索结果或浏览器解析得到的完整 signed URL，尤其要保留 `xsec_token`。不要默认裸 note ID 足够用于 `note` 或 `comments`。

### 提取图片

内置 extractor 会尽量避免驱动小红书前端页面。它会抓取页面 HTML，寻找 `noteDetailMap.*.note.imageList[].urlDefault`，下载图片并写出 manifest。

```powershell
python "xhs-experience-extractor\scripts\extract_xhs_images.py" "<xhs-url>" --out "xhs-experience-extractor\xhs-note-images" --save-html
```

预期输出包括：

- `page01.jpg` 或 `page01.png` 等图片文件；
- `manifest.json`，包含来源元数据、URL 数量、下载数量、图片路径、尺寸和错误信息；
- 使用 `--save-html` 时还会保存 `source.html`。

### OCR 和视觉识别可靠性

对于正文主要写在轮播图里的帖子，这个 skill 会把识别质量当作显式证据变量，而不是默认 OCR 或视觉能力一定可靠。

- 每页都应同时记录 `readable: yes | partial | no` 和 `confidence: high | medium | low | failed`。
- 低置信图片结论应标注 `[OCR-low-confidence]`，并和更强证据分开处理。
- 如果连续多页无法可靠读取，流程会停止继续抽取图片正文细节，转而使用元数据、简介、标签、统计信息、评论和少量高置信可见元素。
- 单帖和多帖最终输出都应包含简短的识别质量说明，例如有多少页清晰、哪些结论需要谨慎核实。

### 本地 Smoke Test

仓库内置一个纯本地 smoke test，用来验证 extractor 不依赖 Agent Reach、OpenCLI、小红书或公网访问。

```powershell
python "xhs-experience-extractor\scripts\smoke_extract_xhs_images.py"
```

测试会启动一个 localhost fixture server，提供一个模拟的小红书帖子页和两张 fixture 图片，然后运行 `extract_xhs_images.py` 并验证 `manifest.json` 是否生成。

成功输出类似：

```text
PASS local xhs extractor smoke test
manifest: ...\xhs-experience-extractor\tmp-smoke-output\manifest.json
downloaded_count: 2
```

`tmp-smoke-output/` 是测试生成的输出，不属于可复用的 skill 源文件。

### 仓库结构

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

### 主要文件

- [`xhs-experience-extractor/SKILL.md`](xhs-experience-extractor/SKILL.md)：主 skill 指令和工作流。
- [`xhs-experience-extractor/references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md)：从 Agent Reach 提取并改写的小红书 OpenCLI 本地指南。
- [`xhs-experience-extractor/references/ocr-playbook.md`](xhs-experience-extractor/references/ocr-playbook.md)：OCR 和长图轮播阅读指南。
- [`xhs-experience-extractor/scripts/extract_xhs_images.py`](xhs-experience-extractor/scripts/extract_xhs_images.py)：从服务端渲染 HTML 提取图片 URL 的本地脚本。
- [`xhs-experience-extractor/scripts/smoke_extract_xhs_images.py`](xhs-experience-extractor/scripts/smoke_extract_xhs_images.py)：本地 extractor smoke test。

### 迁移说明

这个 skill 来自 Agent Reach 中的小红书/OpenCLI 部分，但当前运行路径已经独立：

- Agent Reach 来源行号保留在 [`references/opencli-xhs-usage.md`](xhs-experience-extractor/references/opencli-xhs-usage.md) 中，方便核对。
- 运行时直接使用 `opencli xiaohongshu ...` 命令。
- 不需要 `agent-reach doctor --json`。
- 本地 extractor 和 smoke test 不导入、不执行 Agent Reach 代码。

### 安全和证据规则

- 把小红书帖子视为噪声较多的经验材料，而不是权威事实。
- 保留来源 URL、manifest 路径、逐页笔记、置信度标签和不确定性标记。
- 对评论缺失、图片不可读、短链不可访问、OCR 模糊、视觉识别失败等情况标注 evidence gap。
- 不把中等置信度的图片文字直接升级为跨帖共识，除非有独立证据支持。
- 不把低置信 OCR 或视觉猜测写成可执行方法。
- 不从缺失或不完整的评论里推断共识。
- 对有版权的帖子正文做总结，不长段引用原文。

### License

本项目采用 MIT License 授权。详见 [LICENSE](LICENSE)。

[返回顶部](#xhs-experience-extractor-skill)
