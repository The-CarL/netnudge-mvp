#!/usr/bin/env python3
"""NetNudge MVP - Generate personalized network outreach messages."""

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.netnudge import MatchedContact, OutreachRecord
from src.netnudge.contacts import GoogleContactsClient
from src.netnudge.generator import generate_messages
from src.netnudge.linkedin import parse_linkedin_csv
from src.netnudge.matcher import match_contacts
from src.netnudge.output import write_xlsx

app = typer.Typer(
    name="netnudge",
    help="Generate personalized outreach messages for your network.",
    add_completion=False,
)


def progress_callback(completed: int, total: int) -> None:
    """Display progress for message generation."""
    typer.echo(f"  Generating messages: {completed}/{total}", nl=False)
    typer.echo("\r", nl=False)


@app.command()
def generate(
    event: str = typer.Option(
        ...,
        "--event",
        "-e",
        help="The occasion/event for outreach (e.g., 'Happy New Year', 'checking in')",
    ),
    linkedin_csv: Path = typer.Option(
        ...,
        "--linkedin-csv",
        "-l",
        help="Path to LinkedIn connections CSV export",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        Path("./data/outreach.xlsx"),
        "--output",
        "-o",
        help="Output Excel file path",
    ),
    group: Optional[str] = typer.Option(
        None,
        "--group",
        "-g",
        help="Google Contacts group/label to filter by",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Skip message generation (output contacts without messages)",
    ),
) -> None:
    """Generate personalized outreach messages for your contacts."""
    typer.echo(f"NetNudge MVP - Generating outreach for: {event}")
    typer.echo()

    # Step 1: Fetch Google Contacts
    typer.echo("Fetching Google Contacts...")
    try:
        google_client = GoogleContactsClient()
        google_contacts = google_client.fetch_contacts(group_name=group)
        typer.echo(f"  Found {len(google_contacts)} Google contacts")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nSee README.md for setup instructions.", err=True)
        raise typer.Exit(1)

    # Step 2: Parse LinkedIn CSV
    typer.echo("Parsing LinkedIn connections...")
    try:
        linkedin_contacts = parse_linkedin_csv(linkedin_csv)
        typer.echo(f"  Found {len(linkedin_contacts)} LinkedIn connections")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Step 3: Match contacts
    typer.echo("Matching contacts...")
    matched = match_contacts(google_contacts, linkedin_contacts)

    # Count by confidence
    high = sum(1 for c in matched if c.match_confidence.value == "High")
    medium = sum(1 for c in matched if c.match_confidence.value == "Medium")
    none = sum(1 for c in matched if c.match_confidence.value == "N/A")
    typer.echo(f"  Matched: {high} high, {medium} medium, {none} unmatched")
    typer.echo(f"  Total contacts: {len(matched)}")
    typer.echo()

    # Step 4: Generate messages
    messages: dict[str, str] = {}
    if not dry_run:
        typer.echo("Generating personalized messages...")
        try:
            messages = generate_messages(
                matched, event, progress_callback=progress_callback
            )
            typer.echo()  # Clear progress line
            typer.echo(f"  Generated {len(messages)} messages")
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo("Dry run - skipping message generation")

    # Step 5: Create output records
    records = []
    for contact in matched:
        message = messages.get(contact.full_name, "" if dry_run else "[No message]")
        record = OutreachRecord.from_matched_contact(contact, message)
        records.append(record)

    # Step 6: Write Excel output
    typer.echo()
    typer.echo(f"Writing output to {output}...")
    output_path = write_xlsx(records, output)
    typer.echo(f"  Created: {output_path}")
    typer.echo()
    typer.echo(typer.style("Done!", fg=typer.colors.GREEN, bold=True))


@app.command()
def list_groups() -> None:
    """List available Google Contact groups/labels."""
    typer.echo("Fetching Google Contact groups...")
    try:
        google_client = GoogleContactsClient()
        google_client.authenticate()
        groups = google_client.get_contact_groups()

        if groups:
            typer.echo("\nAvailable groups:")
            for name in sorted(groups.keys()):
                typer.echo(f"  - {name}")
        else:
            typer.echo("No contact groups found.")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
