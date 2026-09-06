import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"

LEADS_FILE = Path(__file__).parent / "leads.jsonl"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def push(text):
    """Send a Pushover notification. Returns True only if it actually went out."""
    if not pushover_user or not pushover_token:
        print("[push] Pushover credentials missing — skipping notification", flush=True)
        return False
    try:
        response = requests.post(
            pushover_url,
            data={"token": pushover_token, "user": pushover_user, "message": text},
            timeout=10,
        )
        if response.status_code != 200:
            print(f"[push] failed {response.status_code}: {response.text}", flush=True)
            return False
        return True
    except requests.RequestException as e:
        print(f"[push] request failed: {e}", flush=True)
        return False


def log_lead(kind, **fields):
    """Append to a local file first — a missed notification shouldn't lose the data."""
    record = {"kind": kind, "at": datetime.now(timezone.utc).isoformat(), **fields}
    try:
        with open(LEADS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as e:
        print(f"[log] could not write {LEADS_FILE}: {e}", flush=True)


def record_user_details(email=None, name="Name not provided", notes="not provided"):
    # The schema says email is required. The model ignores that sometimes.
    if not email:
        return (
            "No email address was provided. Ask the visitor for their email "
            "before calling this tool again."
        )

    email = email.strip()
    if not EMAIL_RE.match(email):
        return (
            f"'{email}' doesn't look like a valid email address. "
            "Ask the visitor to confirm it."
        )

    log_lead("user_details", email=email, name=name, notes=notes)
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "OK"


def record_unknown_question(question):
    log_lead("unknown_question", question=question)
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"


record_user_details_json = {
    "name": "record_user_details",
    "description": (
        "Record that a visitor is interested in getting in touch and has given "
        "their email address. Only call this once they have actually typed an "
        "email address — never invent one."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {
                "type": "string",
                "description": "Any additional info about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": (
        "Record any question you could not fully answer, including questions "
        "where you only gave a partial or hedged answer, or said you didn't "
        "have that detail."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

tool_map = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        print(f"Tool called: {tool_name}", flush=True)

        tool = tool_map.get(tool_name)
        if not tool:
            result = f"Unknown tool: {tool_name}"
        else:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = tool(**arguments)
            except Exception as e:
                # Bad arguments from the model must never take down the app.
                print(f"[tool error] {tool_name}: {type(e).__name__}: {e}", flush=True)
                result = f"Tool failed: {e}"

        results.append(
            {"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id}
        )
    return results