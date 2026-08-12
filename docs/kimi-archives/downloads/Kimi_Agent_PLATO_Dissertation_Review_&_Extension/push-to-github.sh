#!/bin/bash
# Push the swarm-enhanced chapters to GitHub
# Usage: bash push-to-github.sh <your-github-token>

set -e

TOKEN=${1:-$GITHUB_TOKEN}
REPO="SuperInstance/flux-research"
BRANCH="swarm-enhanced"
TEMP_DIR="/tmp/flux-research-push-$$"

if [ -z "$TOKEN" ]; then
    echo "Error: GitHub token required."
    echo "Usage: GITHUB_TOKEN=ghp_xxx bash push-to-github.sh"
    echo "Or:    bash push-to-github.sh ghp_xxx"
    exit 1
fi

echo "=== PLATO Swarm Enhancement Push Script ==="
echo "Repository: $REPO"
echo "Branch: $BRANCH"

# Clone the repository
echo "[1/6] Cloning repository..."
git clone --depth 1 "https://${TOKEN}@github.com/${REPO}.git" "$TEMP_DIR"
cd "$TEMP_DIR"

# Create new branch
echo "[2/6] Creating branch $BRANCH..."
git checkout -b "$BRANCH"

# Copy new chapter files
echo "[3/6] Copying swarm-enhanced chapters..."
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-09-SAFETY.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-10-TRUST.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-11-EPISTEMOLOGY.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-12-EMBODIMENT-CULTURE.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-13-UNIVERSAL.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/CHAPTER-14-HORIZON.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/SWARM-README.md dissertation/
cp /mnt/agents/output/flux-research-swarm-enhanced/dissertation/STRUCTURE-SWARM-ENHANCED.md dissertation/

# Stage files
echo "[4/6] Staging files..."
git add dissertation/CHAPTER-09-SAFETY.md
git add dissertation/CHAPTER-10-TRUST.md
git add dissertation/CHAPTER-11-EPISTEMOLOGY.md
git add dissertation/CHAPTER-12-EMBODIMENT-CULTURE.md
git add dissertation/CHAPTER-13-UNIVERSAL.md
git add dissertation/CHAPTER-14-HORIZON.md
git add dissertation/SWARM-README.md
git add dissertation/STRUCTURE-SWARM-ENHANCED.md

# Commit
echo "[5/6] Committing..."
git -c user.email="swarm@superinstance.ai" -c user.name="PLATO Research Swarm" \
    commit -m "feat(dissertation): swarm-enhanced chapters 9-14 — implications for AI safety, trust, epistemology, embodied cognition, universal applications, and 50-year horizon

This commit adds 6 new chapters (22,000+ words) produced by a 50+ agent
research swarm exploring world-changing implications of the PLATO framework.

New chapters:
- Ch 9: The Safety of Swimming — AI safety through presence
- Ch 10: Trust in the Ether — Distributed consensus as social contract
- Ch 11: The Epistemology of the Ether — Ethics of presence-based knowledge
- Ch 12: Swimming as Thinking — Embodied cognition and agent culture
- Ch 13: The Universal Ether — Applications beyond maritime
- Ch 14: Mathematics of Swarm Consciousness and 50-Year Horizon

250+ citations, 30+ original theoretical concepts."

# Push
echo "[6/6] Pushing to origin/$BRANCH..."
git push -u origin "$BRANCH"

echo ""
echo "=== SUCCESS ==="
echo "Branch '$BRANCH' pushed to $REPO"
echo "Create a PR: https://github.com/$REPO/pull/new/$BRANCH"

# Cleanup
rm -rf "$TEMP_DIR"
