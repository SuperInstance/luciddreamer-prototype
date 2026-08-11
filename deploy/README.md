# LucidDreamer.AI — Deployment Guide

**One-command deploy to Cloudflare.** Infrastructure, workers, and player site — all of it.

---

## Prerequisites

1. **Node.js 18+** and npm
2. **Cloudflare account** (free tier works — all services have free quotas)
3. **Wrangler CLI** (Cloudflare's deploy tool)

### Install Wrangler

```bash
npm install -g wrangler
```

### Log in to Cloudflare

```bash
wrangler login
```

This opens a browser window. Authorize Wrangler to manage your Cloudflare account. You only do this once.

Verify it worked:

```bash
wrangler whoami
```

You should see your account name and email.

---

## Deploy

From the project root:

```bash
./deploy/deploy.sh
```

That's it. The script handles everything:

1. ✅ Creates D1 database (`luciddreamer-db`)
2. ✅ Creates KV namespace (`luciddreamer-feedback`)
3. ✅ Creates R2 bucket (`luciddreamer-audio`)
4. ✅ Creates Vectorize index (`luciddreamer-ideas` — 768 dims, cosine)
5. ✅ Runs all D1 migrations (schema + seed data)
6. ✅ Deploys main worker (player API + feedback + now-playing)
7. ✅ Deploys gallery worker (Ghost Ledger API)
8. ✅ Deploys Pages site (web player)
9. ✅ Verifies each step
10. ✅ Prints all live URLs

### Dry Run

Preview what would happen without making changes:

```bash
./deploy/deploy.sh --dry-run
```

### Verify Only

Check the current state of your Cloudflare resources:

```bash
./deploy/deploy.sh --verify-only
```

---

## What Gets Deployed

### Main Worker (`luciddreamer`)

**Source:** `player/feedback-worker.js` (with `now-playing-worker.js` logic merged)

**Bindings:**
| Binding | Type | Resource |
|---------|------|----------|
| `DB` | D1 | `luciddreamer-db` |
| `FEEDBACK` | KV | `luciddreamer-feedback` |
| `AUDIO` | R2 | `luciddreamer-audio` |
| `IDEAS` | Vectorize | `luciddreamer-ideas` |
| `AI` | Workers AI | Auto-provisioned |

**Endpoints:**
- `GET /api/feedback` — recent listener feedback
- `POST /api/feedback` — submit feedback `{feedback, track, trackId}`
- `GET /api/now-playing` — current track info
- `PUT /api/now-playing` — update track (scheduler only, `X-API-Key` auth)

### Gallery Worker (`luciddreamer-gallery`)

**Source:** `gallery/gallery-worker.js`

**Bindings:**
| Binding | Type | Resource |
|---------|------|----------|
| `GHOST_DB` | D1 | `luciddreamer-db` |
| `GHOST_AUDIO` | R2 | `luciddreamer-audio` |

**Endpoints:**
- `GET /api/sessions` — list session ghosts (supports `?model=`, `?date=`, `?theme=`)
- `GET /api/sessions/:id` — full session detail
- `POST /api/sessions` — create new ghost
- `GET /audio/:key` — serve audio from R2

### Pages Site (`luciddreamer-player`)

**Source:** `player/` directory (index.html, style.css, app.js)

Serves the web player at `https://luciddreamer-player.pages.dev`.

---

## D1 Schema

The `migrations.sql` file creates these tables:

| Table | Purpose |
|-------|---------|
| `tracks` | Audio content metadata (title, model, duration, R2 key, tags) |
| `feedback` | Listener feedback from the web player |
| `sessions` | Creative sessions that produced content |
| `now_playing` | Current/historical broadcast state |
| `ideas` | Knowledge base nodes (insights, risks, visions) |
| `relationships` | Typed edges between ideas |
| `models` | AI models in the fleet |
| `ghosts` | Gallery session records (Ghost Ledger) |

The script also applies seed migrations from `knowledge-base-cloudflare/d1-migrations/` (1042 ideas, 135 relationships, 34 sessions, 4 models) and `docs/knowledge-base/d1-migrations/` if available.

---

## Post-Deploy Setup

### Set the Scheduler API Key

The now-playing `PUT` endpoint requires an API key. Set it as a secret:

```bash
wrangler secret put SCHEDULER_API_KEY
```

Enter a strong random string. Share it with whatever scheduler updates the now-playing data.

### Upload Audio to R2

```bash
wrangler r2 object put luciddreamer-audio/track-001.mp3 --file=./path/to/track.mp3
```

### Seed a Track

```bash
wrangler d1 execute luciddreamer-db --remote --command="
  INSERT INTO tracks (id, title, source_model, duration, audio_key, tags)
  VALUES ('track-001', 'Channel 42 Bootstrap', 'Fleet', 180, 'track-001.mp3', '[\"ambient\",\"bootstrap\"]')
"
```

### Set Now-Playing

```bash
curl -X PUT https://luciddreamer.<account>.workers.dev/api/now-playing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-key>" \
  -d '{
    "key": "now-playing",
    "data": {
      "trackId": "track-001",
      "title": "Channel 42 Bootstrap",
      "model": "Fleet",
      "mood": "Ambient",
      "description": "The station is live.",
      "durationSeconds": 180
    }
  }'
```

---

## Troubleshooting

### "wrangler not authenticated"
Run `wrangler login` and complete the browser authorization.

### "D1 database already exists"
The script detects existing resources and skips creation. Safe to re-run.

### Worker deploy fails
Check that `deploy/wrangler.toml` has valid `database_id` and KV `id`. The script fills these in automatically on first run; if you deployed manually, update them.

### Pages deploy fails
Create the project first:
```bash
wrangler pages project create luciddreamer-player --production-branch main
```

### Vectorize creation fails
Vectorize may not be enabled on your account yet. See [Cloudflare Vectorize docs](https://developers.cloudflare.com/vectorize/).

---

## Architecture

```
                    ┌─────────────────────┐
                    │   Cloudflare Pages   │
                    │  (Web Player HTML)   │
                    │  luciddreamer-player │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   Main Worker        │
                    │  (feedback + API)    │
                    │    luciddreamer      │
                    └──┬─────┬─────┬──────┘
                       │     │     │
              ┌────────▼┐ ┌──▼──┐ ┌▼────────┐
              │ D1 DB   │ │ KV  │ │ R2      │
              │ (data)  │ │(fb) │ │(audio)  │
              └─────────┘ └─────┘ └─────────┘

                    ┌─────────────────────┐
                    │  Gallery Worker      │
                    │  (Ghost Ledger API)  │
                    │ luciddreamer-gallery │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   D1 + R2 (shared)   │
                    └─────────────────────┘

                    ┌─────────────────────┐
                    │   Vectorize Index    │
                    │  luciddreamer-ideas  │
                    │  (semantic search)   │
                    └─────────────────────┘
```

---

## Files

| File | Purpose |
|------|---------|
| `deploy/deploy.sh` | Master deployment script |
| `deploy/wrangler.toml` | Main worker Cloudflare config |
| `deploy/migrations.sql` | D1 database schema (all tables) |
| `deploy/README.md` | This file |
