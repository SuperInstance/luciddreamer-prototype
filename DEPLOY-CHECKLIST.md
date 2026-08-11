# LucidDreamer.AI — Deploy Checklist

**Last verified:** 2026-08-11 13:46 AKDT
**Account:** casey.digennaro@gmail.com (049ff5e84ecf636b53b162cbb580aae6)
**Wrangler:** v4.118.0 (v4.121.0 available)

---

## 1. What Exists vs What Needs Creating

### ✅ Already Exists (Cloudflare)

| Resource | Type | Name | Status |
|----------|------|------|--------|
| Pages | Site | `luciddreamer` | Live (luciddreamer.pages.dev) |
| Pages | Site | `luciddreamer-ai` | Live (luciddreamer-ai.pages.dev, 5 months old) |
| KV | Namespace | `luciddreamer-ai-kv` | Created |
| KV | Namespace | `luciddreamer-content` | Created |
| KV | Namespace | `luciddreamer-videos` | Created |
| R2 | Bucket | `luciddreamer-content` | Created |
| Vectorize | Index | `ai-writings` (768-dim, cosine) | Created |
| D1 | Database | `tap-db` | Created, empty (0 tables) |

### ❌ Needs Creating

| Resource | Type | Name | Purpose |
|----------|------|------|---------|
| D1 | Database | `luciddreamer-db` | Main schema (tracks, feedback, sessions, ideas, ghosts) |
| KV | Namespace | `luciddreamer-feedback` | Feedback storage |
| R2 | Bucket | `luciddreamer-audio` | Audio file storage |
| Vectorize | Index | `luciddreamer-ideas` | Semantic idea search (768-dim, cosine) |
| Worker | Deploy | `luciddreamer` | Main API (feedback + now-playing) |
| Worker | Deploy | `luciddreamer-gallery` | Ghost Ledger API |
| Secret | — | `SCHEDULER_API_KEY` | Auth for now-playing PUT |

### ⚠️ Exists But Stale / Ambiguous

| Resource | Note |
|----------|------|
| `luciddreamer-ai-kv` (KV) | Old namespace, may have stale data |
| `luciddreamer-content` (KV + R2) | Old content namespace/bucket from earlier prototypes |
| `luciddreamer-videos` (KV) | Unused? |
| Pages: `luciddreamer` vs `luciddreamer-ai` | Two Pages projects exist — pick one as canonical |

---

## 2. Order of Operations

### Phase 1: Create Infrastructure (idempotent — safe to re-run)

```bash
# 1. D1 Database
wrangler d1 create luciddreamer-db

# 2. KV Namespace
wrangler kv namespace create luciddreamer-feedback

# 3. R2 Bucket
wrangler r2 bucket create luciddreamer-audio

# 4. Vectorize Index (768 dims for bge-m3 / Workers AI embeddings)
wrangler vectorize create luciddreamer-ideas --dimensions 768 --metric cosine --description "LucidDreamer ideas — semantic search"
```

**Record the IDs output by each command.** You'll need them for wrangler.toml.

### Phase 2: Apply Database Schema

```bash
# 5. Apply master schema (creates all tables with IF NOT EXISTS)
wrangler d1 execute luciddreamer-db --remote --file=deploy/migrations.sql

# 6. Apply knowledge base seed migrations (if any exist)
# Check: ls knowledge-base-cloudflare/migrations/*.sql
# For each: wrangler d1 execute luciddreamer-db --remote --file=<migration.sql>
```

### Phase 3: Update wrangler.toml With Real IDs

Edit `deploy/wrangler.toml` — fill in the IDs from Phase 1:

```toml
[[d1_databases]]
binding = "DB"
database_name = "luciddreamer-db"
database_id = "<ID FROM STEP 1>"        # ← fill this in

[[kv_namespaces]]
binding = "FEEDBACK"
id = "<ID FROM STEP 2>"                  # ← fill this in
```

### Phase 4: Deploy Workers

```bash
# 7. Deploy main worker (API: feedback, now-playing)
cd deploy && wrangler deploy --config wrangler.toml

# 8. Deploy gallery worker (Ghost Ledger API)
# deploy.sh auto-generates gallery-wrangler.toml with the D1 ID
# OR create it manually using gallery/wrangler.toml as template
cd ../gallery && wrangler deploy
```

### Phase 5: Deploy/Update Pages

```bash
# 9. Pick canonical Pages project (recommend: "luciddreamer")
# If it doesn't exist yet:
wrangler pages project create luciddreamer-player --production-branch main

# Deploy the player site
wrangler pages deploy player --project-name luciddreamer-player --branch main
```

### Phase 6: Set Secrets

```bash
# 10. Set scheduler API key for now-playing updates
wrangler secret put SCHEDULER_API_KEY
# (enter a strong random string when prompted)
```

### Phase 7: Seed Content (optional but recommended)

```bash
# 11. Upload first audio track to R2
wrangler r2 object put luciddreamer-audio/track-001.mp3 --file=./path/to/audio.mp3

# 12. Seed a track in D1
wrangler d1 execute luciddreamer-db --remote --command="
  INSERT INTO tracks (id, title, source_model, duration, audio_key, tags)
  VALUES ('track-001', 'Channel 42 Bootstrap', 'Fleet', 180, 'track-001.mp3', '[\"ambient\",\"bootstrap\"]')
"

# 13. Set now-playing
curl -X PUT https://luciddreamer.<account>.workers.dev/api/now-playing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-secret>" \
  -d '{"key":"now-playing","data":{"trackId":"track-001","title":"Channel 42 Bootstrap","model":"Fleet","mood":"Ambient"}}'
```

### Phase 8: Custom Domain (optional)

```bash
# 14. Map luciddreamer.ai domain (if owned)
# Via Cloudflare dashboard or:
wrangler pages deployment setup --project-name luciddreamer-player --domain luciddreamer.ai
```

---

## 3. One-Command Option

The deploy script handles all of phases 1-5 automatically:

```bash
cd deploy && ./deploy.sh              # Full deploy
cd deploy && ./deploy.sh --dry-run    # Preview
cd deploy && ./deploy.sh --verify-only # Check state
```

The script:
- Creates all infrastructure (skips if already exists)
- Runs migrations (all tables use IF NOT EXISTS)
- Fills in resource IDs in wrangler.toml automatically
- Deploys main worker + gallery worker + Pages site
- Verifies each step

**After the script completes**, still manually:
- Set `SCHEDULER_API_KEY` secret
- Upload audio + seed tracks
- Configure custom domain if desired

---

## 4. What Could Go Wrong

### 🔴 High Risk

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **Vectorize not enabled on account** | Deploy script fails at step 4 | Pre-check: `wrangler vectorize list` (✅ confirmed working) |
| **wrangler.toml has empty IDs** | Worker deploy fails — bindings don't resolve | deploy.sh fills these automatically; if running manually, fill them in |
| **Main worker source path mismatch** | deploy/wrangler.toml points to `../player/feedback-worker.js` — must exist | ✅ Verified: player/ dir has feedback-worker.js |
| **Two Pages projects** (luciddreamer vs luciddreamer-ai) | Confusion about which is canonical | Pick `luciddreamer` going forward. Leave old one as-is or delete via dashboard |

### 🟡 Medium Risk

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **D1 migration conflicts** | Tables created by older scripts may conflict | All tables use `IF NOT EXISTS` — re-running is safe |
| **Gallery wrangler.toml uses different DB name** (`ch42-ghost-ledger` vs `luciddreamer-db`) | Gallery worker fails to bind D1 | deploy.sh generates correct gallery config; manual deploy needs updated config |
| **Player wrangler configs use old names** (`ch42-feedback`, `ch42-now-playing`) | Separate worker deploys use wrong names | Use the unified deploy/wrangler.toml which combines everything |
| **KV namespace name mismatch** | deploy.sh creates `luciddreamer-feedback` but gallery/player tomls reference `FEEDBACK_KV` | The unified config in deploy/wrangler.toml uses binding `FEEDBACK` — this is the canonical one |
| **R2 bucket doesn't exist for audio** | Worker can't serve audio | Step 3 creates it; gallery/player configs reference it |

### 🟢 Low Risk

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **Wrangler version outdated** (4.118 vs 4.121) | Minor — no breaking changes expected | `npm update -g wrangler` when convenient |
| **Old Cloudflare resources clutter** | Account has 20 D1 DBs, 120+ KV namespaces, 20 R2 buckets | Not harmful. Clean up via dashboard if desired. |
| **DNS propagation delay for custom domain** | luciddreamer.ai may not resolve immediately | Use *.pages.dev and *.workers.dev URLs until DNS settles |
| **ai-writings Vectorize index dimensions** | `ai-writings` index is 768-dim — matches the new `luciddreamer-ideas` | ✅ Consistent, no issue |

---

## 5. Verification Commands (Post-Deploy)

```bash
# Check infrastructure exists
wrangler d1 list | grep luciddreamer
wrangler kv namespace list | grep luciddreamer-feedback
wrangler r2 bucket list | grep luciddreamer-audio
wrangler vectorize list | grep luciddreamer-ideas

# Check D1 tables
wrangler d1 execute luciddreamer-db --remote --command="SELECT name FROM sqlite_master WHERE type='table'"

# Test worker endpoint
curl -s https://luciddreamer.<account>.workers.dev/api/feedback | head -20

# Test gallery endpoint
curl -s https://luciddreamer-gallery.<account>.workers.dev/api/sessions | head -20

# Test Pages
curl -s https://luciddreamer-player.pages.dev | head -5

# Check secret is set
wrangler secret list
```

---

## 6. Resource Summary After Deploy

| Component | URL/ID | Type |
|-----------|--------|------|
| Player | https://luciddreamer-player.pages.dev | Pages |
| API | https://luciddreamer.{account}.workers.dev | Worker |
| Gallery | https://luciddreamer-gallery.{account}.workers.dev | Worker |
| Database | luciddreamer-db (D1) | SQLite |
| Feedback KV | luciddreamer-feedback (KV) | Key-Value |
| Audio | luciddreamer-audio (R2) | Object Storage |
| Ideas Search | luciddreamer-ideas (Vectorize) | Vector Index |
| AI | Workers AI binding | Auto-provisioned |

---

## Notes

- The `deploy.sh` script is robust — it was written for exactly this and handles existing resources gracefully
- All D1 migrations use `IF NOT EXISTS` so re-running never breaks
- The gallery worker (`gallery/wrangler.toml`) references `ch42-ghost-ledger` DB — this is the **old name**. The unified deploy creates `luciddreamer-db` and the generated gallery config uses the correct name
- Two Pages projects exist (`luciddreamer` and `luciddreamer-ai`). Recommend standardizing on `luciddreamer-player` for the new deployment
- The existing `luciddreamer-content` R2 bucket and KV namespace are from an earlier prototype and are **not the same** as `luciddreamer-audio` and `luciddreamer-feedback`
