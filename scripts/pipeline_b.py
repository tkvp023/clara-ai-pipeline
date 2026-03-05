"""
pipeline_b.py - Onboarding Call → Updated Agent (v2)

Usage:
  python pipeline_b.py <path_to_onboarding_transcript> <account_id>
  python pipeline_b.py --batch   (processes all files in sample_transcripts/onboarding/)
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import load_transcript, get_account_output_dir, load_json, save_json, timestamp, print_section
from extractor import extract_from_onboarding
from agent_generator import generate_agent_spec
from tracker import log_to_sheets


def run_pipeline_b(transcript_path: str, account_id: str = None) -> dict:
    """
    Run Pipeline B on a single onboarding transcript.
    account_id: if None, tries to detect from transcript filename or v1 directory.
    """
    print_section(f"PIPELINE B — Onboarding Update Processing")
    print(f"  📄 Transcript: {transcript_path}")

    # Step 1: Load transcript
    transcript = load_transcript(transcript_path)
    print(f"  📖 Loaded transcript ({len(transcript)} chars)")

    # Step 2: Find matching v1 account
    if not account_id:
        account_id = _detect_account_id(transcript_path, transcript)

    print(f"  🔍 Account ID: {account_id}")
    v1_dir = get_account_output_dir(account_id, "v1")
    memo_path = v1_dir / "account_memo.json"

    if not memo_path.exists():
        raise FileNotFoundError(
            f"No v1 memo found at {memo_path}.\n"
            f"Run Pipeline A first for account: {account_id}"
        )

    existing_memo = load_json(v1_dir, "account_memo.json")
    print(f"  📂 Loaded v1 memo for: {existing_memo.get('company_name')}")

    # Step 3: Extract updates and merge
    print("\n  [Step 3] Extracting updates from onboarding transcript...")
    updated_memo, changelog = extract_from_onboarding(transcript, existing_memo)

    # Step 4: Generate v2 agent spec
    print("\n  [Step 4] Generating updated Retell agent spec (v2)...")
    agent_spec_v2 = generate_agent_spec(updated_memo)

    # Step 5: Build changelog document
    changelog_doc = {
        "account_id": account_id,
        "company_name": updated_memo.get("company_name"),
        "from_version": "v1",
        "to_version": "v2",
        "updated_at": timestamp(),
        "changes": changelog,
        "total_changes": len(changelog)
    }

    # Step 6: Save outputs
    print("\n  [Step 5] Saving v2 outputs...")
    v2_dir = get_account_output_dir(account_id, "v2")
    save_json(updated_memo, v2_dir, "account_memo.json")
    save_json(agent_spec_v2, v2_dir, "agent_spec.json")
    save_json(changelog_doc, v2_dir, "changelog.json")

    # Also save changelog to root changelog folder
    changelog_root = Path(__file__).parent.parent / "changelog"
    changelog_root.mkdir(exist_ok=True)
    save_json(changelog_doc, changelog_root, f"{account_id}_changes.json")

    # Print changelog summary
    print(f"\n  📝 Changes detected ({len(changelog)} total):")
    for change in changelog:
        print(f"     • {change.get('field')}: {change.get('reason','')}")

    # Log to Google Sheets (or local fallback)
    log_to_sheets(
        account_id=account_id,
        company_name=updated_memo.get("company_name", ""),
        pipeline="B", version="v2", status="complete",
        changes=len(changelog), output_dir=str(v2_dir)
    )

    print(f"\n  ✅ Pipeline B complete for: {account_id}")
    print(f"  📁 Outputs: {v2_dir}")

    return {
        "account_id": account_id,
        "output_dir": str(v2_dir),
        "changes": len(changelog),
        "updated_memo": updated_memo
    }


def _detect_account_id(transcript_path: str, transcript: str) -> str:
    """Try to detect account_id from filename or find matching v1 directory."""
    # Check for matching v1 directories
    outputs_dir = Path(__file__).parent.parent / "outputs" / "accounts"
    if outputs_dir.exists():
        accounts = [d.name for d in outputs_dir.iterdir() if d.is_dir()]
        if len(accounts) == 1:
            print(f"  🔍 Auto-detected account: {accounts[0]}")
            return accounts[0]

    # Try to extract from filename: onboarding_001 → look for demo_001 match
    raise ValueError(
        "Could not auto-detect account_id.\n"
        "Run with: python pipeline_b.py <transcript> <account_id>"
    )


def run_batch():
    """Process all onboarding transcripts, matching them to existing v1 accounts."""
    onboarding_dir = Path(__file__).parent.parent / "sample_transcripts" / "onboarding"
    transcripts = list(onboarding_dir.glob("*.txt")) + list(onboarding_dir.glob("*.md"))

    outputs_dir = Path(__file__).parent.parent / "outputs" / "accounts"

    if not transcripts:
        print("❌ No onboarding transcript files found.")
        return

    # Get all v1 account IDs
    v1_accounts = []
    if outputs_dir.exists():
        v1_accounts = [d.name for d in outputs_dir.iterdir() if (d / "v1").exists()]

    if not v1_accounts:
        print("❌ No v1 accounts found. Run Pipeline A first.")
        return

    print(f"\n🚀 Batch mode: {len(transcripts)} onboarding transcript(s), {len(v1_accounts)} v1 account(s)")

    results = []
    for i, (t, acc) in enumerate(zip(sorted(transcripts), sorted(v1_accounts))):
        print(f"\n  [{i+1}/{len(transcripts)}] Matching {t.name} → {acc}")
        try:
            result = run_pipeline_b(str(t), acc)
            results.append({"file": t.name, "status": "success", **result})
        except Exception as e:
            print(f"  ❌ Failed on {t.name}: {e}")
            results.append({"file": t.name, "status": "failed", "error": str(e)})

    print("\n" + "="*50)
    print("  BATCH SUMMARY")
    print("="*50)
    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"  {status_icon} {r['file']} → {r.get('account_id','N/A')} ({r.get('changes',0)} changes)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--batch":
        run_batch()
    elif len(sys.argv) == 3:
        run_pipeline_b(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        run_pipeline_b(sys.argv[1])
    else:
        print("Usage: python pipeline_b.py <transcript> [account_id]")
        print("       python pipeline_b.py --batch")
