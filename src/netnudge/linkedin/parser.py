import csv
from pathlib import Path
from typing import Optional

from .. import Contact, ContactSource


def parse_linkedin_csv(csv_path: str | Path) -> list[Contact]:
    """
    Parse a LinkedIn connections export CSV file.

    LinkedIn export format typically includes:
    - First Name
    - Last Name
    - Email Address
    - Company
    - Position
    - Connected On
    - URL (profile URL)
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"LinkedIn CSV not found: {csv_path}")

    contacts = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        # Skip potential BOM and detect headers
        reader = csv.DictReader(f)

        # Normalize header names (LinkedIn exports can vary)
        if reader.fieldnames:
            header_map = _build_header_map(reader.fieldnames)
        else:
            raise ValueError("CSV file has no headers")

        for row in reader:
            contact = _parse_row(row, header_map)
            if contact:
                contacts.append(contact)

    return contacts


def _build_header_map(headers: list[str]) -> dict[str, str]:
    """Build a mapping from standard field names to actual CSV headers."""
    mapping = {}
    normalized = {h.lower().strip(): h for h in headers}

    # First Name variations
    for key in ["first name", "firstname", "first_name"]:
        if key in normalized:
            mapping["first_name"] = normalized[key]
            break

    # Last Name variations
    for key in ["last name", "lastname", "last_name"]:
        if key in normalized:
            mapping["last_name"] = normalized[key]
            break

    # Email variations
    for key in ["email address", "email", "emailaddress", "email_address"]:
        if key in normalized:
            mapping["email"] = normalized[key]
            break

    # Company variations
    for key in ["company", "organization", "employer"]:
        if key in normalized:
            mapping["company"] = normalized[key]
            break

    # Position/Role variations
    for key in ["position", "title", "job title", "role"]:
        if key in normalized:
            mapping["role"] = normalized[key]
            break

    # LinkedIn URL variations
    for key in ["url", "profile url", "linkedin url", "profile"]:
        if key in normalized:
            mapping["linkedin_url"] = normalized[key]
            break

    return mapping


def _parse_row(row: dict, header_map: dict[str, str]) -> Optional[Contact]:
    """Parse a single CSV row into a Contact."""
    first_name = _get_field(row, header_map, "first_name", "")
    last_name = _get_field(row, header_map, "last_name", "")

    # Skip rows without names
    if not first_name and not last_name:
        return None

    email = _get_field(row, header_map, "email")
    company = _get_field(row, header_map, "company")
    role = _get_field(row, header_map, "role")
    linkedin_url = _get_field(row, header_map, "linkedin_url")

    return Contact(
        first_name=first_name,
        last_name=last_name,
        email=email,
        company=company,
        role=role,
        linkedin_url=linkedin_url,
        source=ContactSource.LINKEDIN,
    )


def _get_field(
    row: dict, header_map: dict[str, str], field: str, default: Optional[str] = None
) -> Optional[str]:
    """Get a field value from a row using the header map."""
    header = header_map.get(field)
    if not header:
        return default

    value = row.get(header, "").strip()
    return value if value else default
