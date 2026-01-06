# NetNudge

AI-powered contact management and personalized outreach for your professional network.

## Features

- **Cleanup Mode**: Review and organize contacts label-by-label with AI assistance
- **Interact Mode**: Generate personalized outreach messages for events
- Real-time updates to Google Contacts
- Persistent context (remembers life events, preferences)
- Chat-based UI powered by Strands Agents + Claude

## Prerequisites

- Python 3.12+
- Google Cloud Platform account (for Google Contacts API)
- Anthropic API key (for Claude)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/The-CarL/netnudge-mvp.git
cd netnudge-mvp
uv sync  # or: pip install -e .
```

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **People API**:
   - Go to APIs & Services > Library
   - Search for "People API"
   - Click Enable
4. Configure OAuth consent screen:
   - Go to APIs & Services > OAuth consent screen
   - Select "External" user type
   - Fill in app name, support email
   - Add scope: `https://www.googleapis.com/auth/contacts` (read/write access)
   - Add yourself as a test user
5. Create OAuth credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app"
   - Copy the **Client ID** and **Client Secret**

### 3. Anthropic API Setup

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key

### 4. Environment Setup

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

## Usage

### Launch the App

```bash
uv run streamlit run app.py
```

This opens a web UI at http://localhost:8501

### Modes

#### Cleanup Mode
Review contacts in a specific category and:
- Verify categorization is still accurate
- Fix outdated information
- Add notes about the relationship
- Reassign category labels

The AI assistant guides you through each contact, asking relevant questions and updating both local state and Google Contacts in real-time.

#### Interact Mode
Generate personalized outreach messages:
1. Set the event/occasion (e.g., "New Year 2025", "Job change")
2. Select a category of contacts to message
3. Chat with the AI to generate personalized messages
4. Approve messages before they're saved

Messages are saved to `./data/messages/{event_id}/` as JSON files.

## Project Structure

```
netnudge-mvp/
├── src/netnudge/
│   ├── agent/
│   │   ├── agent.py          # Strands agent setup
│   │   └── tools/
│   │       ├── contacts.py   # Google Contacts tools
│   │       ├── state.py      # Persistence tools
│   │       └── messages.py   # Message output tools
│   ├── contacts/
│   │   └── google_client.py  # Google People API client
│   └── ui/
│       └── components.py     # Streamlit components
├── app.py                    # Streamlit entry point
├── data/
│   ├── state/                # Persisted context & interactions
│   └── messages/             # Generated outreach messages
└── .env                      # Credentials (not versioned)
```

## Data Persistence

### State Files (`data/state/`)

- `context.json`: User preferences, life events, current event info
- `interactions.json`: Per-contact interaction history

### Message Files (`data/messages/{event_id}/`)

Each message is saved as a JSON file:

```json
{
  "contact": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  },
  "channel": "SMS",
  "message": "Hey John! Happy New Year!...",
  "generated_at": "2025-01-06T10:30:00",
  "approved": true,
  "sent": false
}
```

## Category Labels

Available category labels:

```
category 1 - professional nodes - friends or acquaintances
category 2 - professional nodes
category 3 - lost professional nodes
category 4 - nodes - friends or acquaintances
category 5 - nodes
category 6 - lost nodes
category 7 - close friends
category 8 - friends
category 9 - acquaintances
category 10 - lost friends and acquaintances
category 11 - only woman :)
category 14 - ski patrol
category 15 - family
category 101 - uc
category 102 - other
```

Only `category` labels are managed by this tool. System labels like `mycontacts` are protected.

## Tech Stack

- **Strands Agents SDK** - AI agent framework
- **Claude Sonnet** - AI model (via Anthropic API)
- **Streamlit** - Web UI
- **Google People API** - Contact management

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
Make sure your `.env` file contains a valid API key.

### "Missing Google OAuth credentials"
Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are in `.env`.

### Google OAuth errors
- Make sure People API is enabled
- Add yourself as a test user in OAuth consent screen
- Delete `.google_token.json` to re-authenticate

## License

MIT - see [LICENSE](LICENSE) for details.
