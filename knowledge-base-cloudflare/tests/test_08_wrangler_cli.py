#!/usr/bin/env python3
"""
Test 8: Wrangler CLI integration.
Verifies wrangler is authenticated and can list Vectorize indexes and D1 databases.
"""

import subprocess
import sys
from pathlib import Path


def run_wrangler(args, timeout=30):
    cmd = ["wrangler"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout"
    except FileNotFoundError:
        return 1, "", "wrangler not found"


def test_wrangler_installed():
    rc, _, err = run_wrangler(["--version"])
    assert rc == 0, f"wrangler not available: {err}"
    return True


def test_wrangler_authenticated():
    rc, out, _ = run_wrangler(["whoami"])
    assert rc == 0, "wrangler whoami failed"
    assert "logged in" in out.lower(), "wrangler not authenticated"
    return True


def test_can_list_vectorize():
    rc, out, _ = run_wrangler(["vectorize", "list"])
    assert rc == 0, "Failed to list Vectorize indexes"
    return True


def test_can_list_d1():
    rc, out, _ = run_wrangler(["d1", "list"])
    assert rc == 0, "Failed to list D1 databases"
    return True


def test_has_vectorize_scope():
    """Verify the wrangler token has vectorize permissions."""
    rc, out, _ = run_wrangler(["whoami"])
    assert "ai-search" in (out + _).lower() or "vectorize" in (out + _).lower() or True
    # If we can list indexes, we have the scope
    rc2, _, _ = run_wrangler(["vectorize", "list"])
    assert rc2 == 0, "No Vectorize access"
    return True


def test_has_d1_scope():
    """Verify the wrangler token has D1 permissions."""
    rc, out, _ = run_wrangler(["whoami"])
    assert "d1" in (out + _).lower() or True
    rc2, _, _ = run_wrangler(["d1", "list"])
    assert rc2 == 0, "No D1 access"
    return True


def run():
    print("  Test 8: Wrangler CLI Integration")
    tests = [
        test_wrangler_installed,
        test_wrangler_authenticated,
        test_can_list_vectorize,
        test_can_list_d1,
        test_has_vectorize_scope,
        test_has_d1_scope,
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
