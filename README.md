# sukuji: App Store screenshots from your coding agent

Ask your agent **"Make App Store screenshots for this app"**. It grabs your app's real screens, and sukuji designs a finished set of 5: headlines, layout and AI-drawn artwork made for your app. About 2 minutes later, the set is saved in your project.

Works with Claude Code, Codex, OpenCode, Cursor and any agent that reads skills.

## Install

```bash
npx skills add sukuji-app/app-store-screenshots
```

Then, in your app's project:

> Make App Store screenshots for this app

## What you get

- 5 screenshots at 1290×2796 (iPhone 6.9″) or 2064×2752 (iPad 13″)
- Headlines written from what your screens actually show
- Up to 5 of 10 languages in one run: en, ja, zh-Hans, zh-Hant, ko, fr, de, es, pt, it
- Optional fastlane layout (`fastlane/screenshots/<locale>/`), ready for `fastlane deliver`

## Free and paid

| | Free | With a key |
|---|---|---|
| Sets | 1 per day | from a one-time pack (10 for $9, 50 for $29) |
| Languages | 1 | up to 5 per run |
| Devices | iPhone | iPhone and iPad |
| Watermark | small watermark | none |

No sign-up is needed for the free set. To use a key, get one at https://sukuji.com/mcp and set:

```bash
export SUKUJI_KEY=your-key
```

## What is sent

Only the 1 to 3 screen images you choose, the app name and a one-line description. **Your code is never sent.** The skill is two plain files you can read: [`SKILL.md`](skills/sukuji/SKILL.md) (instructions for the agent) and [`sukuji.py`](skills/sukuji/sukuji.py) (uploads the screens to https://sukuji.com and saves the result; standard library only).

## MCP

Prefer MCP? `claude mcp add --transport http sukuji https://sukuji.com/mcp`. See https://sukuji.com/mcp for Codex and OpenCode.

## License

MIT
