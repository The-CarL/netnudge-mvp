"""Reusable Streamlit UI components."""

from typing import Optional
import streamlit as st


def display_contact_card(contact: dict) -> None:
    """
    Display a contact card with their information.

    Args:
        contact: Dictionary with contact details
    """
    with st.container():
        st.markdown("---")

        # Name and company
        name = contact.get("name", "Unknown")
        company = contact.get("company", "")
        role = contact.get("role", "")

        st.subheader(name)
        if company or role:
            company_role = " - ".join(filter(None, [role, company]))
            st.caption(company_role)

        # Contact info
        col1, col2 = st.columns(2)
        with col1:
            email = contact.get("email")
            if email:
                st.markdown(f"**Email:** {email}")

            phone = contact.get("phone")
            if phone:
                st.markdown(f"**Phone:** {phone}")

        with col2:
            labels = contact.get("labels", [])
            if labels:
                st.markdown("**Labels:**")
                for label in labels:
                    st.markdown(f"- {label}")

        # Notes
        notes = contact.get("notes")
        if notes:
            with st.expander("Notes"):
                st.text(notes)

        st.markdown("---")


def display_message_card(message_data: dict) -> None:
    """
    Display a message card with contact and message info.

    Args:
        message_data: Dictionary with message details
    """
    with st.container():
        contact = message_data.get("contact", {})
        name = contact.get("name", "Unknown")
        channel = message_data.get("channel", "Unknown")
        message = message_data.get("message", "")
        sent = message_data.get("sent", False)

        # Status indicator
        status_icon = "✅" if sent else "⏳"

        st.markdown(f"### {status_icon} {name}")
        st.caption(f"Channel: {channel}")

        st.info(message)

        # Contact info for sending
        col1, col2 = st.columns(2)
        with col1:
            if contact.get("phone"):
                st.markdown(f"📱 {contact['phone']}")
        with col2:
            if contact.get("email"):
                st.markdown(f"📧 {contact['email']}")


def contact_action_buttons(contact: dict, key_prefix: str) -> Optional[str]:
    """
    Display action buttons for a contact and return the action taken.

    Args:
        contact: Dictionary with contact details
        key_prefix: Unique prefix for button keys

    Returns:
        Action string ("engaged", "skipped") or None if no action taken
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Engaged", key=f"{key_prefix}_engaged"):
            return "engaged"

    with col2:
        if st.button("⏭️ Skip", key=f"{key_prefix}_skip"):
            return "skipped"

    with col3:
        if st.button("✏️ Edit", key=f"{key_prefix}_edit"):
            return "edit"

    with col4:
        if st.button("💾 Save", key=f"{key_prefix}_save"):
            return "save"

    return None


def label_selector(current_labels: list[str], key: str) -> list[str]:
    """
    Display a multi-select for category labels.

    Args:
        current_labels: Currently assigned labels
        key: Unique key for the widget

    Returns:
        Selected labels
    """
    all_labels = [
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

    return st.multiselect(
        "Labels",
        options=all_labels,
        default=current_labels,
        key=key,
    )
