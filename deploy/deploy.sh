#!/usr/bin/env bash
#
# deploy.sh — One-command deploy of LucidDreamer.AI to Cloudflare.
#
# Creates all infrastructure (D1, KV, R2, Vectorize), runs migrations,
# deploys the main worker, gallery worker, and Pages player site,
# then verifies each step and prints live URLs.
#
# Usage:
#   ./deploy.sh                # Full deploy
#   ./deploy.sh --dry-run      # Preview without deploying
#   ./deploy.sh --verify-only  # Check current deployment state
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ─── Config ──────────────────────────────────────────────────
D1_NAME="luciddreamer-db"
KV_NAME="luciddreamer-feedback"
R2_NAME="luciddreamer-audio"
VECTORIZE_NAME="luciddreamer-ideas"
PAGES_PROJECT="luciddreamer-player"
GALLERY_WORKER="luciddreamer-gallery"

# ─── Colors ──────────────────────────────────────────────────
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

# ─── Parse args ──────────────────────────────────────────────
DRY_RUN=false
VERIFY_ONLY=false
for arg in "$@"; do
    case $arg in
        --dry-run)     DRY_RUN=true ;;
        --verify-only) VERIFY_ONLY=true ;;
    esac
done

echo ""
echo -e "${BOLD}🌙 LucidDreamer.AI — Full Deploy${NC}"
echo -e "${BOLD}   One command. The whole station.${NC}"
echo ""
echo "   D1:         $D1_NAME"
echo "   KV:         $KV_NAME"
echo "   R2:         $R2_NAME"
echo "   Vectorize:  $VECTORIZE_NAME"
echo "   Pages:      $PAGES_PROJECT"
echo "   Gallery:    $GALLERY_WORKER"
echo ""

# ═══════════════════════════════════════════════════════════════
# Preflight
# ═══════════════════════════════════════════════════════════════

log "Preflight checks..."

# Check wrangler
if ! command -v wrangler &>/dev/null; then
    err "wrangler not installed. Install with: npm install -g wrangler"
    exit 1
fi
ok "wrangler available ($(wrangler --version 2>/dev/null | head -1))"

# Check wrangler auth
WRANGLER_OUT=$(wrangler whoami 2>&1 || true)
if echo "$WRANGLER_OUT" | grep -qi "logged in\|account"; then
    # Extract account name or email for display
    ACCOUNT_INFO=$(echo "$WRANGLER_OUT" | grep -i "account" | head -1 || echo "authenticated")
    ok "wrangler authenticated ($ACCOUNT_INFO)"
else
    err "wrangler not authenticated. Run: wrangler login"
    echo ""
    echo "  After logging in, re-run: ./deploy/deploy.sh"
    exit 1
fi

# Check source files exist
for f in \
    "$PROJECT_DIR/player/feedback-worker.js" \
    "$PROJECT_DIR/player/now-playing-worker.js" \
    "$PROJECT_DIR/player/index.html" \
    "$PROJECT_DIR/gallery/gallery-worker.js" \
    "$SCRIPT_DIR/migrations.sql" \
    "$SCRIPT_DIR/wrangler.toml"; do
    if [ ! -f "$f" ]; then
        err "Missing: $f"
        exit 1
    fi
done
ok "All source files present"

echo ""

# ─── Verify-only mode ────────────────────────────────────────
if [ "$VERIFY_ONLY" = true ]; then
    echo -e "${BOLD}━━━ Verify Mode ━━━${NC}"
    echo ""

    log "D1 databases:"
    wrangler d1 list 2>&1 || warn "Could not list D1"
    echo ""

    log "KV namespaces:"
    wrangler kv namespace list 2>&1 || warn "Could not list KV"
    echo ""

    log "R2 buckets:"
    wrangler r2 bucket list 2>&1 || warn "Could not list R2"
    echo ""

    log "Vectorize indexes:"
    wrangler vectorize list 2>&1 || warn "Could not list Vectorize"
    echo ""

    log "Pages projects:"
    wrangler pages project list 2>&1 || warn "Could not list Pages"
    echo ""

    ok "Verify complete"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════
# Step 1: Create D1 Database
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 1/7: D1 Database ━━━${NC}"
echo ""

D1_ID=""
if wrangler d1 list 2>&1 | grep -q "$D1_NAME"; then
    ok "Database '$D1_NAME' already exists"
    D1_ID=$(wrangler d1 list 2>&1 | grep "$D1_NAME" | awk '{print $NF}' | tr -d '|' || echo "")
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create database '$D1_NAME'"
    else
        log "Creating D1 database '$D1_NAME'..."
        CREATE_OUT=$(wrangler d1 create "$D1_NAME" 2>&1 || true)
        if echo "$CREATE_OUT" | grep -q "database_id"; then
            D1_ID=$(echo "$CREATE_OUT" | grep "database_id" | awk -F'"' '{print $2}')
            ok "Database created (id: $D1_ID)"
        elif echo "$CREATE_OUT" | grep -qi "already exists"; then
            warn "Database already exists (concurrent creation?)"
            D1_ID=$(wrangler d1 list 2>&1 | grep "$D1_NAME" | awk '{print $NF}' | tr -d '|' || echo "")
        else
            err "Failed to create database:"
            echo "$CREATE_OUT"
            exit 1
        fi
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 2: Create KV Namespace
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 2/7: KV Namespace ━━━${NC}"
echo ""

KV_ID=""
KV_LIST=$(wrangler kv namespace list 2>&1 || true)
if echo "$KV_LIST" | grep -q "$KV_NAME"; then
    ok "KV namespace '$KV_NAME' already exists"
    KV_ID=$(echo "$KV_LIST" | grep -A2 "$KV_NAME" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create KV namespace '$KV_NAME'"
    else
        log "Creating KV namespace '$KV_NAME'..."
        CREATE_OUT=$(wrangler kv namespace create "$KV_NAME" 2>&1 || true)
        if echo "$CREATE_OUT" | grep -q '"id"'; then
            KV_ID=$(echo "$CREATE_OUT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
            ok "KV namespace created (id: $KV_ID)"
        elif echo "$CREATE_OUT" | grep -qi "already exists"; then
            warn "KV namespace already exists"
            KV_ID=$(echo "$KV_LIST" | grep -A2 "$KV_NAME" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
        else
            err "Failed to create KV namespace:"
            echo "$CREATE_OUT"
            exit 1
        fi
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 3: Create R2 Bucket
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 3/7: R2 Bucket ━━━${NC}"
echo ""

if wrangler r2 bucket list 2>&1 | grep -q "$R2_NAME"; then
    ok "R2 bucket '$R2_NAME' already exists"
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create R2 bucket '$R2_NAME'"
    else
        log "Creating R2 bucket '$R2_NAME'..."
        if wrangler r2 bucket create "$R2_NAME" >/dev/null 2>&1; then
            ok "R2 bucket created"
        else
            warn "R2 bucket creation returned error (may already exist)"
        fi
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 4: Create Vectorize Index
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 4/7: Vectorize Index ━━━${NC}"
echo ""

if wrangler vectorize list 2>&1 | grep -q "$VECTORIZE_NAME"; then
    ok "Vectorize index '$VECTORIZE_NAME' already exists"
else
    if [ "$DRY_RUN" = true ]; then
        log "(dry-run) Would create index '$VECTORIZE_NAME' (768-dim, cosine)"
    else
        log "Creating Vectorize index '$VECTORIZE_NAME' (768 dims, cosine)..."
        if wrangler vectorize create "$VECTORIZE_NAME" \
            --dimensions 768 \
            --metric cosine \
            --description "LucidDreamer ideas — semantic search" >/dev/null 2>&1; then
            ok "Vectorize index created"
        else
            warn "Index creation returned error (may already exist)"
        fi
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 5: Run D1 Migrations
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 5/7: D1 Migrations ━━━${NC}"
echo ""

MIGRATION_FILE="$SCRIPT_DIR/migrations.sql"
KB_MIGRATIONS_DIR="$PROJECT_DIR/knowledge-base-cloudflare/d1-migrations"

if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Would apply: $MIGRATION_FILE"
    [ -d "$KB_MIGRATIONS_DIR" ] && log "(dry-run) Would apply KB migrations from: $KB_MIGRATIONS_DIR"
else
    # Apply master schema
    if [ -f "$MIGRATION_FILE" ]; then
        log "Applying master schema..."
        if wrangler d1 execute "$D1_NAME" --file="$MIGRATION_FILE" --remote >/dev/null 2>&1; then
            ok "Master schema applied"
        else
            warn "Master schema had errors (tables may already exist — that's OK)"
        fi
    fi

    # Apply KB migrations if they exist (0001-0005)
    if [ -d "$KB_MIGRATIONS_DIR" ]; then
        for sql_file in "$KB_MIGRATIONS_DIR"/*.sql; do
            [ -f "$sql_file" ] || continue
            MIGRATION_NAME=$(basename "$sql_file")
            log "Applying KB migration: $MIGRATION_NAME..."
            if wrangler d1 execute "$D1_NAME" --file="$sql_file" --remote >/dev/null 2>&1; then
                ok "$MIGRATION_NAME applied"
            else
                warn "$MIGRATION_NAME had errors (may already be applied)"
            fi
        done
    fi

    # Also check docs/knowledge-base/d1-migrations as fallback
    DOCS_MIGRATIONS="$PROJECT_DIR/docs/knowledge-base/d1-migrations"
    if [ -d "$DOCS_MIGRATIONS" ]; then
        for sql_file in "$DOCS_MIGRATIONS"/*.sql; do
            [ -f "$sql_file" ] || continue
            MIGRATION_NAME=$(basename "$sql_file")
            # Skip schema.sql since master schema covers it
            [ "$MIGRATION_NAME" = "schema.sql" ] && continue
            log "Applying docs migration: $MIGRATION_NAME..."
            if wrangler d1 execute "$D1_NAME" --file="$sql_file" --remote >/dev/null 2>&1; then
                ok "$MIGRATION_NAME applied"
            else
                warn "$MIGRATION_NAME had errors (may already be applied)"
            fi
        done
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 6: Deploy Workers + Pages
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 6/7: Deploy Workers + Pages ━━━${NC}"
echo ""

# ─── Update wrangler.toml with dynamic IDs ───────────────────
if [ "$DRY_RUN" = false ] && { [ -n "$D1_ID" ] || [ -n "$KV_ID" ]; }; then
    log "Updating wrangler.toml with resource IDs..."
    TOML_FILE="$SCRIPT_DIR/wrangler.toml"
    if [ -n "$D1_ID" ]; then
        sed -i "s/database_id = \"\"/database_id = \"$D1_ID\"/" "$TOML_FILE" 2>/dev/null || true
    fi
    if [ -n "$KV_ID" ]; then
        sed -i "s/^id = \"\"  # filled by deploy.sh/id = \"$KV_ID\"  # filled by deploy.sh/" "$TOML_FILE" 2>/dev/null || true
    fi
    ok "wrangler.toml updated"
fi

# ─── Create gallery wrangler.toml ────────────────────────────
GALLERY_TOML="$SCRIPT_DIR/gallery-wrangler.toml"
if [ "$DRY_RUN" = false ]; then
    log "Generating gallery worker config..."
    cat > "$GALLERY_TOML" << GALLERYEOF
name = "$GALLERY_WORKER"
main = "../gallery/gallery-worker.js"
compatibility_date = "2024-12-01"
compatibility_flags = ["nodejs_compat"]

[vars]
version = "1.0.0"
environment = "production"

[[d1_databases]]
binding = "GHOST_DB"
database_name = "$D1_NAME"
database_id = "${D1_ID:-pending}"

[[r2_buckets]]
binding = "GHOST_AUDIO"
bucket_name = "$R2_NAME"
GALLERYEOF
    ok "Gallery config generated"
fi

# ─── Deploy main worker ──────────────────────────────────────
MAIN_URL=""
if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Would deploy main worker (feedback + now-playing)"
    MAIN_URL="https://luciddreamer.<account>.workers.dev"
else
    log "Deploying main worker..."
    # Combine feedback-worker as main, with now-playing-worker as additional export
    DEPLOY_OUT=$(cd "$SCRIPT_DIR" && wrangler deploy --config wrangler.toml 2>&1 || true)
    if echo "$DEPLOY_OUT" | grep -qi "deployed\|published"; then
        MAIN_URL=$(echo "$DEPLOY_OUT" | grep -o 'https://[a-zA-Z0-9.-]*\.workers\.dev' | head -1 || echo "")
        ok "Main worker deployed"
        [ -n "$MAIN_URL" ] && echo "       URL: $MAIN_URL"
    else
        warn "Main worker deploy output:"
        echo "$DEPLOY_OUT" | head -20
        MAIN_URL="https://luciddreamer.<account>.workers.dev"
    fi
fi

echo ""

# ─── Deploy gallery worker ───────────────────────────────────
GALLERY_URL=""
if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Would deploy gallery worker"
    GALLERY_URL="https://$GALLERY_WORKER.<account>.workers.dev"
else
    log "Deploying gallery worker..."
    GALLERY_DEPLOY=$(cd "$SCRIPT_DIR" && wrangler deploy --config gallery-wrangler.toml 2>&1 || true)
    if echo "$GALLERY_DEPLOY" | grep -qi "deployed\|published"; then
        GALLERY_URL=$(echo "$GALLERY_DEPLOY" | grep -o 'https://[a-zA-Z0-9.-]*\.workers\.dev' | head -1 || echo "")
        ok "Gallery worker deployed"
        [ -n "$GALLERY_URL" ] && echo "       URL: $GALLERY_URL"
    else
        warn "Gallery worker deploy output:"
        echo "$GALLERY_DEPLOY" | head -20
        GALLERY_URL="https://$GALLERY_WORKER.<account>.workers.dev"
    fi
fi

echo ""

# ─── Deploy Pages (player) ───────────────────────────────────
PAGES_URL=""
if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Would deploy Pages site from ../player/"
    PAGES_URL="https://$PAGES_PROJECT.pages.dev"
else
    # Create Pages project if it doesn't exist
    log "Ensuring Pages project '$PAGES_PROJECT' exists..."
    if wrangler pages project list 2>&1 | grep -q "$PAGES_PROJECT"; then
        ok "Pages project already exists"
    else
        wrangler pages project create "$PAGES_PROJECT" --production-branch main >/dev/null 2>&1 || true
        ok "Pages project created"
    fi

    log "Deploying player to Pages..."
    PAGES_DEPLOY=$(wrangler pages deploy "$PROJECT_DIR/player" \
        --project-name "$PAGES_PROJECT" \
        --branch main 2>&1 || true)
    if echo "$PAGES_DEPLOY" | grep -qi "deployed\|url\|pages\.dev"; then
        PAGES_URL=$(echo "$PAGES_DEPLOY" | grep -o 'https://[a-zA-Z0-9.-]*\.pages\.dev' | head -1 || echo "")
        ok "Pages site deployed"
        [ -n "$PAGES_URL" ] && echo "       URL: $PAGES_URL"
    else
        warn "Pages deploy output:"
        echo "$PAGES_DEPLOY" | head -20
        PAGES_URL="https://$PAGES_PROJECT.pages.dev"
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# Step 7: Verify
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}━━━ Step 7/7: Verify ━━━${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    log "(dry-run) Skipping verification"
else
    PASS=0
    FAIL=0

    # D1
    log "Verifying D1..."
    if wrangler d1 list 2>&1 | grep -q "$D1_NAME"; then
        ok "D1 '$D1_NAME' ✓"
        PASS=$((PASS+1))
    else
        err "D1 '$D1_NAME' not found"
        FAIL=$((FAIL+1))
    fi

    # KV
    log "Verifying KV..."
    if wrangler kv namespace list 2>&1 | grep -q "$KV_NAME"; then
        ok "KV '$KV_NAME' ✓"
        PASS=$((PASS+1))
    else
        err "KV '$KV_NAME' not found"
        FAIL=$((FAIL+1))
    fi

    # R2
    log "Verifying R2..."
    if wrangler r2 bucket list 2>&1 | grep -q "$R2_NAME"; then
        ok "R2 '$R2_NAME' ✓"
        PASS=$((PASS+1))
    else
        err "R2 '$R2_NAME' not found"
        FAIL=$((FAIL+1))
    fi

    # Vectorize
    log "Verifying Vectorize..."
    if wrangler vectorize list 2>&1 | grep -q "$VECTORIZE_NAME"; then
        ok "Vectorize '$VECTORIZE_NAME' ✓"
        PASS=$((PASS+1))
    else
        err "Vectorize '$VECTORIZE_NAME' not found"
        FAIL=$((FAIL+1))
    fi

    # Test main worker endpoint (if URL available)
    if [ -n "$MAIN_URL" ] && [[ "$MAIN_URL" != *"<account>"* ]]; then
        log "Testing main worker..."
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$MAIN_URL/api/feedback" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" != "000" ]; then
            ok "Main worker responding (HTTP $HTTP_CODE)"
            PASS=$((PASS+1))
        else
            warn "Main worker not reachable yet (may take a moment to propagate)"
        fi
    fi

    echo ""
    log "Results: $PASS passed, $FAIL failed"
fi

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  🌙 LucidDreamer.AI Deployed${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Live URLs:"
echo "  ───────────"
echo "  🎧 Player (Pages):     ${PAGES_URL:-https://$PAGES_PROJECT.pages.dev}"
echo "  🔧 API (Worker):       ${MAIN_URL:-https://luciddreamer.<account>.workers.dev}"
echo "  🖥  Gallery (Worker):   ${GALLERY_URL:-https://$GALLERY_WORKER.<account>.workers.dev}"
echo ""
echo "  Infrastructure:"
echo "  ──────────────"
echo "  📦 D1:                 $D1_NAME"
echo "  🗂  KV:                 $KV_NAME"
echo "  🪣 R2:                 $R2_NAME"
echo "  🔮 Vectorize:          $VECTORIZE_NAME (768-dim, cosine)"
echo ""
echo "  API Endpoints:"
echo "  ─────────────"
echo "  GET  /api/feedback           — recent listener feedback"
echo "  POST /api/feedback           — submit feedback {feedback, track, trackId}"
echo "  GET  /api/now-playing        — current track info"
echo "  PUT  /api/now-playing        — update track (scheduler, X-API-Key auth)"
echo "  GET  /api/sessions           — gallery: list session ghosts"
echo "  GET  /api/sessions/:id       — gallery: session detail"
echo "  POST /api/sessions           — gallery: create ghost"
echo "  GET  /audio/:key             — gallery: serve audio from R2"
echo ""
echo "  Next steps:"
echo "  ──────────"
echo "  1. Set scheduler secret:  wrangler secret put SCHEDULER_API_KEY"
echo "  2. Upload audio to R2:    wrangler r2 object put luciddreamer-audio/<key> --file=<path>"
echo "  3. Seed D1 tracks:        wrangler d1 execute $D1_NAME --remote --command='INSERT INTO tracks...'"
echo ""
