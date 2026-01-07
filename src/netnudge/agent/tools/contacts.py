"""Google Contacts tools for the agent."""

from strands import tool
from typing import Optional
import threading

from ...contacts import GoogleContactsClient

# Singleton client instance with thread safety
_client: Optional[GoogleContactsClient] = None
_client_lock = threading.Lock()


def _get_client() -> GoogleContactsClient:
    """Get or create the Google Contacts client (thread-safe)."""
    global _client
    if _client is None:
        with _client_lock:
            # Double-check locking pattern
            if _client is None:
                _client = GoogleContactsClient()
                _client.authenticate()
    return _client


@tool
def list_contacts_by_label(label: str) -> list[dict]:
    """
    List all contacts that have a specific category label.

    Args:
        label: The category label name (e.g., "category 2 - professional nodes")

    Returns:
        List of contacts with their details (name, email, phone, company, notes, labels)
    """
    client = _get_client()
    contacts = client.fetch_contacts(group_names=[label])

    return [
        {
            "name": c.full_name,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "company": c.company,
            "role": c.role,
            "notes": c.notes,
            "labels": c.labels,
        }
        for c in contacts
    ]


@tool
def get_all_labels() -> list[str]:
    """
    Get all available contact group labels.

    Returns:
        List of all label names in Google Contacts
    """
    client = _get_client()
    groups = client.get_contact_groups()
    # Filter to only category labels
    return sorted([name for name in groups.keys() if name.startswith("category")])


@tool
def search_contacts(query: str) -> list[dict]:
    """
    Search contacts by name, email, or company.

    Args:
        query: Search query string

    Returns:
        List of matching contacts with their details
    """
    client = _get_client()

    # Try to find by name first
    person = client.find_contact_by_name(query)
    if not person:
        # Try by email
        person = client.find_contact_by_email(query)

    if not person:
        return []

    names = person.get("names", [{}])
    emails = person.get("emailAddresses", [])
    bios = person.get("biographies", [])

    return [
        {
            "name": names[0].get("displayName", "") if names else "",
            "email": emails[0].get("value") if emails else None,
            "notes": bios[0].get("value") if bios else None,
            "resource_name": person.get("resourceName"),
        }
    ]


@tool
def update_contact_notes(name_or_email: str, notes: str) -> str:
    """
    Append notes to a contact's biography in Google Contacts.

    Args:
        name_or_email: The contact's name or email address
        notes: The notes to append to the contact

    Returns:
        Success or failure message
    """
    client = _get_client()

    # Find the contact
    person = client.find_contact_by_email(name_or_email)
    if not person:
        person = client.find_contact_by_name(name_or_email)

    if not person:
        return f"Contact not found: {name_or_email}"

    resource_name = person.get("resourceName")
    if not resource_name:
        return f"No resource name for contact: {name_or_email}"

    success = client.update_contact_notes(resource_name, notes, append=True)
    if success:
        return f"Successfully updated notes for {name_or_email}"
    else:
        return f"Failed to update notes for {name_or_email}"


@tool
def add_label_to_contact(name_or_email: str, label: str) -> str:
    """
    Add a category label to a contact.

    Args:
        name_or_email: The contact's name or email address
        label: The category label to add (e.g., "category 7 - close friends")

    Returns:
        Success or failure message
    """
    client = _get_client()

    # Validate it's a category label
    if not label.lower().startswith("category"):
        return f"Only category labels are allowed. Got: {label}"

    # Find the contact
    person = client.find_contact_by_email(name_or_email)
    if not person:
        person = client.find_contact_by_name(name_or_email)

    if not person:
        return f"Contact not found: {name_or_email}"

    resource_name = person.get("resourceName")
    if not resource_name:
        return f"No resource name for contact: {name_or_email}"

    # Get or create the group
    group_resource = client.get_or_create_group(label)

    success = client.add_contact_to_group(resource_name, group_resource)
    if success:
        return f"Successfully added label '{label}' to {name_or_email}"
    else:
        return f"Failed to add label '{label}' to {name_or_email}"


@tool
def remove_label_from_contact(name_or_email: str, label: str) -> str:
    """
    Remove a category label from a contact.

    Args:
        name_or_email: The contact's name or email address
        label: The category label to remove

    Returns:
        Success or failure message
    """
    client = _get_client()

    # Validate it's a category label
    if not label.lower().startswith("category"):
        return f"Only category labels can be removed. Got: {label}"

    # Find the contact
    person = client.find_contact_by_email(name_or_email)
    if not person:
        person = client.find_contact_by_name(name_or_email)

    if not person:
        return f"Contact not found: {name_or_email}"

    resource_name = person.get("resourceName")
    if not resource_name:
        return f"No resource name for contact: {name_or_email}"

    # Get the group
    groups = client.get_contact_groups()
    group_resource = groups.get(label.lower())

    if not group_resource:
        return f"Label not found: {label}"

    success = client.remove_contact_from_group(resource_name, group_resource)
    if success:
        return f"Successfully removed label '{label}' from {name_or_email}"
    else:
        return f"Failed to remove label '{label}' from {name_or_email}"


# Export all tools
ALL_TOOLS = [
    list_contacts_by_label,
    get_all_labels,
    search_contacts,
    update_contact_notes,
    add_label_to_contact,
    remove_label_from_contact,
]
