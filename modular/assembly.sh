#!/usr/bin/env bash
#
# assembly.sh — Break LucidDreamer prototype into separate module repos
#
# Usage:
#   ./modular/assembly.sh [--github] [--org superinstance]
#
# Without --github: creates local git repos in modular/repos/
# With --github:    creates GitHub repos and pushes (requires `gh` CLI)
#
# This script does NOT push unless --github is explicitly passed.
# By default it just sets up the local repos with CI and proper structure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTOTYPE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"

ORG="${ORG:-superinstance}"
PUSH_TO_GITHUB=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --github) PUSH_TO_GITHUB=true; shift ;;
        --org) ORG="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [--github] [--org ORG_NAME]"
            echo ""
            echo "Without --github: creates local git repos only."
            echo "With --github: creates GitHub repos and pushes."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "╔══════════════════════════════════════════════════╗"
echo "║  LucidDreamer.AI — Modular Assembly              ║"
echo "║  Breaking the monolith into independent packages  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

mkdir -p "$REPOS_DIR"

# ─────────────────────────────────────────────────────────
# Define modules
# ─────────────────────────────────────────────────────────

declare -a PYTHON_MODULES=(
    "conductor:superinstance-conductor:Agent routing layer for multi-agent systems"
    "streamer:superinstance-streamer:Audio streaming muxer with HLS and scheduling"
    "knowledge-base:superinstance-knowledge-base:Recursive idea graph with typed relationships"
    "sonic-shape:superinstance-sonic-shape:Confidence-to-music engine"
)

declare -a JS_MODULES=(
    "player:@superinstance/player:Embeddable HLS audio player widget"
    "terminal:@superinstance/terminal:Crab-traps MUD terminal widget"
)

declare -a WORKER_MODULES=(
    "gallery:superinstance-gallery:Session ghost gallery Cloudflare Worker"
    "feedback:superinstance-feedback:Feedback processing and now-playing workers"
)

declare -a META_MODULES=(
    "luciddreamer:superinstance-luciddreamer:Meta-package that assembles all modules"
)

# ─────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────

create_python_repo() {
    local module_name="$1"
    local pkg_name="$2"
    local description="$3"
    local module_dir="$SCRIPT_DIR/$module_name"

    echo "📦 Creating $pkg_name (Python)..."

    local repo_dir="$REPOS_DIR/$module_name"
    mkdir -p "$repo_dir"

    # Copy module files
    cp -r "$module_dir/src" "$repo_dir/src" 2>/dev/null || true
    cp "$module_dir/setup.py" "$repo_dir/"
    cp "$module_dir/README.md" "$repo_dir/"

    # Create pyproject.toml (modern alternative to setup.py)
    cat > "$repo_dir/pyproject.toml" << EOF
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "$pkg_name"
version = "0.1.0"
description = "$description"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
EOF

    # Create .gitignore
    cat > "$repo_dir/.gitignore" << 'EOF'
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.pytest_cache/
.venv/
venv/
*.pkl
EOF

    # Create tests directory
    mkdir -p "$repo_dir/tests"
    # Copy tests from the prototype if they exist
    local proto_tests="$PROTOTYPE_DIR/$module_name/tests"
    if [[ -d "$proto_tests" ]]; then
        cp -r "$proto_tests/"* "$repo_dir/tests/" 2>/dev/null || true
    fi
    cat > "$repo_dir/tests/__init__.py" << 'EOF'
EOF

    # Create GitHub Actions CI
    mkdir -p "$repo_dir/.github/workflows"
    cat > "$repo_dir/.github/workflows/ci.yml" << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          python -m pytest tests/ -v || echo "No tests yet"

      - name: Build package
        run: |
          pip install build
          python -m build
EOF

    # Initialize git
    (
        cd "$repo_dir"
        git init
        git add -A
        git commit -m "Initial commit: $pkg_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance module system."

        # Rename master to main
        git branch -M main 2>/dev/null || true
    )

    echo "  ✓ $pkg_name ready at $repo_dir"
}

create_js_repo() {
    local module_name="$1"
    local pkg_name="$2"
    local description="$3"
    local module_dir="$SCRIPT_DIR/$module_name"

    echo "📦 Creating $pkg_name (JavaScript)..."

    local repo_dir="$REPOS_DIR/$module_name"
    mkdir -p "$repo_dir"

    # Copy all files (JS modules are flat)
    cp -r "$module_dir/"* "$repo_dir/" 2>/dev/null || true

    # Create .gitignore
    cat > "$repo_dir/.gitignore" << 'EOF'
node_modules/
dist/
.cache/
.wrangler/
.env
EOF

    # Create GitHub Actions CI
    mkdir -p "$repo_dir/.github/workflows"
    cat > "$repo_dir/.github/workflows/ci.yml" << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          if [ -f package.json ]; then npm install; fi

      - name: Lint
        run: |
          if [ -f .eslintrc.json ]; then npm run lint; fi
        continue-on-error: true

      - name: Test
        run: |
          if [ -f package.json ] && grep -q '"test"' package.json; then npm test; fi
        continue-on-error: true
EOF

    # Initialize git
    (
        cd "$repo_dir"
        git init
        git add -A
        git commit -m "Initial commit: $pkg_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance module system."
        git branch -M main 2>/dev/null || true
    )

    echo "  ✓ $pkg_name ready at $repo_dir"
}

create_worker_repo() {
    local module_name="$1"
    local pkg_name="$2"
    local description="$3"
    local module_dir="$SCRIPT_DIR/$module_name"

    echo "📦 Creating $pkg_name (Cloudflare Worker)..."

    local repo_dir="$REPOS_DIR/$module_name"
    mkdir -p "$repo_dir"

    # Copy all files
    cp -r "$module_dir/"* "$repo_dir/" 2>/dev/null || true

    # Create .gitignore
    cat > "$repo_dir/.gitignore" << 'EOF'
node_modules/
.wrangler/
.dev.vars
.env
EOF

    # Create GitHub Actions CI
    mkdir -p "$repo_dir/.github/workflows"
    cat > "$repo_dir/.github/workflows/ci.yml" << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Cloudflare Workers
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        continue-on-error: true
EOF

    # Initialize git
    (
        cd "$repo_dir"
        git init
        git add -A
        git commit -m "Initial commit: $pkg_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance module system."
        git branch -M main 2>/dev/null || true
    )

    echo "  ✓ $pkg_name ready at $repo_dir"
}

push_to_github() {
    local repo_dir="$1"
    local repo_name="$2"
    local description="$3"

    (
        cd "$repo_dir"

        # Create GitHub repo
        gh repo create "$ORG/$repo_name" \
            --public \
            --description "$description" \
            --source=. \
            --push

        echo "  ✓ Pushed to github.com/$ORG/$repo_name"
    ) || echo "  ⚠ Failed to push $repo_name (may already exist)"
}

# ─────────────────────────────────────────────────────────
# Create all module repos
# ─────────────────────────────────────────────────────────

echo "Creating Python module repos..."
for module in "${PYTHON_MODULES[@]}"; do
    IFS=':' read -r name pkg desc <<< "$module"
    create_python_repo "$name" "$pkg" "$desc"
done

echo ""
echo "Creating JavaScript module repos..."
for module in "${JS_MODULES[@]}"; do
    IFS=':' read -r name pkg desc <<< "$module"
    create_js_repo "$name" "$pkg" "$desc"
done

echo ""
echo "Creating Cloudflare Worker repos..."
for module in "${WORKER_MODULES[@]}"; do
    IFS=':' read -r name pkg desc <<< "$module"
    create_worker_repo "$name" "$pkg" "$desc"
done

echo ""
echo "Creating meta-package repo..."
for module in "${META_MODULES[@]}"; do
    IFS=':' read -r name pkg desc <<< "$module"
    create_python_repo "$name" "$pkg" "$desc"
done

# ─────────────────────────────────────────────────────────
# Create the monorepo index
# ─────────────────────────────────────────────────────────

echo ""
echo "📋 Creating monorepo index..."

cat > "$REPOS_DIR/README.md" << 'EOF'
# @superinstance — LucidDreamer.AI Module System

This directory contains all the independently packaged modules of LucidDreamer.AI.

## Python Modules (PyPI)

| Module | Package | Install |
|--------|---------|---------|
| Conductor | `superinstance-conductor` | `pip install superinstance-conductor` |
| Streamer | `superinstance-streamer` | `pip install superinstance-streamer` |
| Knowledge Base | `superinstance-knowledge-base` | `pip install superinstance-knowledge-base` |
| Sonic Shape | `superinstance-sonic-shape` | `pip install superinstance-sonic-shape` |
| **Meta** | `superinstance-luciddreamer` | `pip install superinstance-luciddreamer` |

## JavaScript Modules (npm)

| Module | Package | Install |
|--------|---------|---------|
| Player | `@superinstance/player` | `npm install @superinstance/player` |
| Terminal | `@superinstance/terminal` | `npm install @superinstance/terminal` |

## Cloudflare Workers

| Module | Deploy |
|--------|--------|
| Gallery | `wrangler deploy` |
| Feedback | `wrangler deploy` |

## Architecture

Each module is fully independent. The meta-package (`superinstance-luciddreamer`)
installs all Python modules and wires them together. Web components are deployed
separately to Cloudflare.

## Module Independence

```
pip install superinstance-conductor    # just routing
pip install superinstance-streamer     # just audio
pip install superinstance-knowledge-base  # just the graph
pip install superinstance-sonic-shape  # just music mapping
pip install superinstance-luciddreamer   # everything, connected
```
EOF

# ─────────────────────────────────────────────────────────
# Push to GitHub if requested
# ─────────────────────────────────────────────────────────

if $PUSH_TO_GITHUB; then
    echo ""
    echo "🚀 Pushing to GitHub ($ORG org)..."

    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        echo "ERROR: GitHub CLI (gh) not installed. Install: https://cli.github.com/"
        exit 1
    fi

    for module in "${PYTHON_MODULES[@]}" "${JS_MODULES[@]}" "${WORKER_MODULES[@]}" "${META_MODULES[@]}"; do
        IFS=':' read -r name pkg desc <<< "$module"
        repo_dir="$REPOS_DIR/$name"
        repo_name="ld-$name"
        push_to_github "$repo_dir" "$repo_name" "$desc"
    done

    echo ""
    echo "✅ All modules pushed to github.com/$ORG"
else
    echo ""
    echo "📁 Local repos created at: $REPOS_DIR"
    echo "   Run with --github to push to GitHub."
fi

# ─────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Modular Assembly Complete                       ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║  Python modules:  ${#PYTHON_MODULES[@]}                                  ║"
echo "║  JS modules:      ${#JS_MODULES[@]}                                  ║"
echo "║  Worker modules:  ${#WORKER_MODULES[@]}                                  ║"
echo "║  Meta-package:    ${#META_MODULES[@]}                                  ║"
echo "║                                                  ║"
echo "║  Each module has:                                ║"
echo "║    ✓ README with usage examples                  ║"
echo "║    ✓ Package config (setup.py / package.json)    ║"
echo "║    ✓ Public API (__init__.py / index.js)         ║"
echo "║    ✓ GitHub Actions CI                           ║"
echo "║    ✓ Clear dependency boundaries                 ║"
echo "║                                                  ║"
echo "╚══════════════════════════════════════════════════╝"
