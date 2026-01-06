#!/usr/bin/env python3
"""NetNudge - AI-powered contact management and outreach."""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.netnudge.agent import create_agent

# Page configuration
st.set_page_config(
    page_title="NetNudge",
    page_icon="🤝",
    layout="wide",
)

# Category labels for selection
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


def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = None

    if "mode" not in st.session_state:
        st.session_state.mode = "cleanup"

    if "session_id" not in st.session_state:
        st.session_state.session_id = None


def get_or_create_agent(mode: str, session_id: str):
    """Get existing agent or create new one if mode/session changed."""
    needs_new_agent = (
        st.session_state.agent is None or
        st.session_state.mode != mode or
        st.session_state.session_id != session_id
    )

    if needs_new_agent:
        st.session_state.agent = create_agent(mode, session_id=session_id)
        st.session_state.mode = mode
        st.session_state.session_id = session_id

    return st.session_state.agent


def get_conversation_history(agent) -> list[dict]:
    """Extract conversation history from agent's session."""
    messages = []
    if agent and hasattr(agent, "messages") and agent.messages:
        for msg in agent.messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", [])

            # Extract text from content blocks
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                    elif isinstance(block, str):
                        text_parts.append(block)
                text = "\n".join(text_parts)
            else:
                text = str(content)

            if text.strip():
                messages.append({"role": role, "content": text})

    return messages


def main():
    """Main application entry point."""
    init_session_state()

    # Header
    st.title("🤝 NetNudge")
    st.caption("AI-powered contact management and personalized outreach")

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Mode selection
        mode = st.radio(
            "Mode",
            ["Cleanup", "Interact"],
            help="Cleanup: Review and organize contacts. Interact: Generate outreach messages.",
        )
        mode_key = mode.lower()

        st.divider()

        # Session ID input
        st.subheader("Session")
        session_id = st.text_input(
            "Session ID",
            value="default",
            help="Session ID for saving/resuming conversations",
        )

        st.divider()

        # Mode-specific options
        if mode == "Cleanup":
            st.subheader("Cleanup Mode")
            st.caption("The AI will guide you through labels and contacts.")
            # Build full session ID
            full_session_id = f"cleanup-{session_id}"
            selected_label = None
            event_name = None

        else:  # Interact mode
            st.subheader("Outreach Options")
            event_name = st.text_input(
                "Event name",
                value="New Year 2025",
                help="The occasion for your outreach (e.g., 'New Year 2025', 'Job change announcement')",
            )

            selected_label = st.selectbox(
                "Category to message",
                CATEGORY_LABELS,
                help="Select a category to generate messages for",
            )
            # Build full session ID including event
            event_slug = event_name.lower().replace(" ", "-")
            full_session_id = f"interact-{event_slug}-{session_id}"

        st.divider()

        # Quick actions
        st.subheader("Quick Actions")

        if st.button("🔄 New Session", use_container_width=True):
            # Generate new session ID
            from datetime import datetime
            new_id = datetime.now().strftime("%Y%m%d-%H%M%S")
            st.session_state.agent = None
            st.session_state.session_id = None
            st.rerun()

        if st.button("📊 View Progress", use_container_width=True):
            st.info("Progress tracking coming soon!")

    # Main chat interface (full width)
    st.subheader("💬 Chat")
    st.caption(f"Session: {full_session_id}")

    # Get or create agent with session persistence
    agent = get_or_create_agent(mode_key, full_session_id)

    # Get conversation history from agent's session
    messages = get_conversation_history(agent)

    # Create a container for chat messages
    chat_container = st.container()

    # Chat input at the bottom
    prompt = st.chat_input("Type your message...")

    # Display chat history in the container
    with chat_container:
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Process new message
    if prompt:
        # Get agent response
        with st.spinner("Thinking..."):
            try:
                # Build context for the agent
                if mode_key == "cleanup":
                    context = "The user is in cleanup mode. "
                else:
                    context = f"The user is generating messages for event '{event_name}' for contacts in '{selected_label}'. "

                # Call the agent (session manager auto-persists)
                response = agent(context + prompt)

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # Rerun to show updated messages from session
        st.rerun()


def cli_main():
    """Entry point for CLI."""
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])


if __name__ == "__main__":
    main()
