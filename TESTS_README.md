# 🧪 Test Documentation

## Test Files

### 1. `test_itf_rankings_scraper.py`
Unit tests for the ITF Rankings Scraper:
- Tests scraping logic (with mocked Playwright)
- Tests Notion API updates (with mocked Client)
- Tests data parsing and validation
- Tests error handling

**Run:**
```bash
python3 test_itf_rankings_scraper.py
```

### 2. `test_match_history_scraper.py`
Unit tests for the Match History Scraper:
- Tests FlashScore scraping logic (with mocked Playwright)
- Tests Notion API queries and updates (with mocked Client)
- Tests win rate calculation
- Tests recent form formatting

**Run:**
```bash
python3 test_match_history_scraper.py
```

### 3. `test_scrapers_summary.py`
Simplified integration tests:
- Tests that scrapers can be imported
- Tests data structure validation
- Tests calculation logic (win rate, form formatting)
- Tests name parsing logic

**Run:**
```bash
python3 test_scrapers_summary.py
```

## Test Coverage

### ITF Rankings Scraper
- ✅ Module imports
- ✅ Data structure validation
- ✅ Name parsing and cleaning
- ✅ Scraping function structure
- ✅ Update function structure

### Match History Scraper
- ✅ Module imports
- ✅ Data structure validation
- ✅ Win rate calculation
- ✅ Recent form formatting
- ✅ Scraping function structure
- ✅ Update function structure

## Running All Tests

```bash
# Run all scraper tests
python3 test_scrapers_summary.py
python3 test_itf_rankings_scraper.py
python3 test_match_history_scraper.py
```

## Requirements for Full Tests

For full integration tests (with real API calls), you need:

1. **Dependencies:**
   ```bash
   pip install playwright notion-client
   playwright install chromium
   ```

2. **Environment Variables:**
   - `NOTION_API_KEY` - Notion API token
   - `PLAYER_CARDS_DB_ID` - Player Cards database ID

3. **Test Configuration:**
   - Set `HEADLESS=false` to see browser during tests
   - Ensure network access for Playwright

## Test Strategy

### Unit Tests (Mocked)
- Use `unittest.mock` to mock external dependencies
- Test logic without real API calls or browser automation
- Fast execution, no external dependencies

### Integration Tests (Real)
- Test with real Playwright browser
- Test with real Notion API
- Require environment setup
- Slower execution

## CI/CD Integration

Tests are designed to run in GitHub Actions:
- Unit tests run without external dependencies
- Integration tests require secrets (NOTION_API_KEY, PLAYER_CARDS_DB_ID)
- Playwright browsers installed automatically in CI

## Notes

- Mock tests may show warnings about missing dependencies (expected)
- Full integration tests require actual credentials
- Test failures in CI should be investigated before deployment

