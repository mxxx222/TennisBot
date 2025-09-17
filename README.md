# TennisBot

A Python-based tennis API client for fetching prematch data and live tennis information from tennisapi.com.

## Features

- REST API client for prematch tennis data
- WebSocket listener for live tennis updates
- Match search by date and player names
- Comprehensive data bundle (match info, odds, H2H stats)
- Command-line interface for easy usage

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API credentials in `.env`:
```bash
TENNIS_API_KEY=your_api_key_here
TENNIS_WS_URL=wss://live.tennisapi.com/stream
```

## Usage

### Prematch Data
Get prematch information for a specific match:
```bash
export $(cat .env | xargs)
python tennis_client.py --date 2025-09-17 --match "Sinner vs Alcaraz"
```

### Live Data
Listen to live updates via WebSocket:
```bash
export $(cat .env | xargs)
python tennis_client.py --date 2025-09-17 --match "Sinner vs Alcaraz" --live --ws_url "$TENNIS_WS_URL"
```

## Implementation Details

The client implements:

1. **REST API Integration**: Fetches prematch data including:
   - Match information and details
   - Betting odds
   - Head-to-head statistics

2. **WebSocket Integration**: Live streaming of:
   - Real-time match updates
   - Score changes
   - Event notifications

3. **Smart Match Search**: 
   - Fuzzy matching by player names
   - Date-based filtering
   - Fallback mechanisms for partial matches

## API Methods

The client automatically tries multiple API method names to ensure compatibility:
- `get_events` / `get_events_day` for event listing
- `get_event` / `get_event_details` for match info
- `get_odds` / `get_event_odds` for betting data
- `get_h2h` for head-to-head statistics

## n8n Workflow Integration

For n8n integration, use the following workflow structure:

1. **Trigger**: Webhook POST `/tennis/prematch`
2. **Body**: `{ "date":"YYYY-MM-DD", "match":"Player A vs Player B" }`
3. **HTTP Requests**: Chain API calls for events, details, odds, and H2H
4. **Response**: Return consolidated JSON data

## Notes

- API method names may vary depending on your tennisapi.com subscription
- WebSocket URL should be obtained from your service provider
- The script handles API errors gracefully and provides clear error messages
- Ensure your API key has the necessary permissions for all required methods