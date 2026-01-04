from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MatchConfidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    NONE = "N/A"


class Channel(str, Enum):
    SMS = "SMS"
    LINKEDIN = "LinkedIn"


class ContactSource(str, Enum):
    GOOGLE = "google"
    LINKEDIN = "linkedin"


@dataclass
class Contact:
    """Represents a contact from either Google or LinkedIn."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: ContactSource = ContactSource.GOOGLE

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def normalized_name(self) -> str:
        """Lowercase, stripped name for matching."""
        return self.full_name.lower().strip()

    @property
    def normalized_company(self) -> Optional[str]:
        """Lowercase, stripped company for matching."""
        if self.company:
            return self.company.lower().strip()
        return None


@dataclass
class MatchedContact:
    """A contact with match information from both sources."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None
    linkedin_url: Optional[str] = None
    match_confidence: MatchConfidence = MatchConfidence.NONE
    channel: Channel = Channel.LINKEDIN

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def from_contacts(
        cls,
        google_contact: Optional[Contact],
        linkedin_contact: Optional[Contact],
        confidence: MatchConfidence,
    ) -> "MatchedContact":
        """Create a MatchedContact by merging Google and LinkedIn data."""
        # Prefer Google data for name, email, phone; LinkedIn for URL
        g = google_contact
        l = linkedin_contact

        first_name = (g.first_name if g else None) or (l.first_name if l else "") or ""
        last_name = (g.last_name if g else None) or (l.last_name if l else "") or ""
        email = (g.email if g else None) or (l.email if l else None)
        phone = g.phone if g else None
        company = (g.company if g else None) or (l.company if l else None)
        role = (g.role if g else None) or (l.role if l else None)
        notes = g.notes if g else None
        linkedin_url = l.linkedin_url if l else None

        # Determine channel: SMS if phone available, else LinkedIn
        channel = Channel.SMS if phone else Channel.LINKEDIN

        return cls(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company=company,
            role=role,
            notes=notes,
            linkedin_url=linkedin_url,
            match_confidence=confidence,
            channel=channel,
        )


@dataclass
class OutreachRecord:
    """Final output record for the Excel spreadsheet."""
    name: str
    company: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    channel: str
    match_confidence: str
    message: str
    sent: bool = False

    @classmethod
    def from_matched_contact(cls, contact: MatchedContact, message: str) -> "OutreachRecord":
        return cls(
            name=contact.full_name,
            company=contact.company,
            phone=contact.phone,
            email=contact.email,
            linkedin_url=contact.linkedin_url,
            channel=contact.channel.value,
            match_confidence=contact.match_confidence.value,
            message=message,
            sent=False,
        )
