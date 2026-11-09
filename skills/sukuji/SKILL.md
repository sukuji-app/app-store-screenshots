---
name: sukuji
description: Make App Store screenshots for the user's iOS app with sukuji (AI-designed headlines, layout and artwork, 1290x2796 iPhone or 2064x2752 iPad, up to 5 languages, fastlane layout). Use when the user asks for App Store screenshots, store screenshots, screenshot sets, or marketing images for their iPhone/iPad app.
---

# sukuji: App Store screenshots

sukuji turns 1 to 3 real screens of the app into a finished set of 5 App Store screenshots.
It writes the headlines, picks the layout and draws the backdrop for this app. It takes about 2 minutes.

Everything goes through `sukuji.py`, which sits next to this file. It needs only `python3`.

## 1. Gather the screens (1 to 3)

Use real, full-screen portrait captures of the app's most important screens.
- If a simulator is running the app: `xcrun simctl io booted screenshot screen1.png`. Navigate to another key screen and capture again.
- Otherwise use existing screenshots in the project (for example `fastlane/screenshots`, `docs`, `assets`). Ask the user if you can't find any.

Do not send code. Only the screen images, the app name and a short description leave the machine.

## 2. Describe the app

Read the README, `Info.plist` (`CFBundleDisplayName`) and any store text.
Write:
- the app name;
- one or two sentences on what the app does and for whom.

## 3. Make the set

```bash
python3 <this skill's folder>/sukuji.py make \
  --name "App Name" --desc "What it does, for whom." \
  --lang en --device iphone --out appstore-screenshots \
  screen1.png screen2.png screen3.png
```

- `--lang`: up to 5 comma-separated codes, main one first. Choose from `en, ja, zh-Hans, zh-Hant, ko, fr, de, es, pt, it`. Example: `--lang en,ja,de`.
- `--device`: `iphone` (default) or `ipad`.
- `--header`: also make the App Store header and search-results images.
- `--fastlane`: save into `fastlane/screenshots/<locale>/`, ready for `fastlane deliver`. Use it when the project has a `fastlane` folder.

The script uploads the screens, waits about 2 minutes, then saves and unzips the result. Run it in the foreground with a long timeout (5 minutes or more). When it is done, show the user where the files were saved.

## Free use and keys

- **Without a key:** one free set per day, in one language, for iPhone, with a small watermark.
- **With a key:** no watermark, up to 5 languages, iPad, header images. The user gets a key at https://sukuji.com/mcp and sets it with `export SUKUJI_KEY=...`. The script reads `SUKUJI_KEY` automatically.

If the script says the free set is used up or the key is out of credits, tell the user and pass on the link it prints. Do not retry in a loop.

`python3 sukuji.py credits` shows what is left.
