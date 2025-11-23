# Historical Data Import

Scripts for importing historical tennis match data from various sources into Notion Match Results DB.

## Tennis-Data.co.uk Importer

Imports historical tennis match data (2000-2025) from [Tennis-Data.co.uk](http://www.tennis-data.co.uk) into Notion Match Results DB.

### Features

- **Smart Download**: Multiple download methods with automatic fallback
  - Browser-like HTTP headers (realistic User-Agent)
  - Selenium browser automation (if JavaScript required)
  - Multiple URL pattern detection
  - CSV fallback support
- Downloads Excel files (.xls) from Tennis-Data.co.uk
- Parses match data with full stats and odds (Pinnacle + Bet365)
- Maps to Match Results DB schema (50 properties)
- Duplicate detection using Match ID
- Year filtering via command-line arguments
- Progress tracking and error handling
- Rate limiting for Notion API (3 req/s)
- **Optimized Performance**: Parallel processing (2-3x faster)

### Data Included

- 105,000+ matches (2000-2025)
- ATP, WTA, ITF tournaments
- Full serve/return stats
- Pinnacle + Bet365 odds (opening + closing)
- Player rankings
- Match scores and results

### Prerequisites

1. Install dependencies:
```bash
pip install pandas openpyxl xlrd requests
```

2. Set environment variables:
```bash
export NOTION_API_KEY="your_notion_api_token"
# OR (fallback):
export NOTION_TOKEN="your_notion_api_token"
export NOTION_MATCH_RESULTS_DB_ID="your_database_id"
```

Or use `telegram_secrets.env` or `.env` file:
```
NOTION_API_KEY=your_notion_api_token
# OR (fallback):
NOTION_TOKEN=your_notion_api_token
NOTION_MATCH_RESULTS_DB_ID=your_database_id
```

**Note:** Scripts support both `NOTION_API_KEY` (preferred) and `NOTION_TOKEN` (fallback).

### Usage

#### Import single year (test):
```bash
python scripts/historical/tennis_data_uk_importer.py --years 2024
```

**Expected:**
- 2,000-3,000 matches
- ~5-8 minutes processing time (optimized with parallel processing)

#### Import multiple years:
```bash
python scripts/historical/tennis_data_uk_importer.py --years 2024 2023 2022
```

**Expected:**
- 6,000-9,000 matches
- ~15-25 minutes processing time (optimized with parallel processing)

#### With custom database ID:
```bash
python scripts/historical/tennis_data_uk_importer.py --years 2024 --db-id your_db_id
```

#### With optimized parallel processing:
```bash
# Use more workers for faster processing (default: 5)
python scripts/historical/tennis_data_uk_importer.py --years 2024 --max-workers 10
```

**Performance Optimization:**
- ✅ Parallel processing with ThreadPoolExecutor (5 workers by default)
- ✅ Connection pooling for HTTP requests
- ✅ Duplicate caching to reduce API calls
- ✅ Optimized rate limiting for Notion API
- ✅ Batch processing with concurrent API calls
- **Expected speedup: 2-3x faster** compared to sequential processing

### Field Mapping

**Tennis-Data.co.uk → Match Results DB:**

| Source Field | Target Field | Notes |
|-------------|--------------|-------|
| Date | Match Date, Result Date | |
| Player 1 / Winner | Player A | |
| Player 2 / Loser | Player B | |
| Tournament | Tournament, Tournament Tier | Auto-detected |
| Surface | Surface | Normalized (Hard/Clay/Grass/Carpet) |
| PSW / B365W | Opening Odds A | Pinnacle preferred, Bet365 backup |
| PSL / B365L | Opening Odds B | |
| Score | Actual Score | |
| Winner | Actual Winner | Player A or Player B |
| WRank / Rank1 | Rank A | |
| LRank / Rank2 | Rank B | |
| Rank Delta | Calculated | Rank A - Rank B |
| Odds Movement | Calculated | (Closing - Opening) / Opening * 100 |

### Output

The script provides:
- Progress logs to console
- Summary report per year
- Final summary with totals:
  - Total processed
  - Imported (new matches)
  - Duplicates (skipped)
  - Skipped (invalid data)
  - Errors

### File Storage

Downloaded Excel files are stored in:
```
data/historical/{year}.xls
```

Files are cached - re-running the script won't re-download existing files.

**Manual File Placement:**
If automatic download fails, you can manually download files from Tennis-Data.co.uk and place them in `data/historical/`:
```bash
# Example: Place manually downloaded file
cp ~/Downloads/2024.xls data/historical/2024.xls
python scripts/historical/tennis_data_uk_importer.py --years 2024
```

### Duplicate Detection

Matches are identified as duplicates using:
- Match ID: `td_{date}_{player_a}_{player_b}_{tournament}`
- Event ID: Same as Match ID
- Match Name: "Player A vs Player B"

If a match already exists in Notion, it will be skipped.

### Error Handling

- Invalid rows are skipped with logging
- Individual match errors don't stop the import
- Processing continues on errors
- Summary report shows all errors

### Rate Limiting

The script respects Notion API rate limits:
- 3 requests per second maximum
- Automatic rate limiting between requests
- Batch processing with delays

### Example Output

```
🎾 TENNIS-DATA.CO.UK HISTORICAL DATA IMPORTER
======================================================================
📅 Years to import: 2024, 2023, 2022
📊 Target database: Match Results DB

======================================================================
📅 Importing year: 2024
======================================================================
📁 File already exists: 2024.xls
📖 Parsing Excel file: 2024.xls
✅ Parsed 2847 rows from 2024.xls
📊 Processing 2847 rows...
  Progress: 100/2847 rows processed
  Progress: 200/2847 rows processed
  ...
======================================================================
📊 Year 2024 Summary:
  Processed: 2847
  Imported: 2653
  Duplicates: 142
  Skipped: 52
  Errors: 0
======================================================================

📊 FINAL SUMMARY
======================================================================
Total processed: 8541
✅ Imported: 7959
⏭️  Duplicates: 426
⚠️  Skipped (invalid): 156
❌ Errors: 0
⏱️  Time elapsed: 1847.3 seconds (30.8 minutes)
======================================================================
```

### Troubleshooting

**Error: "pandas not installed"**
```bash
pip install pandas openpyxl xlrd
```

**Error: "Notion client not available"**
- Check `NOTION_API_KEY` or `NOTION_TOKEN` environment variable
- Verify token has access to the database
- Scripts support both variable names (NOTION_API_KEY preferred)

**Error: "Match Results database ID not set"**
- Set `NOTION_MATCH_RESULTS_DB_ID` environment variable
- Or use `--db-id` command-line argument

**Error: "Cannot parse date"**
- Some rows may have invalid date formats
- These are automatically skipped

**Error: "Could not download file from Tennis-Data.co.uk"**
- ⚠️ **Tennis-Data.co.uk URL structure may have changed**
- The script automatically tries:
  - Multiple URL patterns
  - Browser-like HTTP headers (realistic User-Agent)
  - Selenium browser automation (if Chrome available)
  - CSV format fallback
- **Workaround**: Download files manually**
  1. Visit http://www.tennis-data.co.uk/data/
  2. Download Excel files manually for desired years
  3. Place them in `data/historical/` directory (e.g., `2024.xls`)
  4. Run the script again - it will use existing files

**Selenium Browser Automation:**
- Automatically used if Chrome/ChromeDriver is available
- Helps with JavaScript-rendered pages
- Uses headless mode (no visible browser window)
- Falls back to HTTP requests if Selenium unavailable
- Requires: `selenium` and `webdriver-manager` packages (already in requirements.txt)

**Alternative Data Sources:**
If Tennis-Data.co.uk is unavailable, consider:
- **Tennis Abstract**: https://www.tennisabstract.com/ (detailed match stats)
- **ATP/WTA Official Sites**: Tournament results and statistics
- **FlashScore/TennisExplorer**: Historical match data via scraping

**Performance:**
- Optimized with parallel processing (2-3x faster than before)
- **Auto-detects CPU cores** and optimizes worker count automatically
- Default: 5 parallel workers (adjustable with `--max-workers`)
- **Mac Mini optimized**: Automatically uses 5-8 workers based on CPU count
- Rate limiting ensures Notion API compliance (3 req/s)
- Progress updates every 100 rows
- Connection pooling reduces network overhead
- Duplicate caching minimizes redundant API calls

**Mac Mini Performance Tips:**
- ✅ System auto-detects CPU cores and sets optimal workers
- ✅ Default settings work well for 4-8 core Mac Mini
- ✅ For faster processing: `--max-workers 8` (if you have 8+ cores)
- ✅ For stability: `--max-workers 5` (conservative, uses less memory)
- ✅ Monitor Activity Monitor during import to check CPU/memory usage

### Next Steps

After importing historical data:

1. **Validate data quality:**
   - Check Match Results DB in Notion
   - Verify field mappings
   - Review any skipped/invalid rows

2. **Use for ML training:**
   - Historical data provides baseline for ML models
   - 500+ matches minimum for XGBoost training
   - Self-Learning Engine can use this data

3. **Pattern validation:**
   - Compare historical patterns with current system
   - Validate ROI calculations
   - Identify profitable strategies

### Related Documentation

- [Match Results DB Schema](../../tennis_ai/MATCH_RESULTS_DB_SCHEMA.md)
- [Match Results Logger](../../../src/notion/match_results_logger.py)
- [ML Engine README](../../tennis_ai/ML_ENGINE_README.md)


