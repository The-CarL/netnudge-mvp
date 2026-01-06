"""Message output tools for the agent."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from strands import tool

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data"
MESSAGES_DIR = DATA_DIR / "messages"


def _ensure_dirs(event_id: str):
    """Ensure message directories exist for an event."""
    event_dir = MESSAGES_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    return event_dir


def _sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    # Replace spaces with underscores, remove special chars
    safe = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"\s+", "_", safe).strip("_")


@tool
def save_message(
    event_id: str,
    contact_name: str,
    contact_email: Optional[str],
    contact_phone: Optional[str],
    message: str,
    channel: str,
) -> str:
    """
    Save a generated outreach message to the messages folder.

    Args:
        event_id: The event identifier (e.g., "newyear-2025")
        contact_name: The contact's full name
        contact_email: The contact's email address (optional)
        contact_phone: The contact's phone number (optional)
        message: The generated message content
        channel: The outreach channel (SMS, LinkedIn, Email)

    Returns:
        Confirmation message with file path
    """
    event_dir = _ensure_dirs(event_id)

    # Create safe filename from contact name
    filename = _sanitize_filename(contact_name) + ".json"
    filepath = event_dir / filename

    data = {
        "contact": {
            "name": contact_name,
            "email": contact_email,
            "phone": contact_phone,
        },
        "channel": channel,
        "message": message,
        "generated_at": datetime.now().isoformat(),
        "approved": True,
        "sent": False,
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return f"Saved message for {contact_name} to {filepath}"


@tool
def get_message(event_id: str, contact_name: str) -> str:
    """
    Get a previously saved message for a contact.

    Args:
        event_id: The event identifier
        contact_name: The contact's name

    Returns:
        The saved message content or "not found"
    """
    event_dir = MESSAGES_DIR / event_id
    filename = _sanitize_filename(contact_name) + ".json"
    filepath = event_dir / filename

    if not filepath.exists():
        return f"No message found for {contact_name} in event {event_id}"

    with open(filepath, "r") as f:
        data = json.load(f)

    return json.dumps(data, indent=2)


@tool
def get_messages_for_event(event_id: str) -> list[dict]:
    """
    Get all generated messages for a specific event.

    Args:
        event_id: The event identifier

    Returns:
        List of all messages with contact info and status
    """
    event_dir = MESSAGES_DIR / event_id

    if not event_dir.exists():
        return []

    messages = []
    for filepath in event_dir.glob("*.json"):
        with open(filepath, "r") as f:
            data = json.load(f)
            messages.append(data)

    return messages


@tool
def mark_message_sent(event_id: str, contact_name: str) -> str:
    """
    Mark a message as sent.

    Args:
        event_id: The event identifier
        contact_name: The contact's name

    Returns:
        Confirmation message
    """
    event_dir = MESSAGES_DIR / event_id
    filename = _sanitize_filename(contact_name) + ".json"
    filepath = event_dir / filename

    if not filepath.exists():
        return f"No message found for {contact_name}"

    with open(filepath, "r") as f:
        data = json.load(f)

    data["sent"] = True
    data["sent_at"] = datetime.now().isoformat()

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return f"Marked message to {contact_name} as sent"


@tool
def get_event_summary(event_id: str) -> str:
    """
    Get a summary of messages for an event.

    Args:
        event_id: The event identifier

    Returns:
        Summary with counts of generated, sent, and pending messages
    """
    messages = get_messages_for_event(event_id)

    if not messages:
        return f"No messages found for event: {event_id}"

    total = len(messages)
    sent = sum(1 for m in messages if m.get("sent", False))
    pending = total - sent

    by_channel = {}
    for m in messages:
        ch = m.get("channel", "Unknown")
        by_channel[ch] = by_channel.get(ch, 0) + 1

    channel_breakdown = ", ".join([f"{k}: {v}" for k, v in by_channel.items()])

    return f"""Event: {event_id}
Total messages: {total}
Sent: {sent}
Pending: {pending}
By channel: {channel_breakdown}"""


# Export all tools
ALL_TOOLS = [
    save_message,
    get_message,
    get_messages_for_event,
    mark_message_sent,
    get_event_summary,
]
