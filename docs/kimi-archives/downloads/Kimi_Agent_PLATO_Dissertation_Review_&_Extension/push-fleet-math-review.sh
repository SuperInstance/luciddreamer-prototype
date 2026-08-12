#!/bin/bash
# Push the fleet-math-review branch to GitHub
# Usage: GITHUB_TOKEN=ghp_xxx bash push-fleet-math-review.sh

set -e
TOKEN=${1:-$GITHUB_TOKEN}
REPO="SuperInstance/flux-research"
BRANCH="fleet-math-review"
LOCAL_REPO="/tmp/flux-research-fleet"

if [ -z "$TOKEN" ]; then
    echo "Error: GitHub token required."
    echo "Usage: GITHUB_TOKEN=ghp_xxx bash push-fleet-math-review.sh"
    exit 1
fi

echo "=== PLATO Fleet Math Review Push ==="
echo "Branch: $BRANCH"

if [ ! -d "$LOCAL_REPO/.git" ]; then
    echo "Cloning repository..."
    git clone --depth 1 "https://${TOKEN}@github.com/${REPO}.git" "$LOCAL_REPO"
fi

cd "$LOCAL_REPO"

# Setup credentials for push
git remote set-url origin "https://${TOKEN}@github.com/${REPO}.git"

echo "Pushing branch $BRANCH..."
git push -u origin "$BRANCH"

echo ""
echo "=== SUCCESS ==="
echo "Branch '$BRANCH' pushed to $REPO"
echo "Create PR: https://github.com/$REPO/pull/new/$BRANCH"
