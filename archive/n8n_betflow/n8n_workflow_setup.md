# n8n Tennis Results Workflow v2.9.4 - Setup Guide

## Overview

This n8n workflow fetches tennis match data from Tennis API v2.9.4, performs ROI analysis, and generates structured insights for ITF and Challenger level matches.

## Features

- **Scheduled Execution**: Runs 3 times daily (07:30, 11:30, 15:30)
- **Multi-Endpoint Integration**: Fetches fixtures, odds, H2H, and player statistics
- **ROI Analysis**: Calculates profitability flags, expected value, and insights
- **ITF/Challenger Filtering**: Focuses on ITF and Challenger Singles matches
- **Structured Output**: Generates OpenAI-Operator style JSON responses

## Prerequisites

1. **n8n Installation**: n8n must be installed and running
   - Self-hosted: https://docs.n8n.io/getting-started/installation/
   - Cloud: https://n8n.io/

2. **Tennis API v2.9.4 Account**: 
   - Sign up at https://api.api-tennis.com/
   - Obtain your API key
   - Ensure your subscription includes ITF/Challenger data

3. **Environment Variables**:
   - Set `TENNIS_API_KEY` in n8n environment variables

## Installation

### Step 1: Import Workflow

1. Open n8n interface
2. Click **Workflows** → **Import from File**
3. Select `n8n_tennis_results_workflow.json`
4. The workflow will be imported with all nodes configured

### Step 2: Configure Environment Variables

1. In n8n, go to **Settings** → **Environment Variables**
2. Add new variable:
   - **Name**: `TENNIS_API_KEY`
   - **Value**: Your Tennis API v2.9.4 API key
3. Save the environment variable

### Step 3: Verify API Endpoints

The workflow uses the following Tennis API v2.9.4 endpoints:

- `get_fixtures`: Fetches match fixtures
- `get_odds`: Fetches betting odds
- `get_H2H`: Fetches head-to-head statistics
- `get_players`: Fetches player profiles and statistics

Ensure your API subscription includes access to these endpoints.

### Step 4: Configure Schedule Trigger

The workflow includes a Schedule Trigger set to run 3 times daily:
- 07:30 (Morning scan)
- 11:30 (Midday scan)
- 15:30 (Afternoon scan)

To modify the schedule:
1. Click on the **Schedule Trigger** node
2. Adjust the trigger times in the node settings
3. Save the workflow

### Step 5: Test the Workflow

1. Click **Execute Workflow** (manual test)
2. Check the output of each node
3. Verify that:
   - Fixtures are fetched correctly
   - Odds data is retrieved
   - H2H statistics are available
   - ROI analysis is performed
   - Output is properly formatted

## Workflow Structure

```
Schedule Trigger
    ↓
Get Fixtures (HTTP Request)
    ↓
Filter Fixtures (Code Node - filters ITF/Challenger Singles)
    ↓
Split In Batches (processes matches one by one)
    ↓
    ├─→ Get Odds (HTTP Request)
    ├─→ Get H2H (HTTP Request)
    ├─→ Get Player 1 Stats (HTTP Request)
    └─→ Get Player 2 Stats (HTTP Request)
    ↓
ROI Analysis & Data Processing (Code Node)
    ↓
Format Output (Set Node)
```

## Node Descriptions

### 1. Schedule Trigger
- **Type**: Schedule Trigger
- **Function**: Activates workflow at specified times
- **Configuration**: 3 daily triggers (07:30, 11:30, 15:30)

### 2. Get Fixtures
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={{$env.TENNIS_API_KEY}}&date_start={{$now.format('YYYY-MM-DD')}}&date_stop={{$now.format('YYYY-MM-DD')}}&event_type_key=281&timezone=Europe/Helsinki`
- **Parameters**:
  - `date_start`: Today's date
  - `date_stop`: Today's date
  - `event_type_key`: 281 (Challenger Men Singles) - adjust as needed
  - `timezone`: Europe/Helsinki

### 3. Filter Fixtures
- **Type**: Code Node
- **Function**: Filters fixtures for ITF/Challenger Singles matches
- **Logic**: Removes Doubles matches, keeps only Singles

### 4. Split In Batches
- **Type**: Split In Batches
- **Function**: Processes matches one at a time
- **Batch Size**: 1

### 5. Get Odds
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://api.api-tennis.com/tennis/?method=get_odds&APIkey={{$env.TENNIS_API_KEY}}&match_key={{$json.event_key}}`

### 6. Get H2H
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://api.api-tennis.com/tennis/?method=get_H2H&APIkey={{$env.TENNIS_API_KEY}}&first_player_key={{$json.first_player_key}}&second_player_key={{$json.second_player_key}}`

### 7. Get Player Stats
- **Type**: HTTP Request (2 nodes)
- **Method**: GET
- **URL**: `https://api.api-tennis.com/tennis/?method=get_players&APIkey={{$env.TENNIS_API_KEY}}&player_key={{$json.first_player_key}}`

### 8. ROI Analysis & Data Processing
- **Type**: Code Node
- **Function**: 
  - Aggregates odds from multiple bookmakers
  - Calculates mean, median, standard deviation
  - Performs ROI analysis
  - Generates insights
- **Code**: See `n8n_function_node_code.js`

### 9. Format Output
- **Type**: Set Node
- **Function**: Structures final output
- **Output Format**:
```json
{
  "reportGenerated": "2025-01-08T12:00:00.000Z",
  "context": {
    "dateRange": "2025-01-08T12:00:00.000Z",
    "source": "API-Sports Tennis",
    "refreshPolicy": "Scheduled 3x daily"
  },
  "matches": {
    "event_key": "12345",
    "match": "Player A vs Player B",
    "score": "6-4 3-6 7-5",
    "status": "Finished",
    "odds": [...],
    "stats": {...},
    "insight": {...}
  }
}
```

## Customization

### Filtering Different Tournament Types

To filter for different event types, modify the `event_type_key` parameter in the **Get Fixtures** node:

- `281`: Challenger Men Singles
- `265`: ATP Singles
- `266`: WTA Singles
- `267`: ATP Doubles
- Check Tennis API documentation for full list

### Adjusting ROI Analysis

Modify the **ROI Analysis & Data Processing** node code to:
- Change profitability thresholds
- Adjust statistical calculations
- Add custom insights
- Include Elo ratings (see `n8n_elo_calculation.js`)

### Adding Elo Calculation

To add Elo rating calculation:

1. Add Elo calculation code to the **ROI Analysis & Data Processing** node
2. Use Static Data to store player ratings
3. Update ratings after each match
4. Include Elo data in output

See `n8n_elo_calculation.js` for implementation details.

## Output Format

The workflow generates structured JSON output with:

- **reportGenerated**: Timestamp of report generation
- **context**: Metadata about the data source
- **matches**: Array of match objects containing:
  - Match information (players, score, status)
  - Odds data (aggregated from multiple bookmakers)
  - Statistics (1st serve %, break conversions)
  - H2H data
  - **insight** object with:
    - `edgeSummary`: Statistical edge description
    - `roiEst`: ROI estimate
    - `ev`: Expected value percentage
    - `keyDrivers`: Key statistical factors
    - `riskNotes`: Risk warnings

## Troubleshooting

### API Errors

**Problem**: HTTP 401 Unauthorized
- **Solution**: Verify `TENNIS_API_KEY` is set correctly in environment variables

**Problem**: HTTP 429 Too Many Requests
- **Solution**: Add rate limiting between requests or reduce schedule frequency

**Problem**: No fixtures returned
- **Solution**: 
  - Check date range (ensure matches exist for selected date)
  - Verify `event_type_key` is correct
  - Check API subscription includes requested data

### Data Processing Errors

**Problem**: Missing odds data
- **Solution**: 
  - Verify match has odds available in API
  - Add error handling in Function Node
  - Use default values when odds unavailable

**Problem**: Statistics not extracted correctly
- **Solution**: 
  - Review actual API response structure
  - Adjust field mappings in Function Node
  - Add null checks and defaults

### Workflow Execution Issues

**Problem**: Workflow not triggering
- **Solution**: 
  - Verify Schedule Trigger is activated
  - Check n8n is running
  - Review workflow execution logs

**Problem**: Timeout errors
- **Solution**: 
  - Increase timeout settings in HTTP Request nodes
  - Reduce number of concurrent requests
  - Add retry logic

## Advanced Usage

### Integration with Notion

To save results to Notion:

1. Add **Notion** node after **Format Output**
2. Configure Notion database connection
3. Map output fields to Notion properties
4. Enable upsert to avoid duplicates

### Integration with Telegram

To send results via Telegram:

1. Add **Telegram** node after **Format Output**
2. Configure Telegram bot token
3. Format message with match insights
4. Send to specified chat/channel

### Webhook Integration

To trigger workflow via webhook:

1. Replace **Schedule Trigger** with **Webhook** node
2. Configure webhook URL
3. Accept POST requests with optional parameters
4. Use parameters to filter matches or adjust dates

## API Rate Limits

Tennis API v2.9.4 may have rate limits. Monitor:
- Requests per minute
- Requests per day
- API subscription tier limits

Adjust workflow schedule accordingly.

## Support

For issues or questions:
- Review n8n documentation: https://docs.n8n.io/
- Check Tennis API v2.9.4 documentation
- Review workflow execution logs in n8n
- Check node error messages

## License

This workflow is provided as-is for use with Tennis API v2.9.4 and n8n.

