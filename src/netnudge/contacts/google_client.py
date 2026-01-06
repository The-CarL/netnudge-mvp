import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .. import Contact, ContactSource

SCOPES = ["https://www.googleapis.com/auth/contacts"]  # Read/write access
TOKEN_FILE = ".google_token.json"


def _get_client_config() -> dict:
    """Build OAuth client config from environment variables."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Missing Google OAuth credentials.\n"
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.\n"
            "Get these from Google Cloud Console > APIs & Services > Credentials"
        )

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


class GoogleContactsClient:
    """Client for fetching contacts from Google People API."""

    def __init__(self):
        self.creds: Optional[Credentials] = None
        self.service = None

    def authenticate(self) -> None:
        """Perform OAuth2 authentication, reusing token if available."""
        if Path(TOKEN_FILE).exists():
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                client_config = _get_client_config()
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save token for reuse
            with open(TOKEN_FILE, "w") as token:
                token.write(self.creds.to_json())

        self.service = build("people", "v1", credentials=self.creds)

    def get_contact_groups(self) -> dict[str, str]:
        """Get all contact groups (labels). Returns {name: resourceName}."""
        if not self.service:
            self.authenticate()

        results = self.service.contactGroups().list().execute()
        groups = {}
        for group in results.get("contactGroups", []):
            name = group.get("name", "")
            resource_name = group.get("resourceName", "")
            if name and resource_name:
                groups[name.lower()] = resource_name
        return groups

    def fetch_contacts(self, group_names: Optional[list[str]] = None) -> list[Contact]:
        """Fetch contacts, optionally filtered by groups (any match)."""
        if not self.service:
            self.authenticate()

        contacts = []
        page_token = None

        # Get all groups for label resolution
        all_groups = self.get_contact_groups()
        # Reverse mapping: resourceName -> display name
        resource_to_name = {v: k for k, v in all_groups.items()}

        # If groups specified, get their resource names
        group_resources: set[str] = set()
        if group_names:
            for group_name in group_names:
                group_resource = all_groups.get(group_name.lower())
                if not group_resource:
                    available = ", ".join(all_groups.keys())
                    raise ValueError(
                        f"Contact group '{group_name}' not found. Available: {available}"
                    )
                group_resources.add(group_resource)

        while True:
            # Fetch connections with required fields
            request_params = {
                "resourceName": "people/me",
                "pageSize": 100,
                "personFields": "names,emailAddresses,phoneNumbers,organizations,biographies,memberships",
            }
            if page_token:
                request_params["pageToken"] = page_token

            results = self.service.people().connections().list(**request_params).execute()

            for person in results.get("connections", []):
                # Get contact's group memberships
                memberships = person.get("memberships", [])
                member_group_resources = set(
                    m.get("contactGroupMembership", {}).get("contactGroupResourceName")
                    for m in memberships
                )

                # Filter by groups if specified (any match)
                if group_resources:
                    if not group_resources & member_group_resources:  # No intersection
                        continue

                # Resolve labels to display names (only category labels)
                labels = [
                    resource_to_name[r] for r in member_group_resources
                    if r in resource_to_name and resource_to_name[r].startswith("category")
                ]

                contact = self._parse_person(person, labels)
                if contact:
                    contacts.append(contact)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return contacts

    def _parse_person(self, person: dict, labels: list[str] = None) -> Optional[Contact]:
        """Parse a person resource into a Contact."""
        names = person.get("names", [])
        if not names:
            return None

        primary_name = names[0]
        first_name = primary_name.get("givenName", "")
        last_name = primary_name.get("familyName", "")

        if not first_name and not last_name:
            return None

        # Get primary email
        emails = person.get("emailAddresses", [])
        email = emails[0].get("value") if emails else None

        # Get primary phone
        phones = person.get("phoneNumbers", [])
        phone = phones[0].get("value") if phones else None

        # Get organization info
        orgs = person.get("organizations", [])
        company = None
        role = None
        if orgs:
            company = orgs[0].get("name")
            role = orgs[0].get("title")

        # Get notes from biographies
        bios = person.get("biographies", [])
        notes = bios[0].get("value") if bios else None

        return Contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company=company,
            role=role,
            notes=notes,
            labels=labels or [],
            source=ContactSource.GOOGLE,
        )

    def find_contact_by_email(self, email: str) -> Optional[dict]:
        """Find a contact by email address. Returns the full person resource."""
        if not self.service:
            self.authenticate()

        # Search for the contact
        results = self.service.people().searchContacts(
            query=email,
            readMask="names,emailAddresses,biographies,memberships",
        ).execute()

        for result in results.get("results", []):
            person = result.get("person", {})
            emails = person.get("emailAddresses", [])
            for e in emails:
                if e.get("value", "").lower() == email.lower():
                    return person
        return None

    def find_contact_by_name(self, name: str) -> Optional[dict]:
        """Find a contact by name. Returns the full person resource."""
        if not self.service:
            self.authenticate()

        results = self.service.people().searchContacts(
            query=name,
            readMask="names,emailAddresses,biographies,memberships",
        ).execute()

        for result in results.get("results", []):
            person = result.get("person", {})
            names = person.get("names", [])
            for n in names:
                display_name = n.get("displayName", "").lower()
                if display_name == name.lower():
                    return person
        return None

    def update_contact_notes(self, resource_name: str, new_notes: str, append: bool = True) -> bool:
        """Update a contact's notes/biography."""
        if not self.service:
            self.authenticate()

        try:
            # Get current contact data
            person = self.service.people().get(
                resourceName=resource_name,
                personFields="biographies",
            ).execute()

            current_notes = ""
            bios = person.get("biographies", [])
            if bios:
                current_notes = bios[0].get("value", "")

            # Append or replace
            if append and current_notes:
                updated_notes = f"{current_notes}\n\n---\n{new_notes}"
            else:
                updated_notes = new_notes

            # Update the contact
            self.service.people().updateContact(
                resourceName=resource_name,
                updatePersonFields="biographies",
                body={
                    "etag": person.get("etag"),
                    "biographies": [{"value": updated_notes}],
                },
            ).execute()
            return True
        except Exception:
            return False

    def create_contact_group(self, name: str) -> str:
        """Create a new contact group. Returns the resource name."""
        if not self.service:
            self.authenticate()

        result = self.service.contactGroups().create(
            body={"contactGroup": {"name": name}}
        ).execute()
        return result.get("resourceName", "")

    def add_contact_to_group(self, contact_resource: str, group_resource: str) -> bool:
        """Add a contact to a group."""
        if not self.service:
            self.authenticate()

        try:
            self.service.contactGroups().members().modify(
                resourceName=group_resource,
                body={"resourceNamesToAdd": [contact_resource]},
            ).execute()
            return True
        except Exception:
            return False

    def remove_contact_from_group(self, contact_resource: str, group_resource: str) -> bool:
        """Remove a contact from a group."""
        if not self.service:
            self.authenticate()

        try:
            self.service.contactGroups().members().modify(
                resourceName=group_resource,
                body={"resourceNamesToRemove": [contact_resource]},
            ).execute()
            return True
        except Exception:
            return False

    def get_or_create_group(self, name: str) -> str:
        """Get existing group or create new one. Returns resource name."""
        groups = self.get_contact_groups()
        if name.lower() in groups:
            return groups[name.lower()]
        return self.create_contact_group(name)
