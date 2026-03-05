"""
extractor.py - Extract structured account memo from transcript using Groq LLM
"""

import os
from groq import Groq
from dotenv import load_dotenv
from utils import parse_llm_json, timestamp

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

EXTRACTION_PROMPT = """
You are a precise data extraction assistant for Clara AI, a company that builds AI phone agents for HVAC, plumbing, and similar service businesses.

Your task: Extract structured information from the call transcript below and return ONLY a valid JSON object. Do NOT invent or hallucinate any data. If a field is not mentioned, leave it as null or an empty list.

Required JSON structure:
{
  "account_id": "<slug derived from company name, e.g. greenfield-hvac-001>",
  "company_name": "<full company name>",
  "business_hours": {
    "days": "<e.g. Monday-Friday>",
    "start": "<e.g. 8:00 AM>",
    "end": "<e.g. 6:00 PM>",
    "timezone": "<e.g. Central Time>",
    "saturday": "<hours or null>",
    "sunday": "<hours or null>"
  },
  "office_address": "<full address or null>",
  "services_supported": ["<service1>", "<service2>"],
  "emergency_definition": ["<trigger1>", "<trigger2>"],
  "emergency_routing_rules": {
    "primary": {"name": "<name>", "phone": "<phone>"},
    "secondary": {"name": "<name>", "phone": "<phone>"},
    "tertiary": {"name": "<name or service>", "phone": "<phone>"},
    "fallback_action": "<what to do if all contacts fail>"
  },
  "non_emergency_routing_rules": "<description of what happens to non-emergency after-hours calls>",
  "call_transfer_rules": {
    "wait_seconds": <number or null>,
    "retries": <number or null>,
    "fail_action": "<what to say/do if transfer fails>"
  },
  "integration_constraints": ["<constraint1>", "<constraint2>"],
  "after_hours_flow_summary": "<2-3 sentence summary of after-hours call flow>",
  "office_hours_flow_summary": "<2-3 sentence summary of business-hours call flow>",
  "special_instructions": ["<any extra rules mentioned>"],
  "questions_or_unknowns": ["<anything unclear or missing>"],
  "notes": "<short freeform notes>",
  "extracted_at": "<ISO timestamp>"
}

TRANSCRIPT:
{transcript}

Return ONLY the JSON. No explanation, no markdown, no preamble.
"""

UPDATE_PROMPT = """
You are a precise data extraction assistant for Clara AI.

Below is an EXISTING account memo (v1) and a NEW onboarding call transcript.

Your task:
1. Extract any NEW or CHANGED information from the onboarding transcript.
2. Merge it into the existing memo to produce an updated v2 memo.
3. Also produce a changelog listing what changed and why.
4. Do NOT invent data. If something is not mentioned, keep the existing value.

Return ONLY a valid JSON object in this exact format:
{
  "updated_memo": { ...full updated account memo with same structure as v1... },
  "changelog": [
    {
      "field": "<field name>",
      "old_value": "<previous value>",
      "new_value": "<updated value>",
      "reason": "<why it changed based on transcript>"
    }
  ]
}

EXISTING V1 MEMO:
{existing_memo}

ONBOARDING TRANSCRIPT:
{transcript}

Return ONLY the JSON. No explanation, no markdown, no preamble.
"""


def extract_from_demo(transcript: str) -> dict:
    """Extract structured account memo from a demo call transcript."""
    print("  🤖 Calling Groq LLM for extraction...")

    prompt = EXTRACTION_PROMPT.replace("{transcript}", transcript)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content
    memo = parse_llm_json(raw)
    memo["extracted_at"] = timestamp()
    memo["version"] = "v1"
    return memo


def extract_from_onboarding(transcript: str, existing_memo: dict) -> tuple[dict, list]:
    """
    Extract updates from onboarding transcript and merge with existing memo.
    Returns (updated_memo, changelog)
    """
    import json

    print("  🤖 Calling Groq LLM for onboarding update extraction...")

    prompt = UPDATE_PROMPT\
        .replace("{existing_memo}", json.dumps(existing_memo, indent=2))\
        .replace("{transcript}", transcript)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content
    result = parse_llm_json(raw)

    updated_memo = result.get("updated_memo", {})
    changelog = result.get("changelog", [])

    updated_memo["version"] = "v2"
    updated_memo["updated_at"] = timestamp()

    return updated_memo, changelog
