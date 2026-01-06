"""State persistence tools for the agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from strands import tool

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data"
STATE_DIR = DATA_DIR / "state"
CONTEXT_FILE = STATE_DIR / "context.json"
INTERACTIONS_FILE = STATE_DIR / "interactions.json"


def _ensure_dirs():
    """Ensure state directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    """Load JSON file, return empty dict if not exists."""
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_json(path: Path, data: dict):
    """Save data to JSON file."""
    _ensure_dirs()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@tool
def save_user_context(key: str, value: str) -> str:
    """
    Save user context like life events, preferences, or outreach reasons.

    Args:
        key: The context key (e.g., "tone", "current_job", "recent_move")
        value: The context value

    Returns:
        Confirmation message
    """
    context = _load_json(CONTEXT_FILE)

    # Handle special keys
    if key == "life_event":
        if "life_events" not in context:
            context["life_events"] = []
        context["life_events"].append({
            "date": datetime.now().strftime("%Y-%m"),
            "event": value,
        })
    elif key.startswith("preference_"):
        if "preferences" not in context:
            context["preferences"] = {}
        pref_key = key.replace("preference_", "")
        context["preferences"][pref_key] = value
    else:
        context[key] = value

    _save_json(CONTEXT_FILE, context)
    return f"Saved context: {key} = {value}"


@tool
def get_user_context(key: Optional[str] = None) -> str:
    """
    Retrieve saved user context.

    Args:
        key: Specific key to retrieve, or None to get all context

    Returns:
        The context value(s) as a formatted string
    """
    context = _load_json(CONTEXT_FILE)

    if key is None:
        if not context:
            return "No user context saved yet."
        return json.dumps(context, indent=2)

    if key == "life_events":
        events = context.get("life_events", [])
        if not events:
            return "No life events recorded."
        return "\n".join([f"- {e['date']}: {e['event']}" for e in events])

    if key.startswith("preference_"):
        pref_key = key.replace("preference_", "")
        prefs = context.get("preferences", {})
        return prefs.get(pref_key, f"No preference set for: {pref_key}")

    return context.get(key, f"No context found for key: {key}")


@tool
def log_interaction(
    contact_identifier: str,
    event_id: str,
    action: str,
    notes: Optional[str] = None,
) -> str:
    """
    Log an interaction with a contact for a specific event.

    Args:
        contact_identifier: Email or name of the contact
        event_id: The event identifier (e.g., "newyear-2025")
        action: The action taken (e.g., "engaged", "skipped", "message_sent")
        notes: Optional notes about the interaction

    Returns:
        Confirmation message
    """
    interactions = _load_json(INTERACTIONS_FILE)

    # Normalize contact identifier
    contact_key = contact_identifier.lower().replace(" ", "_")

    if contact_key not in interactions:
        interactions[contact_key] = {"events": {}, "cleanup": {}}

    if event_id not in interactions[contact_key]["events"]:
        interactions[contact_key]["events"][event_id] = {}

    event_data = interactions[contact_key]["events"][event_id]
    event_data["status"] = action
    event_data["updated_at"] = datetime.now().isoformat()

    if notes:
        event_data["notes"] = notes

    if action == "message_sent":
        event_data["message_sent"] = True

    _save_json(INTERACTIONS_FILE, interactions)
    return f"Logged {action} for {contact_identifier} in event {event_id}"


@tool
def log_cleanup(contact_identifier: str, notes: str) -> str:
    """
    Log cleanup/review notes for a contact.

    Args:
        contact_identifier: Email or name of the contact
        notes: Notes from the cleanup review

    Returns:
        Confirmation message
    """
    interactions = _load_json(INTERACTIONS_FILE)

    contact_key = contact_identifier.lower().replace(" ", "_")

    if contact_key not in interactions:
        interactions[contact_key] = {"events": {}, "cleanup": {}}

    interactions[contact_key]["cleanup"] = {
        "last_reviewed": datetime.now().isoformat(),
        "notes": notes,
    }

    _save_json(INTERACTIONS_FILE, interactions)
    return f"Logged cleanup notes for {contact_identifier}"


@tool
def get_contact_history(contact_identifier: str) -> str:
    """
    Get all past interactions and cleanup notes for a contact.

    Args:
        contact_identifier: Email or name of the contact

    Returns:
        Formatted history of interactions
    """
    interactions = _load_json(INTERACTIONS_FILE)

    contact_key = contact_identifier.lower().replace(" ", "_")
    history = interactions.get(contact_key)

    if not history:
        return f"No history found for {contact_identifier}"

    result = []

    # Add cleanup info
    cleanup = history.get("cleanup", {})
    if cleanup:
        result.append(f"Last reviewed: {cleanup.get('last_reviewed', 'Unknown')}")
        if cleanup.get("notes"):
            result.append(f"Cleanup notes: {cleanup['notes']}")

    # Add event interactions
    events = history.get("events", {})
    if events:
        result.append("\nEvent interactions:")
        for event_id, data in events.items():
            status = data.get("status", "unknown")
            notes = data.get("notes", "")
            result.append(f"  - {event_id}: {status}" + (f" ({notes})" if notes else ""))

    return "\n".join(result) if result else f"No history for {contact_identifier}"


@tool
def get_contacts_for_event(event_id: str, status: Optional[str] = None) -> list[dict]:
    """
    Get all contacts that have been processed for a specific event.

    Args:
        event_id: The event identifier
        status: Optional filter by status (e.g., "engaged", "skipped")

    Returns:
        List of contacts with their event status
    """
    interactions = _load_json(INTERACTIONS_FILE)

    results = []
    for contact_key, data in interactions.items():
        events = data.get("events", {})
        if event_id in events:
            event_data = events[event_id]
            if status is None or event_data.get("status") == status:
                results.append({
                    "contact": contact_key,
                    "status": event_data.get("status"),
                    "notes": event_data.get("notes"),
                    "message_sent": event_data.get("message_sent", False),
                })

    return results


# Export all tools
ALL_TOOLS = [
    save_user_context,
    get_user_context,
    log_interaction,
    log_cleanup,
    get_contact_history,
    get_contacts_for_event,
]
