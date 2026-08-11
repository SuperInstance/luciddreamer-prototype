# Live URLs — Last Updated 2026-08-11 15:38 AKDT

## Git Repos (all pushed, up to date)

| Repo | Branch | Remote |
|------|--------|--------|
| ai-writings | main | ✅ Up to date |
| luciddreamer-prototype | main | ✅ Up to date |
| hermes-ob1-core | master | ✅ Up to date |

## Cloudflare Pages Deployments

### Front Door Experience (luciddreamer)
- **Production URL:** https://luciddreamer.pages.dev — ✅ HTTP 200, serving content
- **Latest Deployment:** https://6bc1441d.luciddreamer.pages.dev — ✅ HTTP 200
- **Project:** `luciddreamer`
- **Source:** `front-door-experience/`

### Gallery (luciddreamer-gallery)
- **Production URL:** https://luciddreamer-gallery.pages.dev — ⚠️ 404 at root (no index.html; gallery uses gallery.html)
- **Gallery Page:** https://luciddreamer-gallery.pages.dev/gallery — ✅ HTTP 200
- **Latest Deployment:** https://e714020f.luciddreamer-gallery.pages.dev — ✅ Deployed
- **Gallery at deployment:** https://e714020f.luciddreamer-gallery.pages.dev/gallery — ✅ HTTP 200
- **Project:** `luciddreamer-gallery`
- **Source:** `gallery/`
- **Note:** Root returns 404 because the directory has `gallery.html` not `index.html`. To fix, either rename to `index.html` or set a custom redirect in Cloudflare Pages settings.

## Verification Summary

| URL | Status | Notes |
|-----|--------|-------|
| https://luciddreamer.pages.dev | ✅ 200 | Front door live, serving HTML |
| https://6bc1441d.luciddreamer.pages.dev | ✅ 200 | Deployment-specific URL |
| https://luciddreamer-gallery.pages.dev | ⚠️ 404 | No index.html at root |
| https://luciddreamer-gallery.pages.dev/gallery | ✅ 200 | Gallery page accessible |
| https://e714020f.luciddreamer-gallery.pages.dev/gallery | ✅ 200 | Deployment-specific gallery |

## All Clear ✅
Everything is pushed, deployed, and verified. The only minor issue is the gallery root URL returning 404 — easily fixed by renaming `gallery.html` → `index.html` if desired.
