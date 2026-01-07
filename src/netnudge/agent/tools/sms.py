"""SMS sending tool using Google Messages Web via browser-use.

This tool uses browser automation to send SMS messages through
Google Messages for Web (messages.google.com/web).

First-time setup requires scanning a QR code with your phone.
The browser session (cookies/auth) is persisted via user_data_dir.
"""

import asyncio
import os
from pathlib import Path

from strands import tool

# Browser-use imports
from browser_use import Agent, Browser, ChatAnthropic

# Persistent browser profile directory (for auth session, not browser reuse)
BROWSER_PROFILE_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "browser_profile"
GOOGLE_MESSAGES_URL = "https://messages.google.com/web/conversations"


def _create_browser() -> Browser:
    """Create a fresh browser instance.

    Uses user_data_dir to persist auth session (QR pairing) across runs.
    Each call creates a new browser - simpler and more reliable.
    """
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return Browser(
        headless=False,
        user_data_dir=str(BROWSER_PROFILE_DIR),
    )


def _get_llm() -> ChatAnthropic:
    """Get the LLM for browser-use agent.

    Uses Sonnet 4 for browser automation - Haiku has structured output
    issues with browser-use. Sonnet is 3x more expensive but works reliably.
    SMS sends are infrequent so cost impact is minimal (~$0.01-0.02/message).
    """
    # ChatAnthropic from browser-use reads ANTHROPIC_API_KEY from env
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
    )


async def _send_sms_async(recipient: str, message: str) -> str:
    """Async implementation of SMS sending."""
    browser = _create_browser()
    llm = _get_llm()

    task = f"""
    Send an SMS to "{recipient}" via Google Messages for Web.

    STEP 1: Navigate and verify authentication
    - Go to https://messages.google.com/web/conversations
    - If you see a QR code or "Pair with QR code", STOP and return:
      "QR_AUTH_REQUIRED: Please run setup first to pair your phone."
    - Wait for the page to fully load (you should see your conversations list)

    STEP 2: Start a new chat
    - Click the "Start chat" button (blue button with + icon, usually bottom right)
    - Wait for the new conversation screen to appear

    STEP 3: Search for the contact
    - In the "To" field or search box, type: {recipient}
    - Wait for search results to appear

    STEP 4: Verify the correct contact
    - Look at the search results
    - If NO results: return "ERROR: Contact '{recipient}' not found"
    - If MULTIPLE results: return "ERROR: Multiple contacts match '{recipient}'. Please be more specific."
    - If exactly ONE result that matches "{recipient}": click on it to select

    STEP 5: Type the message
    - Click in the message input field at the bottom
    - Type this exact message (preserve formatting):
      {message}

    STEP 6: Send the message
    - Click the Send button (arrow icon) or press Enter
    - Verify the message appears in the conversation

    STEP 7: Confirm success
    - If message appears in chat: return "SUCCESS: Message sent to {recipient}"
    - If any error: return "ERROR: <describe what went wrong>"

    IMPORTANT:
    - Do NOT guess or assume - verify each step visually
    - If anything looks wrong, stop and report the error
    - The recipient name must match exactly before sending
    """

    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            max_actions_per_step=3,
        )

        result = await agent.run()

        # Extract the final result
        if hasattr(result, 'final_result'):
            final = result.final_result()
            if final:
                return str(final)
        return str(result)

    except Exception as e:
        return f"ERROR: {str(e)}"


@tool
def send_sms(recipient: str, message: str) -> str:
    """
    Send an SMS message via Google Messages for Web.

    Uses browser automation to send messages through your linked Android phone.
    First-time use requires scanning a QR code to pair with your phone.

    Args:
        recipient: The contact name or phone number to send to
        message: The message text to send

    Returns:
        Success or error message
    """
    # Run the async function in a new event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _send_sms_async(recipient, message)
                )
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(_send_sms_async(recipient, message))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(_send_sms_async(recipient, message))


@tool
def check_messages_auth() -> str:
    """
    Check if Google Messages for Web is authenticated.

    Opens the browser to messages.google.com and checks if QR code
    pairing is needed.

    Returns:
        Authentication status message
    """
    async def _check_auth():
        browser = _create_browser()
        llm = _get_llm()

        task = """
        Navigate to https://messages.google.com/web/conversations

        Check what you see:

        1. If you see a QR code or "Pair with QR code" message:
           Return "QR_AUTH_REQUIRED: Please run setup to pair your phone."

        2. If you see a list of conversations or a "Start chat" option:
           Return "AUTHENTICATED: Google Messages is connected and ready to send SMS."

        3. If you see any error or unexpected page:
           Return "ERROR: <describe what you see>"
        """

        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                max_actions_per_step=3,
            )

            result = await agent.run()

            if hasattr(result, 'final_result'):
                final = result.final_result()
                if final:
                    return str(final)
            return str(result)

        except Exception as e:
            return f"ERROR: {str(e)}"

    try:
        return asyncio.run(_check_auth())
    except Exception as e:
        return f"ERROR: {str(e)}"


# Export all tools
ALL_TOOLS = [
    send_sms,
    check_messages_auth,
]


def setup_messages_auth():
    """
    Interactive setup for Google Messages pairing.

    Opens browser and waits for you to scan the QR code.
    No timeout - take as long as you need.

    Usage:
        uv run python src/netnudge/agent/tools/sms.py setup
    """
    from playwright.sync_api import sync_playwright

    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("GOOGLE MESSAGES SETUP")
    print("="*60)
    print("\nOpening browser to messages.google.com/web...")
    print("\nOn your Android phone:")
    print("  1. Open Google Messages app")
    print("  2. Tap Menu (⋮) → Device pairing → QR code scanner")
    print("  3. Scan the QR code shown in the browser")
    print("\n" + "-"*60)
    print("Press ENTER here when pairing is complete...")
    print("="*60 + "\n")

    with sync_playwright() as p:
        # Launch with persistent context
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            headless=False,
            args=['--start-maximized'],
            no_viewport=True,
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(GOOGLE_MESSAGES_URL)

        # Wait for user to complete pairing
        input()  # Blocks until Enter is pressed

        # Check if we see conversations (authenticated) or still QR code
        try:
            # Look for conversation list or compose button
            page.wait_for_selector(
                'mws-conversations-list, [aria-label="Start chat"]',
                timeout=5000
            )
            print("\n✓ SUCCESS: Google Messages is now paired!")
            print("  Session saved to: data/browser_profile/")
            result = "AUTHENTICATED"
        except:
            # Check current URL
            url = page.url
            if "authentication" in url or "welcome" in url:
                print("\n⚠ Still on QR code page. Pairing may not have completed.")
                print("  Try scanning the QR code again, then press Enter.")
            else:
                print(f"\n⚠ Unexpected page: {url}")
            result = "NOT_AUTHENTICATED"

        context.close()
        return result


# Simple test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # Interactive setup mode
        setup_messages_auth()
    else:
        print("Testing Google Messages authentication...")
        result = check_messages_auth()
        print(f"Result: {result}")
