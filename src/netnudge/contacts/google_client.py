import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .. import Contact, ContactSource

SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]
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

    def fetch_contacts(self, group_name: Optional[str] = None) -> list[Contact]:
        """Fetch contacts, optionally filtered by group."""
        if not self.service:
            self.authenticate()

        contacts = []
        page_token = None

        # If group specified, get the group's resource name
        group_resource = None
        if group_name:
            groups = self.get_contact_groups()
            group_resource = groups.get(group_name.lower())
            if not group_resource:
                available = ", ".join(groups.keys())
                raise ValueError(
                    f"Contact group '{group_name}' not found. Available: {available}"
                )

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
                contact = self._parse_person(person)
                if contact:
                    # Filter by group if specified
                    if group_resource:
                        memberships = person.get("memberships", [])
                        member_groups = [
                            m.get("contactGroupMembership", {}).get("contactGroupResourceName")
                            for m in memberships
                        ]
                        if group_resource not in member_groups:
                            continue
                    contacts.append(contact)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return contacts

    def _parse_person(self, person: dict) -> Optional[Contact]:
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
            source=ContactSource.GOOGLE,
        )
