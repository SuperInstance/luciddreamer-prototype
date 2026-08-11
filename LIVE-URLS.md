# LucidDreamer.AI — Live URLs

Last updated: 2026-08-11 15:22 AKDT

## ⚠️ DEPLOYMENT STATUS: PENDING — CLOUDFLARE AUTH EXPIRED

All infrastructure creation and deployment commands were attempted but failed because:
- The wrangler OAuth token expired at 23:09 UTC (15:09 AKDT on 2026-08-11)
- The refresh token is also expired/invalid
- No CLOUDFLARE_API_TOKEN is set in the environment
- No interactive browser available for OAuth re-login

### What's Needed
Run `wrangler login` in an interactive terminal (Casey's machine with browser),
then re-run the deploy commands below.

---

## Expected URLs (once deployed)

| Component | URL | Status |
|-----------|-----|--------|
| **Main Player** | https://luciddreamer-player.pages.dev | ⏳ Pending |
| **Gallery** | https://luciddreamer-gallery.pages.dev | ⏳ Pending |
| **Front Door** | (deploys as player/ — no front-door-experience/ dir) | ⏳ Pending |
| **R2 Audio: dawn-broadcast** | https://luciddreamer-audio.r2.dev/dawn-broadcast.mp3 | ⏳ Pending |
| **R2 Audio: the-tap-song** | https://luciddreamer-audio.r2.dev/the-tap-song.mp3 | ⏳ Pending |

## Infrastructure (to be created)

| Resource | Name | Status |
|----------|------|--------|
| D1 Database | luciddreamer-db | ⏳ Pending |
| KV Namespace | LUCIDDREAMER_FEEDBACK | ⏳ Pending |
| R2 Bucket | luciddreamer-audio | ⏳ Pending |
| Vectorize Index | luciddreamer-ideas (768d, cosine) | ⏳ Pending |

---

## Deployment Commands (run after `wrangler login`)

```bash
# 1. Create infrastructure
wrangler d1 create luciddreamer-db
wrangler kv namespace create LUCIDDREAMER_FEEDBACK
wrangler r2 bucket create luciddreamer-audio
wrangler vectorize create luciddreamer-ideas --dimensions 768 --metric cosine

# 2. Deploy Pages
cd /home/eileen/projects/luciddreamer-prototype
wrangler pages deploy player/ --project-name luciddreamer-player
wrangler pages deploy gallery/ --project-name luciddreamer-gallery

# 3. Upload audio to R2
wrangler r2 object put luciddreamer-audio/dawn-broadcast.mp3 \
  --file=/home/eileen/projects/ai-writings/radio-theater/channel-42-dawn/dawn-broadcast.mp3
wrangler r2 object put luciddreamer-audio/the-tap-song.mp3 \
  --file=/home/eileen/projects/ai-writings/radio-theater/the-tap-song.mp3
```

## Note
- `front-door-experience/` directory does not exist in the prototype
- Player is deployed as the main site
- Account ID: 049ff5e84ecf636b53b162cbb580aae6
