import json
import os
from typing import Callable, Optional

import anthropic

from .. import MatchedContact

BATCH_SIZE = 5
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are helping write brief, warm, personalized outreach messages for professional networking.

Guidelines:
- Keep messages concise (2-3 sentences max)
- Be warm and genuine, not salesy
- Reference specific details when available (company, role, past interactions from notes)
- Match the tone to the occasion/event
- Make it easy to respond to

You will receive a batch of contacts with their details. Return a JSON array with a message for each contact, in the same order.

Output format:
[
  {"name": "John Smith", "message": "Your personalized message here"},
  {"name": "Jane Doe", "message": "Your personalized message here"}
]

Return ONLY the JSON array, no other text."""


def generate_messages(
    contacts: list[MatchedContact],
    event: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict[str, str]:
    """
    Generate personalized messages for contacts using Claude API.

    Args:
        contacts: List of contacts to generate messages for
        event: The occasion/event for the outreach (e.g., "Happy New Year")
        progress_callback: Optional callback(completed, total) for progress updates

    Returns:
        Dictionary mapping contact full_name to generated message
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Get your API key from https://console.anthropic.com/"
        )

    client = anthropic.Anthropic(api_key=api_key)
    messages: dict[str, str] = {}

    # Process in batches
    total = len(contacts)
    for i in range(0, total, BATCH_SIZE):
        batch = contacts[i : i + BATCH_SIZE]
        batch_messages = _generate_batch(client, batch, event)
        messages.update(batch_messages)

        if progress_callback:
            progress_callback(min(i + BATCH_SIZE, total), total)

    return messages


def _generate_batch(
    client: anthropic.Anthropic, contacts: list[MatchedContact], event: str
) -> dict[str, str]:
    """Generate messages for a batch of contacts."""
    # Build contact details for the prompt
    contact_details = []
    for c in contacts:
        details = {
            "name": c.full_name,
            "company": c.company or "Unknown",
            "role": c.role or "Unknown",
        }
        if c.notes:
            details["notes"] = c.notes
        contact_details.append(details)

    user_prompt = f"""Event/Occasion: {event}

Contacts to write messages for:
{json.dumps(contact_details, indent=2)}

Generate a personalized message for each contact. Return as a JSON array."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Parse the response
        response_text = response.content[0].text.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        result = json.loads(response_text)

        # Build name -> message mapping
        messages = {}
        for item in result:
            name = item.get("name", "")
            message = item.get("message", "")
            if name and message:
                messages[name] = message

        return messages

    except json.JSONDecodeError as e:
        # If JSON parsing fails, return empty messages for this batch
        return {c.full_name: f"[Message generation failed: {e}]" for c in contacts}
    except anthropic.APIError as e:
        return {c.full_name: f"[API error: {e}]" for c in contacts}
