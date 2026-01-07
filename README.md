# NetNudge

AI-powered contact management and personalized outreach for your professional network.

## Features

- **Cleanup Mode**: Review contacts and categorize as active vs "lost" relationships
- **Interact Mode**: Generate and send personalized messages with three execution modes
- **SMS Sending**: Send messages via Google Messages Web (Android phones)
- Real-time updates to Google Contacts
- Session persistence across restarts
- Chat-based UI powered by Strands Agents + Claude Haiku

## Prerequisites

- Python 3.12+
- Google Cloud Platform account (for Google Contacts API)
- Anthropic API key (for Claude)
- Android phone with Google Messages (for SMS sending)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/The-CarL/netnudge-mvp.git
cd netnudge-mvp
uv sync
```

### 2. Install Playwright Browser

```bash
uv run playwright install chromium
```

### 3. Google Cloud Setup

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

### 4. Anthropic API Setup

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key

### 5. Environment Setup

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

### 6. Google Messages Setup (for SMS)

First-time only - pair your phone:

```bash
uv run python -c "
from dotenv import load_dotenv; load_dotenv()
from src.netnudge.agent.tools.sms import check_messages_auth
print(check_messages_auth())
"
```

A browser opens to `messages.google.com/web`. Scan the QR code with your Android phone:
1. Open Google Messages app
2. Tap Menu (⋮) → Device pairing → QR code scanner
3. Scan the QR code

The session persists in `data/browser_profile/`.

## Usage

### Launch the App

```bash
uv run streamlit run app.py
```

Opens a web UI at http://localhost:8501

### Cleanup Mode

Review contacts label-by-label to determine active vs "lost" relationships:

| Active Categories | Lost Category |
|-------------------|---------------|
| category 1 + 2 (professional nodes) | → category 3 (lost professional) |
| category 4 + 5 (nodes) | → category 6 (lost nodes) |
| category 7 + 8 + 9 (friends) | → category 10 (lost friends) |

Workflow:
1. Select an active category to review
2. Contacts shown oldest-first (most likely to be "lost")
3. For each contact: keep active, move to lost, or update info
4. All changes include dated notes in Google Contacts

### Interact Mode

Generate and send personalized outreach messages. Three execution modes:

| Mode | Description |
|------|-------------|
| **Message Gen** | Generate messages only, save for later |
| **One-by-One** | Review → approve/edit/skip → send → update notes |
| **Full Autonomous** | Generate → send → update (no review) |

**SMS Eligibility:**
- ✅ US numbers (+1 or standard US format)
- ❌ Non-US numbers → marked for manual followup
- ❌ No phone → marked for manual followup

Non-eligible contacts are logged for manual handling later.

## Project Structure

```
netnudge-mvp/
├── src/netnudge/
│   ├── agent/
│   │   ├── agent.py          # Strands agent setup + prompts
│   │   └── tools/
│   │       ├── contacts.py   # Google Contacts tools
│   │       ├── state.py      # Persistence tools
│   │       ├── messages.py   # Message output tools
│   │       ├── system.py     # Date/time tools
│   │       └── sms.py        # SMS via Google Messages
│   └── contacts/
│       └── google_client.py  # Google People API client (httpx transport)
├── app.py                    # Streamlit entry point
├── data/
│   ├── state/                # Persisted context & interactions
│   ├── messages/             # Generated outreach messages
│   ├── sessions/             # Agent conversation history
│   └── browser_profile/      # Persistent browser for SMS
└── .env                      # Credentials (not versioned)
```

## Data Persistence

### State Files (`data/state/`)

- `context.json`: User preferences, life events, manual followup list
- `interactions.json`: Per-contact interaction history

### Message Files (`data/messages/{event_id}/`)

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

### Session Files (`data/sessions/`)

Conversation history for resuming sessions.

## Category Labels

```
Active:
  category 1 - professional nodes - friends or acquaintances
  category 2 - professional nodes
  category 4 - nodes - friends or acquaintances
  category 5 - nodes
  category 7 - close friends
  category 8 - friends
  category 9 - acquaintances

Lost:
  category 3 - lost professional nodes
  category 6 - lost nodes
  category 10 - lost friends and acquaintances

Other:
  category 11 - only woman :)
  category 14 - ski patrol
  category 15 - family
  category 101 - uc
  category 102 - other
```

## Tech Stack

- **Strands Agents SDK** - AI agent framework
- **Claude Haiku 4.5** - AI model (cost-efficient)
- **Streamlit** - Web UI
- **Google People API** - Contact management
- **browser-use** - Browser automation for SMS
- **httpx** - HTTP client (replaces httplib2 for stability)

## Cost

Uses Claude Haiku 4.5 (~$1/M input, $5/M output tokens). Typical session costs < $0.10.

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
Make sure your `.env` file contains a valid API key.

### "Missing Google OAuth credentials"
Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are in `.env`.

### Google OAuth errors
- Make sure People API is enabled
- Add yourself as a test user in OAuth consent screen
- Delete `.google_token.json` to re-authenticate

### Memory corruption / malloc errors
This was fixed by using httpx instead of httplib2. If issues persist, ensure you're using the pinned package versions in `pyproject.toml`.

### SMS not sending
- Run `check_messages_auth()` to verify Google Messages is paired
- Browser profile is stored in `data/browser_profile/`
- Delete that folder and re-pair if needed

## Roadmap (Post-MVP)

### Event-Driven Autonomous Pipeline
- Fully autonomous outreach with no human interaction
- Trigger-based messaging (birthdays, job changes, anniversaries)
- Scheduled campaigns with smart send-time optimization
- Response detection and automated follow-up sequences

### Multi-Channel Messaging
- **LinkedIn** - Direct messages via browser automation
- **Signal** - Via Signal CLI or linked desktop
- **WhatsApp** - Via WhatsApp Web
- **Email** - Gmail/Outlook integration
- **SMS** - T-Mobile Digits, Google Voice, or carrier APIs
- Channel preference learning per contact

### Contact Discovery & Enrichment
- LinkedIn contact import and sync
- Automatic profile enrichment (company, role, location)
- Life event detection (job changes, promotions, moves)
- Relationship strength scoring with decay modeling

### Contact Management Dashboard
- Single source of truth for all contacts
- Who to engage, when, why, and how
- Customizable category labels (not hardcoded)
- Relationship health scores and alerts
- Engagement history timeline
- Pipeline/funnel view for networking goals

### Intelligence & Analytics
- Message effectiveness tracking (response rates)
- A/B testing for outreach templates
- Optimal timing analysis per contact
- Network graph visualization
- Warm intro path finding

### Integrations
- Calendar sync (Google Calendar, Outlook)
- Meeting scheduling automation
- CRM export (HubSpot, Salesforce)
- Voice/call logging

### Performance & Cost Optimization
- **Async message sending** - Current browser automation is slow (~5s/message). Need parallel execution or queue-based approach.
- **Smart model selection** - Use cheaper models (Haiku) for simple tasks, expensive models (Sonnet/Opus) only for complex reasoning
- **Prompt caching** - 90% savings on repeated system prompts (requires Bedrock or LiteLLM)
- **Token budgeting** - Set per-session cost limits with automatic model downgrade

### Conversation Context (SSoT)
- **Import prior text conversations** - Pull SMS/iMessage history for context
- **Unified interaction timeline** - All channels (SMS, email, LinkedIn, calls) in one view
- **Context-aware message generation** - Reference last conversation, time since contact
- **Sentiment tracking** - Relationship health based on conversation tone

### End-to-End Vision
A fully autonomous networking co-pilot that:
1. **Monitors** your network for engagement opportunities
2. **Prioritizes** who needs attention based on relationship decay
3. **Drafts** personalized messages using context from ALL prior interactions
4. **Sends** via the optimal channel at the optimal time
5. **Tracks** responses and schedules follow-ups
6. **Updates** contact records automatically
7. **Reports** on network health and engagement metrics

No daily check-ins required - just periodic reviews of autonomous actions.

## License

MIT - see [LICENSE](LICENSE) for details.
