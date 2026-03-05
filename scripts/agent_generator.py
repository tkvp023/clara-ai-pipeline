"""
agent_generator.py - Generate Retell Agent Spec from structured account memo
"""

from utils import timestamp


def generate_system_prompt(memo: dict) -> str:
    """Build the AI phone agent system prompt from account memo fields."""

    company = memo.get("company_name", "the company")
    hours = memo.get("business_hours", {})
    biz_hours_str = f"{hours.get('days','Mon-Fri')} {hours.get('start','8:00 AM')} - {hours.get('end','6:00 PM')} {hours.get('timezone','')}"
    sat = hours.get("saturday")
    sun = hours.get("sunday")
    if sat:
        biz_hours_str += f", Saturday {sat}"
    if sun:
        biz_hours_str += f", Sunday {sun}"

    address = memo.get("office_address", "our office")
    services = ", ".join(memo.get("services_supported", []))

    # Emergency routing
    routing = memo.get("emergency_routing_rules", {})
    primary = routing.get("primary", {})
    secondary = routing.get("secondary", {})
    tertiary = routing.get("tertiary", {})
    fallback = routing.get("fallback_action", "take a message and ensure a callback within 30 minutes")

    emergency_def = memo.get("emergency_definition", [])
    emergency_list = "\n".join(f"  - {e}" for e in emergency_def) if emergency_def else "  - Situations requiring immediate response"

    non_emergency = memo.get("non_emergency_routing_rules", "Take a message and call back next business day.")
    transfer_rules = memo.get("call_transfer_rules", {})
    fail_action = transfer_rules.get("fail_action", "Apologize, take a message, and assure a callback.")

    special = memo.get("special_instructions", [])
    special_str = "\n".join(f"- {s}" for s in special) if special else ""

    prompt = f"""You are a professional AI phone receptionist for {company}.

## YOUR IDENTITY
- You are a friendly, professional phone agent for {company}.
- You handle incoming calls for scheduling, emergencies, and general inquiries.
- NEVER mention that you are an AI or that you are making "function calls". Speak naturally.
- NEVER promise same-day service unless it is a confirmed emergency.
- ALWAYS collect the caller's name and callback number before ending the call.

## BUSINESS INFORMATION
- Company: {company}
- Address: {address}
- Services: {services}
- Business Hours: {biz_hours_str}

## DURING BUSINESS HOURS FLOW
1. Greet: Answer warmly, state the company name, ask how you can help.
2. Collect name: "May I get your name please?"
3. Understand the issue: Listen, ask clarifying questions only if needed.
4. Check maintenance agreement (if applicable): "Are you currently on one of our maintenance agreements?"
5. Collect callback number: "And the best number to reach you?"
6. Attempt transfer: Transfer the call to the appropriate team member.
7. If transfer fails: Apologize and say: "{fail_action}"
8. Confirm next steps: Tell the caller what to expect.
9. Ask: "Is there anything else I can help you with?"
10. Close warmly.

## AFTER HOURS FLOW
1. Greet: State the company name and that the office is currently closed.
2. Ask purpose: "Are you calling about an emergency or a general inquiry?"

### If EMERGENCY:
Emergencies are defined as:
{emergency_list}

3. Confirm emergency type, collect: Full name, callback number, and service address.
4. Attempt transfer to on-call technician (do NOT say you are transferring to a specific person by name).
   - First attempt: on-call primary
   - Second attempt: on-call secondary
   - Third attempt: {tertiary.get('name','emergency answering service') if tertiary else 'emergency answering service'}
5. If all transfers fail: "{fallback}"
6. Assure caller: "Our on-call team will reach you within 30 minutes."
7. Ask: "Is there anything else I can help you with?"
8. Close warmly.

### If NON-EMERGENCY after hours:
{non_emergency}

## SPECIAL INSTRUCTIONS
{special_str if special_str else "- Follow standard call protocol."}

## CONSTRAINTS
- Do NOT mention tool names, transfer mechanisms, or internal processes to callers.
- Do NOT collect more information than needed for routing and dispatch.
- Do NOT ask more than 2-3 questions before attempting to help or transfer.
- Always be calm, empathetic, and professional.
"""
    return prompt.strip()


def generate_agent_spec(memo: dict) -> dict:
    """Generate a complete Retell Agent Draft Spec from the account memo."""

    version = memo.get("version", "v1")
    company = memo.get("company_name", "Unknown Company")
    hours = memo.get("business_hours", {})
    routing = memo.get("emergency_routing_rules", {})
    transfer_rules = memo.get("call_transfer_rules", {})

    system_prompt = generate_system_prompt(memo)

    spec = {
        "agent_name": f"{company} AI Receptionist",
        "version": version,
        "generated_at": timestamp(),
        "voice_style": {
            "gender": "female",
            "tone": "professional and warm",
            "speed": "normal",
            "notes": "Should sound calm and helpful. Not robotic."
        },
        "system_prompt": system_prompt,
        "key_variables": {
            "company_name": company,
            "timezone": hours.get("timezone", ""),
            "business_hours": {
                "weekdays": f"{hours.get('days','')} {hours.get('start','')} - {hours.get('end','')}",
                "saturday": hours.get("saturday"),
                "sunday": hours.get("sunday")
            },
            "office_address": memo.get("office_address"),
            "emergency_contacts": {
                "primary": routing.get("primary"),
                "secondary": routing.get("secondary"),
                "tertiary": routing.get("tertiary")
            }
        },
        "tool_invocation_placeholders": [
            {
                "name": "transfer_call",
                "description": "Transfer the call to an on-call technician or team member",
                "trigger": "When caller needs to be routed to a human",
                "note": "Never mention this tool to the caller"
            },
            {
                "name": "create_job_ticket",
                "description": "Create a service job in the job management system",
                "trigger": "When a new service request is confirmed",
                "note": "Never mention this tool to the caller"
            },
            {
                "name": "check_maintenance_agreement",
                "description": "Check if a customer has an active maintenance agreement",
                "trigger": "During business hours when caller identity is established",
                "note": "Never mention this tool to the caller"
            }
        ],
        "call_transfer_protocol": {
            "wait_before_transfer_seconds": transfer_rules.get("wait_seconds", 30),
            "max_retries": transfer_rules.get("retries", 2),
            "transfer_order": [
                routing.get("primary", {}),
                routing.get("secondary", {}),
                routing.get("tertiary", {})
            ],
            "on_transfer_fail": transfer_rules.get("fail_action", "Apologize, take a message, assure callback.")
        },
        "fallback_protocol": {
            "action": "Take message",
            "fields_to_collect": ["full_name", "callback_number", "issue_description", "service_address"],
            "promise": "Assure caller of callback within 30 minutes for emergencies, next business day for non-emergencies."
        },
        "retell_import_instructions": {
            "step_1": "Log in to app.retellai.com",
            "step_2": "Go to Agents > Create Agent",
            "step_3": "Paste the system_prompt field above into the System Prompt box",
            "step_4": "Set voice settings to match voice_style above",
            "step_5": "Add transfer tool with numbers from call_transfer_protocol",
            "step_6": "Save and test with a call"
        }
    }

    return spec
