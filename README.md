# NetNudge MVP

CLI tool to generate personalized outreach messages for your professional network by combining Google Contacts with LinkedIn connections.

## Features

- Pull contacts from Google Contacts via People API
- Import LinkedIn connections from CSV export
- Match contacts across sources (email, name, company)
- Generate personalized messages using Claude AI
- Output to Excel spreadsheet for review and manual sending

## Prerequisites

- Python 3.12+
- Google Cloud Platform account
- Anthropic API account (for Claude)
- LinkedIn account (for connections export)

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
   - Add scope: `https://www.googleapis.com/auth/contacts.readonly`
   - Add yourself as a test user
5. Create OAuth credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app"
   - Copy the **Client ID** and **Client Secret** (you'll add these to `.env`)

### 3. Claude API Setup

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-api...`)

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

### 5. Export LinkedIn Connections

1. Go to [LinkedIn Settings](https://www.linkedin.com/mypreferences/d/download-my-data)
2. Request your data archive
3. Wait for email notification (can take up to 24 hours)
4. Download and extract the archive
5. Find `Connections.csv` and copy it to `./data/` folder

## Usage

### Basic Usage

```bash
# Generate New Year outreach messages
python cli.py generate --event "Happy New Year" --linkedin-csv ./data/Connections.csv

# With output path
python cli.py generate -e "checking in" -l ./data/Connections.csv -o ./data/outreach-jan.xlsx
```

### Filter by Contact Group

```bash
# Only contacts in a specific Google Contacts group
python cli.py generate -e "Happy New Year" -l ./data/Connections.csv --group "networking-active"
```

### List Available Groups

```bash
python cli.py list-groups
```

### Dry Run (Skip Message Generation)

```bash
# Test matching without using Claude API
python cli.py generate -e "test" -l ./data/Connections.csv --dry-run
```

## Output

The tool generates an Excel file with columns:

| Column | Description |
|--------|-------------|
| Name | Contact's full name |
| Company | Company name |
| Phone | Phone number (if available) |
| Email | Email address |
| LinkedIn URL | Profile URL from LinkedIn |
| Channel | Suggested channel: SMS (if phone) or LinkedIn |
| Match Confidence | High, Medium, or N/A |
| Message | Generated personalized message |
| Sent | Checkbox for tracking |

## Matching Logic

Contacts are matched between Google and LinkedIn using:

- **High confidence**: Email address match OR (full name + company match)
- **Medium confidence**: Full name match only
- **N/A**: Contact exists in only one source

## Project Structure

```
netnudge-mvp/
├── src/netnudge/
│   ├── contacts/       # Google Contacts API
│   ├── linkedin/       # CSV parser
│   ├── matcher/        # Contact matching
│   ├── generator/      # Claude message generation
│   └── output/         # Excel writer
├── cli.py              # Main entry point
├── .env                # All credentials (not versioned)
└── data/               # CSV inputs and outputs (not versioned)
```

## Future Vision

This is an MVP. The full version will be agentic with:
- Automatic message sending via SMS/LinkedIn APIs
- Response tracking and conversation management
- Relationship scoring and prioritization
- Calendar integration for follow-ups

## Troubleshooting

### "Missing Google OAuth credentials"
Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file.

### "ANTHROPIC_API_KEY not set"
Create a `.env` file with your API key. See Setup section.

### "Contact group not found"
Run `python cli.py list-groups` to see available groups.

### OAuth consent screen errors
Make sure you added yourself as a test user in Google Cloud Console.

## License

MIT - see [LICENSE](LICENSE) for details.
