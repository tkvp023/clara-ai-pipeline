"""
run_all.py - Run the full Clara Pipeline on all transcripts in the dataset.

Usage:
  python run_all.py

This script:
1. Runs Pipeline A on all demo transcripts
2. Runs Pipeline B on all onboarding transcripts (matched by index order)
3. Prints a full summary report
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from pipeline_a import run_pipeline_a
from pipeline_b import run_pipeline_b


def main():
    base = Path(__file__).parent

    demo_dir = base / "sample_transcripts" / "demo"
    onboarding_dir = base / "sample_transcripts" / "onboarding"

    demo_files = sorted(list(demo_dir.glob("*.txt")) + list(demo_dir.glob("*.md")))
    onboarding_files = sorted(list(onboarding_dir.glob("*.txt")) + list(onboarding_dir.glob("*.md")))

    print("\n" + "🚀 " * 20)
    print("  CLARA PIPELINE — FULL RUN")
    print("🚀 " * 20)
    print(f"\n  Found {len(demo_files)} demo transcript(s)")
    print(f"  Found {len(onboarding_files)} onboarding transcript(s)\n")

    # ---- PIPELINE A ----
    print("\n" + "="*60)
    print("  PHASE 1: PIPELINE A — Demo Calls → v1 Agents")
    print("="*60)

    a_results = []
    for i, f in enumerate(demo_files):
        print(f"\n  [{i+1}/{len(demo_files)}] Processing: {f.name}")
        try:
            result = run_pipeline_a(str(f))
            a_results.append({"file": f.name, "status": "✅", **result})
        except Exception as e:
            print(f"  ❌ Error: {e}")
            a_results.append({"file": f.name, "status": "❌", "error": str(e)})

    # ---- PIPELINE B ----
    print("\n" + "="*60)
    print("  PHASE 2: PIPELINE B — Onboarding Calls → v2 Agents")
    print("="*60)

    # Match onboarding files to their v1 accounts (by index)
    successful_accounts = [r for r in a_results if r["status"] == "✅"]
    b_results = []

    for i, f in enumerate(onboarding_files):
        if i >= len(successful_accounts):
            print(f"\n  ⚠️  No matching v1 account for {f.name}, skipping.")
            continue

        account_id = successful_accounts[i]["account_id"]
        print(f"\n  [{i+1}/{len(onboarding_files)}] Processing: {f.name} → {account_id}")
        try:
            result = run_pipeline_b(str(f), account_id)
            b_results.append({"file": f.name, "status": "✅", **result})
        except Exception as e:
            print(f"  ❌ Error: {e}")
            b_results.append({"file": f.name, "status": "❌", "error": str(e)})

    # ---- FINAL SUMMARY ----
    print("\n\n" + "="*60)
    print("  FINAL SUMMARY")
    print("="*60)

    print(f"\n  Pipeline A Results ({len(a_results)} files):")
    for r in a_results:
        print(f"    {r['status']} {r['file']} → {r.get('account_id', r.get('error',''))}")

    print(f"\n  Pipeline B Results ({len(b_results)} files):")
    for r in b_results:
        print(f"    {r['status']} {r['file']} → {r.get('account_id','')} ({r.get('changes',0)} changes) {r.get('error','')}")

    total = len(a_results) + len(b_results)
    success = sum(1 for r in a_results + b_results if r["status"] == "✅")
    print(f"\n  Total: {success}/{total} successful")
    print(f"\n  📁 All outputs saved to: outputs/accounts/")
    print(f"  📋 Changelogs saved to: changelog/\n")


if __name__ == "__main__":
    main()
