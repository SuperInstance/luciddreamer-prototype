"""python -m arena_proofs -> regenerate PROOF-REPORT.md"""

from .report import REPORT_PATH, generate_report

if __name__ == "__main__":
    generate_report()
    print(f"wrote {REPORT_PATH}")
