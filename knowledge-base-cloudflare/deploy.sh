#!/usr/bin/env bash
#
# deploy.sh — One-command deploy of the Semantic Bridge to Cloudflare.
#
# Creates the Vectorize index, D1 database, runs migrations,
# vectorizes all ideas, and verifies the deployment.
#
# Usage:
#   ./deploy.sh                    # Full deploy
#   ./deploy.sh --dry-run          # Preview everything
#   ./deploy.sh --skip-vectorize   # Skip embedding (if already done)
#   ./deploy.sh --verify-only      # Just check current state

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INDEX_NAME="luciddreamer-kb"
D1_NAME="luciddreamer-kb"

# Colors
BOLD='\033[1m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${BLUE}▸${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }

# Parse args
DRY_RUN=false
SKIP_VECTORIZE=false
VERIFY_ONLY=false
for arg in "$@"; do
    case $arg in
        --dry-run)        DRY_RUN=true ;;
        --skip-vectorize) SKIP_VECTORIZE=true ;;
        --verify-only)    VERIFY_ONLY=true ;;
    esac
done

echo ""
echo -e "${BOLD}🌙 Semantic Bridge — Full Deploy${NC}"
echo -e "${BOLD}   The Molt: philosophy becomes queryable infrastructure${NC}"
echo ""
echo "   Index:      $INDEX_NAME"
echo "   Database:   $D1_NAME"
echo "   Project:    $PROJECT_DIR"
echo ""

# ─── Preflight ────────────────────────────────────────────────────────────────

log "Preflight checks..."

# Check wrangler auth
if ! command -v wrangler &>/dev/null; then
    err "wrangler not installed"
    exit 1
fi
ok "wrangler available"

WRANGLER_OUT=$(wrangler whoami 2>&1)
if echo "$WRANGLER_OUT" | grep -q "logged in"; then
    ok "wrangler authenticated"
else
    err "wrangler not authenticated. Run: wrangler login"
    exit 1
fi

# Check Ollama
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama online"
else
    warn "Ollama not responding (vectorization will fail)"
    if [ "$SKIP_VECTORIZE" = false ] && [ "$VERIFY_ONLY" = false ]; then
        err "Ollama required for vectorization. Start it or use --skip-vectorize"
        exit 1
    fi
fi

# Check nomic-embed-text model
if curl -sf http://localhost:11434/api/tags 2>/dev/null | grep -q "nomic-embed-text"; then
    ok "nomic-embed-text model available"
else
    warn "nomic-embed-text not found. Install: ollama pull nomic-embed-text"
    if [ "$SKIP_VECTORIZE" = false ] && [ "$VERIFY_ONLY" = false ]; then
        err "nomic-embed-text required for vectorization"
        exit 1
    fi
fi

# Check knowledge base
KB_PKL="$PROJECT_DIR/docs/knowledge-base/knowledge_base.pkl"
if [ -f "$KB_PKL" ]; then
    SIZE=$(du -h "$KB_PKL" | cut -f1)
    ok "Knowledge base found ($SIZE)"
else
    err "Knowledge base not found at $KB_PKL"
    exit 1
fi

echo ""

if [ "$VERIFY_ONLY" = true ]; then
    log "Verify-only mode"
    echo ""
    python3 "$SCRIPT_DIR/query_cloudflare.py" --stats
    echo ""
    python3 "$SCRIPT_DIR/d1_sync.py" --verify --db-name "$D1_NAME"
    exit 0
fi

# ─── Step 1: Create Vectorize Index ───────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ Step 1/5: Vectorize Index ━━━${NC}"
echo ""

if wrangler vectorize list 2>&1 | grep -q "$INDEX_NAME"; then
    ok "Index '$INDEX_NAME' already exists"
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create index '$INDEX_NAME' (768-dim, cosine)"
    else
        log "Creating Vectorize index '$INDEX_NAME' (768-dim, cosine)..."
        if wrangler vectorize create "$INDEX_NAME" \
            --dimensions 768 \
            --metric cosine \
            --description "LucidDreamer knowledge base — 1042 ideas, semantic search"; then
            ok "Index created"
        else
            warn "Index creation returned error (may already exist)"
        fi
    fi
fi

# ─── Step 2: Create D1 Database ───────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ Step 2/5: D1 Database ━━━${NC}"
echo ""

if wrangler d1 list 2>&1 | grep -q "$D1_NAME"; then
    ok "Database '$D1_NAME' already exists"
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create database '$D1_NAME'"
    else
        log "Creating D1 database '$D1_NAME'..."
        if wrangler d1 create "$D1_NAME" >/dev/null 2>&1; then
            ok "Database created"
        else
            warn "Database creation returned error (may already exist)"
        fi
    fi
fi

# ─── Step 3: Run D1 Migrations ────────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ Step 3/5: D1 Migrations ━━━${NC}"
echo ""

log "Generating SQL migrations..."
if [ "$DRY_RUN" = true ]; then
    python3 "$SCRIPT_DIR/d1_sync.py" --generate-only --db-name "$D1_NAME"
else
    python3 "$SCRIPT_DIR/d1_sync.py" --db-name "$D1_NAME"
fi

# ─── Step 4: Vectorize All Ideas ──────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ Step 4/5: Vectorize Ideas ━━━${NC}"
echo ""

if [ "$SKIP_VECTORIZE" = true ]; then
    warn "Skipping vectorization (--skip-vectorize)"
else
    if [ "$DRY_RUN" = true ]; then
        python3 "$SCRIPT_DIR/vectorize_ideas.py" --dry-run
    else
        python3 "$SCRIPT_DIR/vectorize_ideas.py"
    fi
fi

# ─── Step 5: Verify ───────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ Step 5/5: Verify ━━━${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Skipping verification"
else
    log "Verifying Vectorize index..."
    wrangler vectorize info "$INDEX_NAME" 2>&1 || warn "Could not get index info"

    echo ""
    log "Verifying D1 database..."
    python3 "$SCRIPT_DIR/d1_sync.py" --verify --db-name "$D1_NAME"
fi

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  ✅ Semantic Bridge deployed. The philosophy is queryable.${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Next:"
echo "    python3 $SCRIPT_DIR/query_cloudflare.py \"presence\""
echo "    python3 $SCRIPT_DIR/query_cloudflare.py --model hermes"
echo "    python3 $SCRIPT_DIR/query_cloudflare.py --type risk"
echo "    python3 $SCRIPT_DIR/query_cloudflare.py --status mature"
echo ""
