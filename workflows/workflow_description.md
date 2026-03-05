# Clara Pipeline — Workflow Architecture

## Overview

Since we're running on a low-resource machine, this pipeline is implemented as Python scripts rather than n8n. The architecture mirrors what an n8n workflow would do, making it easy to migrate later.

## Data Flow Diagram

```
PIPELINE A (Demo Call → v1)
─────────────────────────────────────────────────────
  [INPUT]                [PROCESS]              [OUTPUT]
  demo_001.txt  ──▶  load_transcript()
                    ──▶  extract_from_demo()     account_memo.json (v1)
                         (Groq LLM)        ──▶  agent_spec.json (v1)
                    ──▶  generate_agent_spec()   tracker.json
                    ──▶  save_outputs()
                    ──▶  log_to_tracker()


PIPELINE B (Onboarding → v2)
─────────────────────────────────────────────────────
  [INPUT]                [PROCESS]              [OUTPUT]
  onboarding_001.txt ──▶ load_transcript()
  account_memo (v1)  ──▶ extract_from_onboarding()
                         (Groq LLM)        ──▶  account_memo.json (v2)
                    ──▶  generate_agent_spec()   agent_spec.json (v2)
                    ──▶  build_changelog()        changelog.json
                    ──▶  save_outputs()
```

## Equivalent n8n Node Mapping

| Script Function          | n8n Node Equivalent              |
|--------------------------|----------------------------------|
| `load_transcript()`      | Read Binary File node            |
| `extract_from_demo()`    | HTTP Request → Groq API          |
| `parse_llm_json()`       | JSON Parse / Function node       |
| `generate_agent_spec()`  | Function node (template engine)  |
| `save_json()`            | Write Binary File / Supabase     |
| `log_to_tracker()`       | Google Sheets / Airtable node    |

## How to Migrate to n8n (Future)

1. Install n8n: `docker run -p 5678:5678 n8nio/n8n`
2. Create a workflow with:
   - Trigger: Webhook (receive transcript file)
   - Node 1: HTTP Request to Groq API (extraction prompt)
   - Node 2: Function node (parse JSON, generate agent spec)
   - Node 3: Write to Supabase or GitHub
   - Node 4: Write to Google Sheets (tracker)
3. For Pipeline B: Add a "load v1 memo" step before the LLM call

## LLM Prompt Strategy

- Temperature: 0.1 (deterministic, factual extraction)
- Model: llama3-70b-8192 (best free model on Groq)
- Retry: If JSON parse fails, retry once with stricter prompt
- Hallucination prevention: Explicit "leave null if missing" instruction
