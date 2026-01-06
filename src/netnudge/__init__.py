"""NetNudge - AI-powered contact management and personalized outreach."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContactSource(str, Enum):
    GOOGLE = "google"


@dataclass
class Contact:
    """Represents a contact from Google Contacts."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    source: ContactSource = ContactSource.GOOGLE

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def normalized_name(self) -> str:
        """Lowercase, stripped name for matching."""
        return self.full_name.lower().strip()


# Category labels available in the system
CATEGORY_LABELS = [
    "category 1 - professional nodes - friends or acquaintances",
    "category 2 - professional nodes",
    "category 3 - lost professional nodes",
    "category 4 - nodes - friends or acquaintances",
    "category 5 - nodes",
    "category 6 - lost nodes",
    "category 7 - close friends",
    "category 8 - friends",
    "category 9 - acquaintances",
    "category 10 - lost friends and acquaintances",
    "category 11 - only woman :)",
    "category 14 - ski patrol",
    "category 15 - family",
    "category 101 - uc",
    "category 102 - other",
]
