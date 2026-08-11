# @superinstance/feedback

**Feedback processing and now-playing API for LucidDreamer.AI.**

Two Cloudflare Workers that handle listener feedback collection and real-time now-playing metadata.

## Components

### Feedback Worker (`feedback-worker.js`)
Receives listener feedback from the web player, stores in KV with 30-day TTL.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/feedback` | POST | Submit feedback `{ feedback, track, trackId, timestamp }` |
| `/api/feedback` | GET | Recent feedback (admin/debug) |

### Now-Playing Worker (`now-playing-worker.js`)
Returns current track info, calculates elapsed time, advances to next track when current ends.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/now-playing` | GET | Current track + up next + listener count |
| `/api/now-playing` | PUT | Update now-playing (scheduler only, API key required) |

## Deploy

### Feedback Worker

```toml
# wrangler.toml
name = "luciddreamer-feedback"
main = "feedback-worker.js"
compatibility_date = "2024-12-01"

[[kv_namespaces]]
binding = "FEEDBACK_KV"
id = "REPLACE_WITH_YOUR_KV_ID"
```

```bash
wrangler deploy
```

### Now-Playing Worker

```toml
# wrangler.toml
name = "luciddreamer-now-playing"
main = "now-playing-worker.js"
compatibility_date = "2024-12-01"

[[kv_namespaces]]
binding = "NOW_PLAYING_KV"
id = "REPLACE_WITH_YOUR_KV_ID"

[vars]
SCHEDULER_API_KEY = "your-secret-key"
```

```bash
wrangler deploy
```

## Recommendation Engine (Future)

The feedback module will eventually include a recommendation engine that:
- Analyzes feedback sentiment and themes
- Correlates feedback with track characteristics (mood, model, time of day)
- Suggests track reordering and scheduling improvements
- Feeds back into the streamer's playlist weighting

## Dependencies

- Cloudflare Workers + KV

## License

MIT
