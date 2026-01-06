"""System tools for the agent."""

from datetime import datetime

from strands import tool


@tool
def get_current_datetime() -> str:
    """
    Get the current date and time on the local system.

    Returns:
        Current datetime in a human-readable format
    """
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


@tool
def get_current_date() -> str:
    """
    Get the current date.

    Returns:
        Current date (e.g., "January 6, 2025")
    """
    return datetime.now().strftime("%B %d, %Y")


# Export all tools
ALL_TOOLS = [
    get_current_datetime,
    get_current_date,
]
