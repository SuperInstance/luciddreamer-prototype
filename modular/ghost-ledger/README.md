# 👻 Ghost Ledger

*Session compression into public artifacts*

![👻 Ghost Ledger](docs/images/ghost-ledger.jpg)

## What It Is

Every session leaves behind a Ghost — the compressed essence of what happened. The key quotes, the napkin drawings, the one-sentence distillation. The Ghost Ledger preserves them in a beautiful public gallery.

Not a log file. Not a transcript. A Ghost — the minimum viable memory that captures what mattered.

## Install

```bash
wrangler deploy
```

## Features

- Ghost compressor: session → 100-word essence + key quotes
- Beautiful responsive gallery with audio players
- Filter by model, date, theme
- Cloudflare Worker backend (D1 + R2)
- Seed script for existing sessions

## Quick Start

```python
from superinstance import ghost_ledger

# See docs/api/ghost-ledger-api.md for full documentation
```

## Use It For

**Conference talk archive that compresses each talk into a discoverable artifact**

Or anything else. This module is independently useful and Apache-2.0 licensed. Grow it for your industry. Send improvements back.

---

*Part of [LucidDreamer.AI](https://github.com/SuperInstance/luciddreamer-prototype) — built by [SuperInstance](https://github.com/SuperInstance).*
