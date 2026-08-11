#!/usr/bin/env python3
"""
Test 10: Deploy script structure.
Verifies the deploy.sh script and all components are in place.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent


def test_deploy_script_exists():
    path = SCRIPT_DIR / "deploy.sh"
    assert path.exists(), f"deploy.sh not found at {path}"
    return True


def test_deploy_script_executable():
    path = SCRIPT_DIR / "deploy.sh"
    assert path.exists(), "deploy.sh not found"
    # Check if file has execute permission (simplified check)
    import os
    mode = os.stat(path).st_mode
    assert mode & 0o111, f"deploy.sh not executable (mode: {oct(mode)})"
    return True


def test_deploy_script_has_steps():
    """Verify deploy.sh contains all 5 deployment steps."""
    path = SCRIPT_DIR / "deploy.sh"
    content = path.read_text()
    expected_steps = [
        "Vectorize Index",
        "D1 Database",
        "D1 Migrations",
        "Vectorize Ideas",
        "Verify",
    ]
    for step in expected_steps:
        assert step in content, f"Missing step in deploy.sh: {step}"
    return True


def test_all_components_exist():
    """Verify all required files exist."""
    required = [
        "vectorize_ideas.py",
        "query_cloudflare.py",
        "d1_sync.py",
        "deploy.sh",
        "README.md",
    ]
    for f in required:
        path = SCRIPT_DIR / f
        assert path.exists(), f"Missing: {f}"
    return True


def test_migrations_dir_exists():
    """Verify migrations directory exists for generated SQL."""
    path = SCRIPT_DIR / "migrations"
    assert path.is_dir(), f"migrations dir not found at {path}"
    return True


def test_tests_count():
    """Verify there are at least 10 test files."""
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    assert len(test_files) >= 10, f"Expected ≥10 test files, found {len(test_files)}"
    return True


def run():
    print("  Test 10: Deploy Structure")
    tests = [
        test_deploy_script_exists,
        test_deploy_script_executable,
        test_deploy_script_has_steps,
        test_all_components_exist,
        test_migrations_dir_exists,
        test_tests_count,
    ]
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"    ✓ {name}")
        except (AssertionError, Exception) as e:
            print(f"    ✗ {name}: {e}")
            return False
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
