# OpenCLI Xiaohongshu Usage

opencli 是用户需要预先安装好的外部命令行工具，本skill不提供安装，仅说明调用方式。如未安装，请参考 [OpenCLI Chrome Web Store 页面](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk)。

This reference is local to `xhs-experience-extractor`; it contains the Xiaohongshu OpenCLI usage needed by this skill.

## Source Paragraphs Migrated From Agent Reach

The Xiaohongshu-specific material was migrated from these Agent Reach locations:

- `agent-reach/SKILL.md` lines 49-50: run `agent-reach doctor --json` before logged-in or multi-backend platforms and select commands by `active_backend`.
- `agent-reach/SKILL.md` lines 93-104: logged-in platforms are selected by doctor; Xiaohongshu desktop path is `opencli xiaohongshu search "query" -f yaml`.
- `agent-reach/SKILL.md` lines 113-118: `agent-reach doctor --json` checks available channels and active backends.
- `agent-reach/references/social.md` lines 5-28: Xiaohongshu backend selection and OpenCLI commands for search, note, comments, feed, and user.
- `agent-reach/references/social.md` lines 58-64: Xiaohongshu `xsec_token`, rate-limit, and read-only cautions.

## Local OpenCLI Readiness Check

`xhs-experience-extractor` uses `opencli xiaohongshu ...` directly as its Xiaohongshu access path. Do not require `agent-reach doctor --json` before using this skill.

First check whether `opencli` is available on Windows `PATH`:

```powershell
Get-Command opencli -ErrorAction SilentlyContinue
```

If this returns nothing, OpenCLI is not installed or is not exposed on `PATH`. Report that local blocker and ask the user to install OpenCLI or fix `PATH`; do not fall back to Agent Reach.

If `opencli` exists, run one cheap Xiaohongshu smoke test before launching several platform calls:

```powershell
opencli xiaohongshu search "<targeted query>" -f yaml
```

Interpret the smoke-test result directly:

- Normal YAML output: OpenCLI Xiaohongshu access is usable for this session.
- `BROWSER_CONNECT` or `Browser Bridge extension not connected`: Chrome is closed, the OpenCLI extension is disabled, or the browser bridge has not connected yet.
- `AUTH_REQUIRED` or a login-required error: the browser bridge may be connected, but Xiaohongshu login state is missing or expired.
- Other command-not-found or syntax errors: report the exact local OpenCLI blocker and do not invent alternate platform commands.

## OpenCLI Commands

OpenCLI is the preferred desktop path because it reuses the user's Chrome login state.

```powershell
# Search notes
opencli xiaohongshu search "query" -f yaml

# Read note metadata/body/stats.
# Prefer the full signed URL from a search result or resolved browser page, including xsec_token when present.
opencli xiaohongshu note "NOTE_URL" -f yaml

# Read comments, including nested comments when available.
# Prefer the full signed URL with xsec_token. Use a note id only if the command/version explicitly accepts it.
opencli xiaohongshu comments "NOTE_URL_OR_NOTE_ID" -f yaml

# Home recommendation feed
opencli xiaohongshu feed -f yaml

# Public notes from a user profile
opencli xiaohongshu user USER_ID -f yaml
```

For `xhs-experience-extractor`, the usual path is:

1. Search with 1-3 targeted queries.
2. Pick candidate notes with concrete baseline, method, materials, screenshots, or comments.
3. Read each note with `opencli xiaohongshu note "<full signed URL>" -f yaml`.
4. Read comments only when comments affect trust, disagreement, or user decision quality.

## URL And Token Rules

Xiaohongshu enforces signed context through `xsec_token`. Do not treat a bare note id as sufficient when reading details.

Correct flow:

1. Use search, feed, or browser resolution to obtain the full note URL.
2. Preserve `xsec_token` and other signed query parameters when present.
3. Pass the full URL to `note` and, when possible, to `comments`.

If `opencli xiaohongshu note` fails on a bare note id, retry with the full signed URL copied from the search result or resolved page. If only a bare id is available and metadata still cannot be fetched, continue only with clearly labeled partial evidence.

## Browser Bridge Troubleshooting

OpenCLI Xiaohongshu requires Chrome to be open, the OpenCLI extension to be installed/enabled, and the user to be logged into Xiaohongshu in Chrome.

Before launching several OpenCLI calls, run one cheap smoke test:

```powershell
opencli xiaohongshu search "<targeted query>" -f yaml
```

If the command returns `BROWSER_CONNECT` or `Browser Bridge extension not connected`:

1. Check whether Chrome is running.
2. If Chrome is closed, open Chrome or ask the user to open Chrome.
3. Wait briefly for the OpenCLI extension to reconnect, then retry one single search as the smoke test.
4. If Chrome is already running, ask the user to verify that the OpenCLI extension is enabled and connected.
5. If the bridge still fails after Chrome is open and one retry, report the browser-bridge blocker and use only non-OpenCLI evidence if available.

If the command returns `AUTH_REQUIRED` or a login-required error, the browser bridge may be connected but Xiaohongshu login state is missing or expired. Ask the user to log into Xiaohongshu in Chrome once, then retry a single smoke-test search.

Do not start multiple parallel `opencli xiaohongshu` calls until the smoke test succeeds.

## Short Links: xhslink.com

For shared short links such as `xhslink.com`, first try to resolve the link to the final full Xiaohongshu URL. Direct HTTP or OpenCLI resolution may fail because the redirect can depend on browser or logged-in context.

Required handling:

1. Try direct resolution only if it is cheap and non-destructive.
2. If direct resolution fails, open the short link in the user's logged-in browser context and capture the final full Xiaohongshu URL.
3. Do not search the short-link code and treat a search result as the target note.
4. A search result is only a candidate. Verify it against the opened short link, supplied page title, author, topic, or visible page content.
5. If the final URL cannot be verified, ask for the full Xiaohongshu URL or browser-state access instead of guessing.

## Frequency And Scope Rules

- High-frequency requests, batch searches, and deep comment pagination can trigger verification or rate limits. Keep calls paced, roughly 2-3 seconds apart when running several requests.
- Use OpenCLI for read actions only: search, note, comments, feed, user. Do not post, comment, like, collect, follow, or perform other write actions.
- If comments fail or appear incomplete, do not infer consensus from missing comments. Label the evidence gap.