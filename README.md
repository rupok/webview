# WebView

> Turn your website into a real Android app. URL in, signed APK/AAB out.

```bash
pip install webview
webview init https://your-site.com
webview build
```

That's it. WebView picks the right path for your site, generates a complete
buildable Android project, and walks you through producing a signed APK
or Play Store-ready AAB.

---

## Three paths, picked automatically

| Site looks like… | Path | What you get |
|---|---|---|
| HTTPS + valid PWA manifest | **TWA** (via [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap)) | A Trusted Web Activity AAB — Play Store-blessed, full Chrome under the hood |
| Anything else | **Kotlin** WebView project | A modern Android Studio project with WebView, splash, pull-to-refresh, deep links |
| You don't want a local toolchain | **GitHub Actions** | Push your `webview.json` and CI builds the APK for you |

`webview build` calls `webview detect` for you and chooses. Override
with `--kotlin` or `--twa` if you know better.

---

## Quickstart

```bash
pip install webview
cd path/to/your/project

webview init https://your-site.com \
    --name "My App" \
    --package com.yourdomain.myapp

webview detect           # see why it picked the path it did
webview build            # generate the project under ./out
```

Then either:

**Local build** (need JDK 17 + Android SDK):
```bash
cd out && ./gradlew assembleRelease
# APK: app/build/outputs/apk/release/app-release.apk
```

**CI build** (no local toolchain):
```bash
webview ci               # writes .github/workflows/build.yml
git add . && git commit -m "ship app" && git push
# Download the APK from the Actions run's artifacts
```

---

## What you get

### Kotlin path — modern WebView app

A clean Android Studio project (Gradle KTS, AndroidX, Kotlin 2.0, Material 3):

- `WebView` with JavaScript, DOM storage, mediaplayback enabled
- Pull-to-refresh
- Edge-to-edge layout, status-bar tinting, AndroidX SplashScreen
- WebView state survives rotation
- `tel:`, `mailto:`, `sms:` go to the system handler
- Off-domain links open in the user's real browser (configurable)
- `https://your-host/*` app-link intent filter
- Adaptive launcher icon (auto-generated from a single PNG, or a letter
  tile from your app name if you supply nothing)
- Network security config locked to your domain

### TWA path — full Chrome inside an app

For PWAs, generates a Bubblewrap-ready directory:

```
out/
├── twa-manifest.json    ← consumed by `bubblewrap init`
├── icon.png             ← 512x512 launcher source
├── README.md            ← step-by-step
└── webview.json         ← copy of your config
```

Then `bubblewrap init --manifest=./twa-manifest.json && bubblewrap build`
gives you `app-release-bundle.aab` (Play Store) and
`app-release-signed.apk` (sideload).

### CI path — no local toolchain needed

`webview ci` writes `.github/workflows/build.yml`. On push to `main`
(or via "Run workflow"), GitHub Actions:

1. Installs Python, JDK 17, Gradle, (Node + Bubblewrap if `--twa`).
2. Runs `webview build`.
3. Uploads the APK/AAB as a workflow artifact you can download from
   the Actions tab.

You only need a GitHub account.

---

## `webview.json`

Everything is driven by a single file:

```json
{
  "name": "My App",
  "url": "https://your-site.com/",
  "package": "com.yourdomain.myapp",
  "version_name": "1.0.0",
  "version_code": 1,
  "theme_color": "#1976D2",
  "background_color": "#FFFFFF",
  "min_sdk": 24,
  "target_sdk": 35,
  "icon": "./logo.png",
  "orientation": "unspecified",
  "allow_external_links": false
}
```

`webview init` writes a sensible default; edit it and re-run `webview build`.

---

## CLI reference

```
webview init <url>         Write webview.json
webview detect [<url>]     Probe a URL and recommend a build path
webview build              Generate a project (auto-picks path)
  --kotlin                   Force Kotlin WebView path
  --twa                      Force TWA / Bubblewrap path
  --output ./out             Where to write the project
webview ci                 Write .github/workflows/build.yml
  --path kotlin|twa
webview info               Show the active webview.json
```

---

## When to use what

| Your situation | Use |
|---|---|
| Your site is already a PWA (manifest + service worker) | `--twa`. Best UX, Play Store-blessed. |
| HTTPS site, no PWA, want a Play Store app | `--kotlin`. Add native value (push, share, offline) before submitting. |
| HTTP / intranet / staging site | `--kotlin`. TWA requires HTTPS. |
| You don't have JDK + Android SDK and don't want to install them | `webview ci`. Build in the cloud. |
| You just want users to install your site, no Play Store | Honestly? Tell them "Add to Home Screen" from Chrome. WebView is for when you specifically need a sideloadable APK or Play Store presence. |

---

## Project history

| Version | Era       | Stack                       | What it did |
|---------|-----------|-----------------------------|-------------|
| **v1**  | 2014–2015 | Eclipse + Java + ADT        | Wrapped a website in an Android app |
| **v2**  | 2026–     | Python CLI + Kotlin/TWA/CI  | Same idea, modern toolchain, signed AAB |

v1 is preserved at branch
[`archive/eclipse-android`](https://github.com/rupok/webview/tree/archive/eclipse-android)
and tag `legacy/v1.0-eclipse-2015`. The git history is intact.

---

## License

GPL-2.0-or-later (carried over from v1).

## Contributing

```bash
pip install -e '.[dev]'
pytest
ruff check src/ tests/
```
