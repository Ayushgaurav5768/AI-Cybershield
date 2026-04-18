# AI CyberShield Chrome Extension (MV3)

## Load locally
1. Open `chrome://extensions`
2. Enable Developer mode
3. Click `Load unpacked`
4. Select `apps/chrome-extension`

## Features in this MVP
- Auto-scan on page load using backend `/scan`
- Badge states: `SAFE`, `WARN`, `DNG`, `ERR`
- Popup: manual scan, risk score, explanations, report/trust actions
- Credential form submission warning in content script
- Warning interstitial for dangerous pages (optional setting)
- User reports, allowlist, and extension event telemetry ingestion

## API dependency
Backend expected at `http://127.0.0.1:8000`.

## Privacy notes
- No page content is uploaded in this MVP; URL-level checks only.
- Extension stores local settings and latest scan in `chrome.storage.local`.
- TODO: Add explicit consent screen before telemetry in production.
