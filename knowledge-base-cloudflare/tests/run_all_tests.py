#!/usr/bin/env python3
"""
run_all_tests.py — Run all Semantic Bridge tests.

Runs all 10 test files in sequence and reports results.
"""

import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).parent


def main():
    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    total = len(test_files)
    passed = 0
    failed = 0
    start = time.time()

    print()
    print("━" * 60)
    print("  🧪 Semantic Bridge — Test Suite")
    print(f"  Running {total} test files...")
    print("━" * 60)

    for test_file in test_files:
        # Import and run
        module_name = test_file.stem
        print(f"\n  Running {module_name}...")

        # Use subprocess for isolation
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True, text=True, timeout=60
        )

        # Print output
        if result.stdout:
            print(result.stdout.rstrip())

        if result.returncode == 0:
            passed += 1
        else:
            failed += 1
            if result.stderr:
                print(f"    STDERR: {result.stderr[:300]}")

    elapsed = time.time() - start
    print()
    print("━" * 60)
    print(f"  Results: {passed}/{total} passed, {failed} failed ({elapsed:.1f}s)")
    if failed == 0:
        print("  ✅ All tests passed!")
    else:
        print(f"  ❌ {failed} test(s) failed")
    print("━" * 60)
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
