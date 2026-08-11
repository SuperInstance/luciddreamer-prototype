# LucidDreamer.AI — Live URLs

Last updated: 2026-08-11 15:25 AKDT

## 🚪 FRONT DOOR EXPERIENCE — PRIMARY SITE

| Component | URL | Status |
|-----------|-----|--------|
| **Front Door (main site)** | https://luciddreamer.pages.dev | ⏳ Deploy pending — CF auth expired |
| **Custom Domain** | https://luciddreamer.ai | ⏳ DNS pending (CNAME needed → luciddreamer.pages.dev) |

### Front Door Details
- **Directory:** `front-door-experience/`
- **Title:** "The Front Door — The F/V EILEEN"
- **Tagline:** "Seven stories from the Tap, aboard the F/V EILEEN. Come in out of the weather."
- **Audio:** prologue.mp3, story-1.mp3, bed.mp3
- **Art:** assets/the-door.jpg
- **Experience:** Welcome sequence → enter the bar → story player

---

## 🌐 OTHER LIVE URLS

| Component | URL | Status |
|-----------|-----|--------|
| **Gallery** | https://luciddreamer.pages.dev (previous deploy) | ✅ Live (old version) |
| **AI Writings** | https://ai-writings.pages.dev | ✅ Live |
| **Tensor-MIDI** | https://tensor-midi.pages.dev | ✅ Live |
| **The Tap** | https://the-tap.casey-digennaro.workers.dev | ✅ Live |
| **The Tap Pub (frontend)** | https://the-tap-pub.pages.dev | ✅ Live |
| **ScummVM Prototype** | https://scummvm-prototype.pages.dev | ✅ Live |

---

## R2 Audio (to be uploaded)

| File | R2 Path | Status |
|------|---------|--------|
| prologue.mp3 | luciddreamer-audio/front-door-prologue.mp3 | ⏳ Pending |
| story-1.mp3 | luciddreamer-audio/front-door-story-1.mp3 | ⏳ Pending |

---

## ⚠️ DEPLOYMENT BLOCKER: CLOUDFLARE AUTH EXPIRED

**The wrangler OAuth token expired at 23:09 UTC (15:09 AKDT on 2026-08-11).**
The refresh token is also invalid. No CLOUDFLARE_API_TOKEN is in the environment.

### To unblock, run in an interactive terminal on Casey's machine:
```bash
wrangler login

# Then deploy:
cd /home/eileen/projects/luciddreamer-prototype
wrangler pages deploy front-door-experience/ --project-name luciddreamer

# Upload audio:
wrangler r2 object put luciddreamer-audio/front-door-prologue.mp3 --file=front-door-experience/audio/prologue.mp3
wrangler r2 object put luciddreamer-audio/front-door-story-1.mp3 --file=front-door-experience/audio/story-1.mp3
```

**Account ID:** 049ff5e84ecf636b53b162cbb580aae6
