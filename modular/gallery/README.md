# @superinstance/gallery

**Session ghost gallery — every conversation compressed to its essence.**

A Cloudflare Worker that serves compressed session "ghosts" — the distilled soul of each conversation. Deployable independently to Cloudflare Workers + D1 + R2.

> Every session a ghost. Every ghost a trace.

## Deploy

```bash
wrangler deploy
```

## What It Does

- **Ghost compression** — takes raw session markdown and extracts title, date, models present, key quotes, napkin drawings, themes, and a ~100-word essence
- **Gallery API** — RESTful API for browsing ghosts by date, model, or theme
- **Audio serving** — serves associated audio from R2
- **D1-backed** — session metadata stored in D1 for fast queries
- **R2-backed** — audio files stored in R2

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List all ghosts (with optional `?model=`, `?date=`, `?theme=` filters) |
| `/api/sessions/:id` | GET | Full ghost detail with complete text |
| `/api/sessions` | POST | Create a new ghost |
| `/audio/:key` | GET | Serve audio from R2 |
| `/` | GET | Gallery HTML page |

## Wrangler Configuration

```toml
# wrangler.toml
name = "luciddreamer-gallery"
main = "gallery-worker.js"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "GHOST_DB"
database_name = "luciddreamer-ghosts"
database_id = "your-d1-id"

[[r2_buckets]]
binding = "GHOST_AUDIO"
bucket_name = "luciddreamer-ghost-audio"
```

## Standalone Usage

### Compress sessions

```bash
python3 ghost_compressor.py session.md --output ghost.json
python3 ghost_compressor.py --batch ./docs/ --output gallery_data.json
```

### Seed the gallery

```bash
python3 seed_data.py --source ../docs --seed-api --api-url https://gallery.luciddreamer.ai/api
```

## Dependencies

**Required:**
- Cloudflare account (Workers, D1, R2)
- `wrangler` CLI

**For ghost compression:**
- Python 3.10+ (standard library only)

## License

MIT
