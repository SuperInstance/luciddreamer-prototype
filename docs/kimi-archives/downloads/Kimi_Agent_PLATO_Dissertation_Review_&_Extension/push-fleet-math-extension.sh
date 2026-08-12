#!/bin/bash
# Push fleet-math-extension branch to GitHub
# Usage: GITHUB_TOKEN=ghp_xxx bash push-fleet-math-extension.sh

set -e
TOKEN=${1:-$GITHUB_TOKEN}
REPO="SuperInstance/flux-research"
BRANCH="fleet-math-extension"
TEMP_DIR="/tmp/flux-research-ext-$$"

if [ -z "$TOKEN" ]; then
    echo "Error: GitHub token required."
    echo "Usage: GITHUB_TOKEN=ghp_xxx bash push-fleet-math-extension.sh"
    exit 1
fi

echo "=== PLATO Fleet Math Extension Push ==="

# Clone
if [ ! -d "$TEMP_DIR/.git" ]; then
    echo "Cloning..."
    git clone --depth 1 "https://${TOKEN}@github.com/${REPO}.git" "$TEMP_DIR"
fi

cd "$TEMP_DIR"

# Create branch
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

# Copy files from our local package
PKG="/mnt/agents/output/flux-research-fleet-math-ext"
cp "$PKG"/dissertation/CHAPTER-09-SAFETY.md dissertation/ 2>/dev/null || true
cp "$PKG"/dissertation/CHAPTER-10-TRUST.md dissertation/ 2>/dev/null || true
cp "$PKG"/dissertation/CHAPTER-14-HORIZON.md dissertation/ 2>/dev/null || true
cp "$PKG"/dissertation/APPENDIX-C-EMERGENCE-DEFINITION.md dissertation/ 2>/dev/null || true
cp "$PKG"/dissertation/APPENDIX-D-ZHC-COMPLEXITY.md dissertation/ 2>/dev/null || true
cp "$PKG"/dissertation/APPENDIX-E-RIGIDITY-HOLONOMY-BRIDGE.md dissertation/ 2>/dev/null || true

# Stage and commit
git add -A
git -c user.email="swarm@superinstance.ai" -c user.name="PLATO Fleet Math Extension Swarm" \
    commit -m "feat(dissertation): fleet mathematics extension — formal proofs, complexity analysis, rigidity bridge

Three new appendices providing mathematical formalization:

APPENDIX-C: Non-Tautological Emergence Definition
- Fixes circular β₁ > 0 = emergence definition
- Defines emergence as d(β₁)/dt crossing zero (Scheffer et al. CSD)
- Persistent homology stability theorem (Cohen-Steiner et al. 2007)
- 2.7s window justified as empirical topological-behavioral lag

APPENDIX-D: Formal ZHC Complexity Analysis
- Naive implementation: O(C·L·N) with linear tile lookup
- HashMap-optimized: O(C·L), achieving claimed O(1) per-node
- PBFT 3-phase commit formal walkthrough: O(n²) messages
- Head-to-head comparison table with honest caveats
- 38ms claim decomposed: <1μs compute + 2×10ms network

APPENDIX-E: Rigidity-Holonomy Bridge Theorem
- Theorem: 3D bearing rigidity → well-defined cycle holonomy
- Proof sketches for all three parts (uniqueness, consistency, converse)
- 12-neighbor bound formally justified via rigidity constraints
- Corollary: structural trust + geometric trust equivalence

Line-level corrections to CH-09, CH-10, CH-14:
- Cross-references to appendices added
- Laman 2D → 3D bearing rigidity clarification
- O(1) claim qualified with HashMap optimization
" || true

# Push
git remote set-url origin "https://${TOKEN}@github.com/${REPO}.git"
git push -u origin "$BRANCH"

echo ""
echo "=== SUCCESS ==="
echo "Branch '$BRANCH' pushed to $REPO"
echo "Create PR: https://github.com/$REPO/pull/new/$BRANCH"

rm -rf "$TEMP_DIR"
