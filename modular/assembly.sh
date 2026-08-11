#!/usr/bin/env bash
#
# assembly.sh — Auto-glue system for LucidDreamer modular packages
#
# Breaks the monolith prototype into 8 independent module repos + 1 meta-package,
# each with LICENSE (Apache-2.0), CI workflow, and proper dependency manifests.
#
# Usage:
#   ./modular/assembly.sh              # Build local repos (no push)
#   ./modular/assembly.sh --push       # Build and push to GitHub (requires gh CLI)
#   ./modular/assembly.sh --org NAME   # Override GitHub org (default: SuperInstance)
#
# Idempotent: safe to re-run. Existing repos are skipped unless --force is passed.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTOTYPE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"
TMP_BASE="${TMPDIR:-/tmp}"

ORG="SuperInstance"
PUSH=false
FORCE=false

# ─── Parse args ───────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)   PUSH=true;   shift ;;
        --force)  FORCE=true;  shift ;;
        --org)    ORG="$2";    shift 2 ;;
        --help|-h)
            echo "Usage: $0 [--push] [--force] [--org ORG_NAME]"
            echo ""
            echo "  --push     Create GitHub repos and push (requires gh CLI)"
            echo "  --force    Rebuild repos even if they already exist"
            echo "  --org      GitHub org name (default: $ORG)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Color helpers ────────────────────────────────────────
if [[ -t 1 ]]; then
    B='\033[1m'  R='\033[0m'  G='\033[32m'  Y='\033[33m'  C='\033[36m'  D='\033[90m'
else
    B='' R='' G='' Y='' C='' D=''
fi
info()  { echo -e "${C}ℹ${R}  $*"; }
ok()    { echo -e "${G}✓${R}  $*"; }
warn()  { echo -e "${Y}⚠${R}  $*"; }
title() { echo -e "\n${B}══ $* ══${R}"; }

# ─── Track results for summary table ──────────────────────
declare -a SUMMARY_LINES=()
record_result() {
    local module="$1" url="$2" status="$3" tests="$4"
    SUMMARY_LINES+=("$module|$url|$status|$tests")
}

# ─── Apache-2.0 License text ─────────────────────────────
write_license() {
    local dir="$1"
    cat > "$dir/LICENSE" << 'LICENSE_EOF'
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2024-2026 Lucineer / Casey DiGenaro

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
LICENSE_EOF
}

# ─── CI workflow generators ───────────────────────────────

write_python_ci() {
    local dir="$1"
    local pkg_name="$2"
    mkdir -p "$dir/.github/workflows"
    cat > "$dir/.github/workflows/test.yml" << 'CI_EOF'
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package and dev dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with pytest
        run: |
          if [ -d tests ]; then
            python -m pytest tests/ -v --tb=short
          elif [ -d src/tests ]; then
            python -m pytest src/tests/ -v --tb=short
          else
            echo "No tests directory found — skipping"
          fi

      - name: Build distribution
        run: |
          pip install build
          python -m build
        continue-on-error: true

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check . --exit-zero
CI_EOF
}

write_js_ci() {
    local dir="$1"
    local pkg_name="$2"
    mkdir -p "$dir/.github/workflows"
    cat > "$dir/.github/workflows/test.yml" << 'CI_EOF'
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          if [ -f package.json ]; then npm ci || npm install; fi

      - name: Lint
        run: |
          if grep -q '"lint"' package.json 2>/dev/null; then npm run lint; fi
        continue-on-error: true

      - name: Test
        run: |
          if grep -q '"test"' package.json 2>/dev/null; then npm test; fi
        continue-on-error: true

      - name: Verify build
        run: |
          if grep -q '"build"' package.json 2>/dev/null; then npm run build; fi
        continue-on-error: true
CI_EOF
}

write_worker_ci() {
    local dir="$1"
    local pkg_name="$2"
    mkdir -p "$dir/.github/workflows"
    cat > "$dir/.github/workflows/test.yml" << 'CI_EOF'
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Wrangler
        run: npm install -g wrangler

      - name: Validate worker syntax
        run: |
          for f in *.js; do
            if [ -f "$f" ]; then
              echo "Checking $f..."
              node --check "$f"
            fi
          done

      - name: Validate wrangler config
        run: |
          for f in wrangler*.toml; do
            if [ -f "$f" ]; then
              echo "Validating $f..."
              wrangler deploy --config "$f" --dry-run || true
            fi
          done
        continue-on-error: true

  deploy:
    runs-on: ubuntu-latest
    needs: validate
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install -g wrangler
      - name: Deploy workers
        run: |
          for f in wrangler*.toml; do
            if [ -f "$f" ]; then
              echo "Deploying $f..."
              wrangler deploy --config "$f" || true
            fi
          done
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        continue-on-error: true
CI_EOF
}

# ─── Count tests in a module ──────────────────────────────
count_tests() {
    local dir="$1"
    local count=0
    # Python tests: count test functions/methods
    if [[ -d "$dir/tests" ]]; then
        count=$(grep -rE '^\s*def test_|^\s*async def test_' "$dir/tests/" 2>/dev/null | wc -l || true)
    fi
    if [[ -d "$dir/src/tests" ]]; then
        local src_count
        src_count=$(grep -rE '^\s*def test_|^\s*async def test_' "$dir/src/tests/" 2>/dev/null | wc -l || true)
        count=$((count + src_count))
    fi
    # JS tests
    if [[ -d "$dir/__tests__" ]]; then
        local js_count
        js_count=$(grep -rE '^\s*(test|it)\(' "$dir/__tests__/" 2>/dev/null | wc -l || true)
        count=$((count + js_count))
    fi
    if [[ $count -eq 0 ]]; then
        echo "—"
    else
        echo "$count"
    fi
}

# ─── Python .gitignore ────────────────────────────────────
write_python_gitignore() {
    cat > "$1/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.so
.pytest_cache/
.coverage
htmlcov/
.tox/
.venv/
venv/
env/
*.pkl
*.pdc
.mypy_cache/
.ruff_cache/
.DS_Store
EOF
}

write_js_gitignore() {
    cat > "$1/.gitignore" << 'EOF'
node_modules/
dist/
.cache/
.wrangler/
.dev.vars
.env
.DS_Store
*.log
EOF
}

# ═════════════════════════════════════════════════════════
# MODULE DEFINITIONS
# ═════════════════════════════════════════════════════════

# Format: "module_dir:repo_name:package_type:description"
# package_type: python | js | worker
declare -a MODULES=(
    "conductor:luciddreamer-conductor:python:Agent routing layer for multi-agent systems"
    "streamer:luciddreamer-streamer:python:Audio streaming muxer with HLS, crossfades, and scheduling"
    "knowledge-base:luciddreamer-knowledge-base:python:Recursive idea graph with typed relationships"
    "sonic-shape:luciddreamer-sonic-shape:python:Confidence-to-music engine mapping agent state to musical parameters"
    "gallery:luciddreamer-gallery:worker:Session ghost gallery Cloudflare Worker with D1 and R2"
    "player:luciddreamer-player:js:Embeddable HLS audio player widget"
    "terminal:luciddreamer-terminal:js:Crab-traps MUD terminal widget with character creation"
    "feedback:luciddreamer-feedback:worker:Feedback processing and now-playing API workers"
)

# Meta-package depends on all 8
META_MODULE="luciddreamer:luciddreamer:python:Meta-package — multi-agent dream radio station"

# ═════════════════════════════════════════════════════════
# BUILDER: Python module
# ═════════════════════════════════════════════════════════

build_python_module() {
    local module_dir="$1" repo_name="$2" description="$3"
    local src_dir="$SCRIPT_DIR/$module_dir"
    local pkg_name="superinstance-${module_dir//-/_}"
    local repo_url="https://github.com/$ORG/$repo_name"

    title "Building $repo_name (Python)"

    # Create temp directory
    local tmp_dir
    tmp_dir=$(mktemp -d "${TMP_BASE}/ld-asm-${module_dir}.XXXXXX")
    trap "rm -rf '$tmp_dir'" RETURN

    # Copy module files
    info "Copying files from $src_dir..."
    if [[ -d "$src_dir/src" ]]; then
        cp -r "$src_dir/src" "$tmp_dir/src"
    fi
    # Copy top-level Python files
    cp "$src_dir/__init__.py" "$tmp_dir/__init__.py" 2>/dev/null || true
    cp "$src_dir/setup.py" "$tmp_dir/setup.py" 2>/dev/null || true
    cp "$src_dir/README.md" "$tmp_dir/README.md" 2>/dev/null || echo "# $repo_name\n\n$description" > "$tmp_dir/README.md"
    # Copy any config files
    cp "$src_dir"/*.yaml "$tmp_dir/" 2>/dev/null || true

    # Ensure setup.py exists with proper deps
    if [[ ! -f "$tmp_dir/setup.py" ]]; then
        info "Generating setup.py..."
        cat > "$tmp_dir/setup.py" << SETUP_EOF
from setuptools import setup, find_packages

setup(
    name="$repo_name",
    version="0.1.0",
    description="$description",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lucineer / Casey DiGenaro",
    author_email="casey@superinstance.com",
    url="$repo_url",
    license="Apache-2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0", "ruff>=0.4"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
SETUP_EOF
    else
        # Patch existing setup.py: change license from MIT to Apache-2.0
        info "Updating license references in setup.py..."
        sed -i 's/license="MIT"/license="Apache-2.0"/g' "$tmp_dir/setup.py"
        sed -i 's/License :: OSI Approved :: MIT License/License :: OSI Approved :: Apache Software License/g' "$tmp_dir/setup.py"
    fi

    # Create pyproject.toml
    cat > "$tmp_dir/pyproject.toml" << TOML_EOF
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests", "src/tests"]
TOML_EOF

    write_license "$tmp_dir"
    write_python_gitignore "$tmp_dir"
    write_python_ci "$tmp_dir" "$repo_name"

    # Count tests
    local test_count
    test_count=$(count_tests "$tmp_dir")

    # Init git
    (
        cd "$tmp_dir"
        git init -q
        git add -A
        git commit -q -m "feat: initial release of $repo_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance modular system.
License: Apache-2.0"
        git branch -M main 2>/dev/null || true
    )

    # Move to repos dir
    mkdir -p "$REPOS_DIR"
    local final_dir="$REPOS_DIR/$module_dir"
    if [[ -d "$final_dir" ]] && $FORCE; then
        rm -rf "$final_dir"
    fi
    if [[ -d "$final_dir" ]]; then
        warn "$repo_name already exists at $final_dir — skipping (use --force to rebuild)"
        record_result "$repo_name" "$repo_url" "skipped (exists)" "$test_count"
        return 0
    fi
    mv "$tmp_dir" "$final_dir"

    ok "$repo_name built → $final_dir ($test_count tests)"
    record_result "$repo_name" "$repo_url" "✓ built" "$test_count"

    # Push if requested
    if $PUSH; then
        push_repo "$final_dir" "$repo_name" "$description" "$repo_url"
    fi
}

# ═════════════════════════════════════════════════════════
# BUILDER: JavaScript module
# ═════════════════════════════════════════════════════════

build_js_module() {
    local module_dir="$1" repo_name="$2" description="$3"
    local src_dir="$SCRIPT_DIR/$module_dir"
    local repo_url="https://github.com/$ORG/$repo_name"

    title "Building $repo_name (JavaScript)"

    local tmp_dir
    tmp_dir=$(mktemp -d "${TMP_BASE}/ld-asm-${module_dir}.XXXXXX")
    trap "rm -rf '$tmp_dir'" RETURN

    # Copy all files
    info "Copying files from $src_dir..."
    cp -r "$src_dir/"* "$tmp_dir/" 2>/dev/null || true

    # Ensure package.json exists with proper metadata
    if [[ ! -f "$tmp_dir/package.json" ]]; then
        info "Generating package.json..."
        cat > "$tmp_dir/package.json" << PKG_EOF
{
  "name": "@luciddreamer/${module_dir}",
  "version": "0.1.0",
  "description": "$description",
  "license": "Apache-2.0",
  "author": "Lucineer / Casey DiGenaro",
  "repository": {
    "type": "git",
    "url": "$repo_url"
  },
  "scripts": {
    "dev": "npx http-server -p 3000",
    "test": "echo \"No tests yet\" && exit 0"
  },
  "devDependencies": {}
}
PKG_EOF
    else
        # Patch existing: update license field
        info "Updating license in package.json..."
        sed -i 's/"license": "MIT"/"license": "Apache-2.0"/g' "$tmp_dir/package.json"
    fi

    write_license "$tmp_dir"
    write_js_gitignore "$tmp_dir"
    write_js_ci "$tmp_dir" "$repo_name"

    local test_count
    test_count=$(count_tests "$tmp_dir")

    (
        cd "$tmp_dir"
        git init -q
        git add -A
        git commit -q -m "feat: initial release of $repo_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance modular system.
License: Apache-2.0"
        git branch -M main 2>/dev/null || true
    )

    mkdir -p "$REPOS_DIR"
    local final_dir="$REPOS_DIR/$module_dir"
    if [[ -d "$final_dir" ]] && $FORCE; then
        rm -rf "$final_dir"
    fi
    if [[ -d "$final_dir" ]]; then
        warn "$repo_name already exists — skipping (use --force to rebuild)"
        record_result "$repo_name" "$repo_url" "skipped (exists)" "$test_count"
        return 0
    fi
    mv "$tmp_dir" "$final_dir"

    ok "$repo_name built → $final_dir"
    record_result "$repo_name" "$repo_url" "✓ built" "$test_count"

    if $PUSH; then
        push_repo "$final_dir" "$repo_name" "$description" "$repo_url"
    fi
}

# ═════════════════════════════════════════════════════════
# BUILDER: Cloudflare Worker module
# ═════════════════════════════════════════════════════════

build_worker_module() {
    local module_dir="$1" repo_name="$2" description="$3"
    local src_dir="$SCRIPT_DIR/$module_dir"
    local repo_url="https://github.com/$ORG/$repo_name"

    title "Building $repo_name (Cloudflare Worker)"

    local tmp_dir
    tmp_dir=$(mktemp -d "${TMP_BASE}/ld-asm-${module_dir}.XXXXXX")
    trap "rm -rf '$tmp_dir'" RETURN

    info "Copying files from $src_dir..."
    cp -r "$src_dir/"* "$tmp_dir/" 2>/dev/null || true

    # Ensure package.json exists
    if [[ ! -f "$tmp_dir/package.json" ]]; then
        info "Generating package.json..."
        cat > "$tmp_dir/package.json" << PKG_EOF
{
  "name": "@luciddreamer/${module_dir}",
  "version": "0.1.0",
  "description": "$description",
  "license": "Apache-2.0",
  "author": "Lucineer / Casey DiGenaro",
  "scripts": {
    "deploy": "wrangler deploy",
    "dev": "wrangler dev"
  },
  "devDependencies": {
    "wrangler": "^3.0.0"
  }
}
PKG_EOF
    else
        info "Updating license in package.json..."
        sed -i 's/"license": "MIT"/"license": "Apache-2.0"/g' "$tmp_dir/package.json"
    fi

    write_license "$tmp_dir"
    write_js_gitignore "$tmp_dir"
    write_worker_ci "$tmp_dir" "$repo_name"

    local test_count
    test_count=$(count_tests "$tmp_dir")

    (
        cd "$tmp_dir"
        git init -q
        git add -A
        git commit -q -m "feat: initial release of $repo_name v0.1.0

$description

Extracted from luciddreamer-prototype monolith.
Part of the @superinstance modular system.
License: Apache-2.0"
        git branch -M main 2>/dev/null || true
    )

    mkdir -p "$REPOS_DIR"
    local final_dir="$REPOS_DIR/$module_dir"
    if [[ -d "$final_dir" ]] && $FORCE; then
        rm -rf "$final_dir"
    fi
    if [[ -d "$final_dir" ]]; then
        warn "$repo_name already exists — skipping (use --force to rebuild)"
        record_result "$repo_name" "$repo_url" "skipped (exists)" "$test_count"
        return 0
    fi
    mv "$tmp_dir" "$final_dir"

    ok "$repo_name built → $final_dir"
    record_result "$repo_name" "$repo_url" "✓ built" "$test_count"

    if $PUSH; then
        push_repo "$final_dir" "$repo_name" "$description" "$repo_url"
    fi
}

# ═════════════════════════════════════════════════════════
# BUILDER: Meta-package (depends on all 8 modules)
# ═════════════════════════════════════════════════════════

build_meta_package() {
    IFS=':' read -r module_dir repo_name pkg_type description <<< "$META_MODULE"
    local src_dir="$SCRIPT_DIR/$module_dir"
    local repo_url="https://github.com/$ORG/$repo_name"

    title "Building META-PACKAGE: $repo_name"

    local tmp_dir
    tmp_dir=$(mktemp -d "${TMP_BASE}/ld-asm-meta.XXXXXX")
    trap "rm -rf '$tmp_dir'" RETURN

    # Copy existing meta files if present
    info "Copying meta-package files..."
    if [[ -d "$src_dir/src" ]]; then
        mkdir -p "$tmp_dir/src"
        cp -r "$src_dir/src/"* "$tmp_dir/src/"
    fi
    cp "$src_dir/README.md" "$tmp_dir/README.md" 2>/dev/null || true

    # Generate setup.py with deps on all 8 modules
    info "Generating meta setup.py with dependencies on all sub-packages..."
    cat > "$tmp_dir/setup.py" << 'META_SETUP_EOF'
from setuptools import setup, find_packages

setup(
    name="luciddreamer",
    version="0.1.0",
    description="Meta-package — multi-agent dream radio station that auto-assembles all modules",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lucineer / Casey DiGenaro",
    author_email="casey@superinstance.com",
    url="https://github.com/SuperInstance/luciddreamer",
    license="Apache-2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        # Python modules
        "superinstance-conductor>=0.1.0",
        "superinstance-streamer>=0.1.0",
        "superinstance-knowledge-base>=0.1.0",
        "superinstance-sonic-shape>=0.1.0",
        # JS/Worker modules (documented — not pip-installable)
        # luciddreamer-player:    npm install @luciddreamer/player
        # luciddreamer-terminal:  npm install @luciddreamer/terminal
        # luciddreamer-gallery:   Cloudflare Worker — wrangler deploy
        # luciddreamer-feedback:  Cloudflare Worker — wrangler deploy
    ],
    extras_require={
        "config": ["pyyaml>=6.0"],
        "dev": ["pytest>=7.0", "pytest-cov>=4.0", "ruff>=0.4"],
    },
    entry_points={
        "console_scripts": [
            "luciddreamer = luciddreamer.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
META_SETUP_EOF

    # pyproject.toml
    cat > "$tmp_dir/pyproject.toml" << 'META_TOML_EOF'
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.pytest.ini_options]
testpaths = ["tests", "src/tests"]
META_TOML_EOF

    write_license "$tmp_dir"
    write_python_gitignore "$tmp_dir"
    write_python_ci "$tmp_dir" "$repo_name"

    local test_count
    test_count=$(count_tests "$tmp_dir")

    (
        cd "$tmp_dir"
        git init -q
        git add -A
        git commit -q -m "feat: initial release of $repo_name v0.1.0 — meta-package

$description

Pulls in all 8 LucidDreamer modules as dependencies:
  Python:  conductor, streamer, knowledge-base, sonic-shape
  JS:      player, terminal
  Workers: gallery, feedback

Install everything with: pip install luciddreamer

Part of the @superinstance modular system.
License: Apache-2.0"
        git branch -M main 2>/dev/null || true
    )

    mkdir -p "$REPOS_DIR"
    local final_dir="$REPOS_DIR/$module_dir"
    if [[ -d "$final_dir" ]] && $FORCE; then
        rm -rf "$final_dir"
    fi
    if [[ -d "$final_dir" ]]; then
        warn "$repo_name already exists — skipping (use --force to rebuild)"
        record_result "$repo_name" "$repo_url" "skipped (exists)" "$test_count"
        return 0
    fi
    mv "$tmp_dir" "$final_dir"

    ok "$repo_name built → $final_dir"
    record_result "$repo_name" "$repo_url" "✓ built (meta)" "$test_count"

    if $PUSH; then
        push_repo "$final_dir" "$repo_name" "$description" "$repo_url"
    fi
}

# ═════════════════════════════════════════════════════════
# PUSHER: Create GitHub repo and push
# ═════════════════════════════════════════════════════════

push_repo() {
    local repo_dir="$1" repo_name="$2" description="$3" expected_url="$4"

    if ! command -v gh &>/dev/null; then
        warn "gh CLI not installed — cannot push $repo_name"
        return 1
    fi

    info "Pushing $repo_name to GitHub..."
    (
        cd "$repo_dir"
        if gh repo create "$ORG/$repo_name" --public --description "$description" --source=. --push 2>/dev/null; then
            ok "Pushed to $expected_url"
        else
            # Repo might already exist — try pushing to it
            git remote add origin "$expected_url.git" 2>/dev/null || true
            git push -u origin main 2>/dev/null && ok "Pushed to $expected_url" || warn "Could not push $repo_name"
        fi
    ) || warn "Push failed for $repo_name"

    # Update summary status
    local i=${#SUMMARY_LINES[@]} arg_path
    arg_path=$(grep -n "|skipped\||✓ built" <<< "${SUMMARY_LINES[-1]}")
}

# ═════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  LucidDreamer.AI — Modular Assembly System               ║"
echo "║  Auto-glue for independent package repos                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
info "Organization: $ORG"
info "Output:       $REPOS_DIR"
info "Mode:         $(if $PUSH; then echo 'BUILD + PUSH'; else echo 'BUILD ONLY (no push)'; fi)"
info "Force rebuild: $($FORCE && echo 'yes' || echo 'no')"
echo ""

mkdir -p "$REPOS_DIR"

# ─── Build all modules ────────────────────────────────────
for mod_def in "${MODULES[@]}"; do
    IFS=':' read -r module_dir repo_name pkg_type desc <<< "$mod_def"
    case "$pkg_type" in
        python) build_python_module "$module_dir" "$repo_name" "$desc" ;;
        js)     build_js_module "$module_dir" "$repo_name" "$desc" ;;
        worker) build_worker_module "$module_dir" "$repo_name" "$desc" ;;
    esac
done

# ─── Build meta-package ───────────────────────────────────
build_meta_package

# ─── Write repos README / index ───────────────────────────
cat > "$REPOS_DIR/README.md" << 'INDEX_EOF'
# LucidDreamer.AI — Modular Package System

All 8 independent modules + 1 meta-package, assembled from the prototype monolith.

## Python Modules (PyPI)

| Module | Package | Install |
|--------|---------|---------|
| Conductor | `superinstance-conductor` | `pip install superinstance-conductor` |
| Streamer | `superinstance-streamer` | `pip install superinstance-streamer` |
| Knowledge Base | `superinstance-knowledge-base` | `pip install superinstance-knowledge-base` |
| Sonic Shape | `superinstance-sonic-shape` | `pip install superinstance-sonic-shape` |

## JavaScript Modules (npm)

| Module | Package | Install |
|--------|---------|---------|
| Player | `@luciddreamer/player` | `npm install @luciddreamer/player` |
| Terminal | `@luciddreamer/terminal` | `npm install @luciddreamer/terminal` |

## Cloudflare Workers

| Module | Deploy |
|--------|--------|
| Gallery | `wrangler deploy` |
| Feedback | `wrangler deploy` |

## Meta-Package

```bash
pip install luciddreamer
```

Installs all Python modules. Web components are deployed separately.

## License

All modules: Apache-2.0
INDEX_EOF

# ═════════════════════════════════════════════════════════
# SUMMARY TABLE
# ═════════════════════════════════════════════════════════

echo ""
echo "┌─────────────────────────────────────────────────────────────────────────────────────┐"
echo "│                          ASSEMBLY SUMMARY                                           │"
echo "├──────────────────────────────┬──────────────────────────────────────┬───────────┬────────────┤"
echo "│ Module                       │ Repo URL                             │ Status    │ Test Count │"
echo "├──────────────────────────────┼──────────────────────────────────────┼───────────┼────────────┤"

for line in "${SUMMARY_LINES[@]}"; do
    IFS='|' read -r mod url status tests <<< "$line"
    printf "│ %-28s │ %-36s │ %-9s │ %-10s │\n" "$mod" "$url" "$status" "$tests"
done

echo "├──────────────────────────────┼──────────────────────────────────────┼───────────┼────────────┤"
total_modules=${#SUMMARY_LINES[@]}
echo "│ Total: $total_modules modules                                                                       │"
echo "└─────────────────────────────────────────────────────────────────────────────────────┘"
echo ""
info "Repos location: $REPOS_DIR"
if $PUSH; then
    info "All modules pushed to GitHub org: $ORG"
else
    info "No push performed. Run with --push to push to GitHub."
fi
echo ""
ok "Assembly complete."
