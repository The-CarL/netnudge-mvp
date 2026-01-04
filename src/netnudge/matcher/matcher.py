from typing import Optional

from .. import Contact, MatchedContact, MatchConfidence


def match_contacts(
    google_contacts: list[Contact], linkedin_contacts: list[Contact]
) -> list[MatchedContact]:
    """
    Match Google contacts with LinkedIn connections.

    Matching rules:
    - High confidence: Email match OR (full name + company match)
    - Medium confidence: Full name only match (normalized, case-insensitive)
    - No match: Contacts only in one source

    Returns all contacts with match information.
    """
    matched = []
    used_linkedin_indices: set[int] = set()

    # Build lookup indices for LinkedIn contacts
    linkedin_by_email: dict[str, int] = {}
    linkedin_by_name: dict[str, list[int]] = {}
    linkedin_by_name_company: dict[tuple[str, str], int] = {}

    for i, contact in enumerate(linkedin_contacts):
        # Index by email
        if contact.email:
            linkedin_by_email[contact.email.lower()] = i

        # Index by normalized name
        name_key = contact.normalized_name
        if name_key:
            linkedin_by_name.setdefault(name_key, []).append(i)

        # Index by name + company
        if name_key and contact.normalized_company:
            linkedin_by_name_company[(name_key, contact.normalized_company)] = i

    # Process Google contacts
    for g_contact in google_contacts:
        linkedin_match: Optional[Contact] = None
        confidence = MatchConfidence.NONE
        matched_idx: Optional[int] = None

        # Try email match (high confidence)
        if g_contact.email:
            idx = linkedin_by_email.get(g_contact.email.lower())
            if idx is not None and idx not in used_linkedin_indices:
                linkedin_match = linkedin_contacts[idx]
                confidence = MatchConfidence.HIGH
                matched_idx = idx

        # Try name + company match (high confidence)
        if not linkedin_match and g_contact.normalized_name and g_contact.normalized_company:
            key = (g_contact.normalized_name, g_contact.normalized_company)
            idx = linkedin_by_name_company.get(key)
            if idx is not None and idx not in used_linkedin_indices:
                linkedin_match = linkedin_contacts[idx]
                confidence = MatchConfidence.HIGH
                matched_idx = idx

        # Try name-only match (medium confidence)
        if not linkedin_match and g_contact.normalized_name:
            candidates = linkedin_by_name.get(g_contact.normalized_name, [])
            for idx in candidates:
                if idx not in used_linkedin_indices:
                    linkedin_match = linkedin_contacts[idx]
                    confidence = MatchConfidence.MEDIUM
                    matched_idx = idx
                    break

        # Mark LinkedIn contact as used
        if matched_idx is not None:
            used_linkedin_indices.add(matched_idx)

        # Create matched contact
        matched_contact = MatchedContact.from_contacts(
            google_contact=g_contact,
            linkedin_contact=linkedin_match,
            confidence=confidence,
        )
        matched.append(matched_contact)

    # Add unmatched LinkedIn contacts
    for i, l_contact in enumerate(linkedin_contacts):
        if i not in used_linkedin_indices:
            matched_contact = MatchedContact.from_contacts(
                google_contact=None,
                linkedin_contact=l_contact,
                confidence=MatchConfidence.NONE,
            )
            matched.append(matched_contact)

    return matched
