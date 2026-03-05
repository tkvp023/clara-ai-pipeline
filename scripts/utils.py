"""
utils.py - Shared utility functions for Clara Pipeline
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path


def load_transcript(file_path: str) -> str:
    """Load transcript text from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_account_output_dir(account_id: str, version: str = "v1") -> Path:
    """Return and create the output directory for an account version."""
    base = Path(__file__).parent.parent / "outputs" / "accounts" / account_id / version
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_json(data: dict, path: Path, filename: str) -> Path:
    """Save a dict as a formatted JSON file."""
    filepath = path / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  ✅ Saved: {filepath}")
    return filepath


def load_json(path: Path, filename: str) -> dict:
    """Load a JSON file into a dict."""
    filepath = path / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_llm_json(raw: str) -> dict:
    """
    Safely parse JSON from an LLM response.
    Handles markdown code blocks and extra text.
    """
    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    # Find the first { and last } to extract JSON object
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in LLM response:\n{raw}")
    return json.loads(clean[start:end])


def generate_account_id(company_name: str) -> str:
    """Generate a URL-safe account ID from a company name."""
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    return f"{slug}-001"


def timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def print_section(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
