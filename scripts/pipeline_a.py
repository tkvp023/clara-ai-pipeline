"""
pipeline_a.py - Demo Call → Preliminary Agent (v1)

Usage:
  python pipeline_a.py <path_to_transcript>
  python pipeline_a.py --batch   (processes all files in sample_transcripts/demo/)
"""

import sys
import os
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_transcript, get_account_output_dir, save_json, print_section
from extractor import extract_from_demo
from agent_generator import generate_agent_spec
from tracker import log_to_sheets


def run_pipeline_a(transcript_path: str) -> dict:
    """
    Run Pipeline A on a single demo transcript.
    Returns dict with account_id and output paths.
    """
    print_section(f"PIPELINE A — Demo Call Processing")
    print(f"  📄 Transcript: {transcript_path}")

    # Step 1: Load transcript
    transcript = load_transcript(transcript_path)
    print(f"  📖 Loaded transcript ({len(transcript)} chars)")

    # Step 2: Extract structured memo via LLM
    print("\n  [Step 2] Extracting account memo...")
    memo = extract_from_demo(transcript)
    account_id = memo.get("account_id", "unknown-account")
    print(f"  🏢 Account ID: {account_id}")

    # Step 3: Generate Retell agent spec
    print("\n  [Step 3] Generating Retell agent spec...")
    agent_spec = generate_agent_spec(memo)
    print(f"  🤖 Agent spec generated for: {memo.get('company_name')}")

    # Step 4: Save outputs
    print("\n  [Step 4] Saving outputs...")
    out_dir = get_account_output_dir(account_id, "v1")
    save_json(memo, out_dir, "account_memo.json")
    save_json(agent_spec, out_dir, "agent_spec.json")

    # Step 5: Save tracker entry
    tracker = {
        "account_id": account_id,
        "company_name": memo.get("company_name"),
        "status": "v1_complete",
        "transcript_source": str(transcript_path),
        "output_dir": str(out_dir),
        "created_at": memo.get("extracted_at")
    }
    save_json(tracker, out_dir, "tracker.json")

    # Log to Google Sheets (or local fallback)
    log_to_sheets(
        account_id=account_id,
        company_name=memo.get("company_name", ""),
        pipeline="A", version="v1", status="complete",
        transcript_file=str(transcript_path),
        output_dir=str(out_dir)
    )

    print(f"\n  ✅ Pipeline A complete for: {account_id}")
    print(f"  📁 Outputs: {out_dir}")

    return {"account_id": account_id, "output_dir": str(out_dir), "memo": memo}


def run_batch():
    """Process all demo transcripts in the sample_transcripts/demo/ folder."""
    demo_dir = Path(__file__).parent.parent / "sample_transcripts" / "demo"
    transcripts = list(demo_dir.glob("*.txt")) + list(demo_dir.glob("*.md"))

    if not transcripts:
        print("❌ No transcript files found in sample_transcripts/demo/")
        print("   Add .txt or .md files and try again.")
        return

    print(f"\n🚀 Batch mode: Found {len(transcripts)} demo transcript(s)")
    results = []

    for t in transcripts:
        try:
            result = run_pipeline_a(str(t))
            results.append({"file": t.name, "status": "success", **result})
        except Exception as e:
            print(f"  ❌ Failed on {t.name}: {e}")
            results.append({"file": t.name, "status": "failed", "error": str(e)})

    print("\n" + "="*50)
    print("  BATCH SUMMARY")
    print("="*50)
    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"  {status_icon} {r['file']} → {r.get('account_id', 'N/A')}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--batch":
        run_batch()
    else:
        run_pipeline_a(sys.argv[1])
