# 🎯 N8N-Style Web Scraper

A modular, workflow-based web scraping system inspired by n8n. Collect data from websites, forums, Telegram groups, and Discord servers using configurable workflows.

## ✨ Features

- **Modular Architecture**: n8n-style nodes for different data sources
- **Workflow Engine**: Visual workflow creation with data flow between nodes
- **Multiple Data Sources**: Web scraping, Telegram, Discord, and more
- **Data Processing**: Filter, transform, and store collected data
- **Anti-Detection**: Built-in measures to avoid blocking
- **Database Integration**: Store data in SQLite, PostgreSQL, or MongoDB
- **Configuration Options**: JSON configs, Python API, or CLI

## 🚀 Quick Start

### 1. Installation

```bash
# Install required dependencies
pip install aiohttp beautifulsoup4 selenium requests

# Optional: For Telegram scraping
pip install telethon

# Optional: For Discord scraping
pip install discord.py

# Optional: For advanced databases
pip install psycopg2-binary pymongo
```

### 2. Basic Usage

#### Using Python API

```python
import asyncio
from n8n_scraper import WorkflowManager
from n8n_scraper.config import create_web_scraper_workflow

async def main():
    # Create a web scraper workflow
    workflow_config = create_web_scraper_workflow(
        name="My Forum Scraper",
        urls=["https://example-forum.com"],
        database_config={
            "db_type": "sqlite",
            "connection_string": "forum_data.db"
        }
    )

    # Execute workflow
    manager = WorkflowManager()
    workflow_id = manager.load_workflow(workflow_config.to_dict())
    result = await manager.execute_workflow(workflow_id)

    print(f"Workflow completed: {result['success']}")

asyncio.run(main())
```

#### Using CLI

```bash
# Create a new workflow
python -m n8n_scraper.cli create-workflow web "My Forum Scraper"

# Edit the generated workflow file
# Then run it
python -m n8n_scraper.cli run-workflow workflows/my_forum_scraper.json

# List available workflows
python -m n8n_scraper.cli list-workflows
```

#### Using JSON Configuration

```json
{
  "id": "web_scraper_example",
  "name": "Web Scraper Workflow",
  "nodes": [
    {
      "id": "web_scraper_1",
      "type": "webScraper",
      "parameters": {
        "urls": ["https://example.com"],
        "selectors": {"content": ".post"}
      }
    },
    {
      "id": "db_storage_1",
      "type": "databaseStorage",
      "parameters": {
        "db_type": "sqlite",
        "connection_string": "data.db"
      }
    }
  ],
  "connections": [
    {
      "from": "web_scraper_1",
      "fromOutput": "data",
      "to": "db_storage_1",
      "toInput": "data"
    }
  ]
}
```

## 🏗️ Architecture

### Node Types

#### Source Nodes (Data Generators)
- **WebScraperNode**: Scrapes websites and forums
- **TelegramScraperNode**: Collects messages from Telegram channels
- **DiscordScraperNode**: Monitors Discord servers and channels

#### Processing Nodes (Data Transformers)
- **DataFilterNode**: Filters and cleans data
- **DataTransformerNode**: Transforms data formats and structure

#### Storage Nodes (Data Sinks)
- **DatabaseStorageNode**: Stores data in databases

### Workflow Engine

The workflow engine orchestrates node execution in topological order, ensuring proper data flow between connected nodes.

## 📖 Node Reference

### WebScraperNode

Scrapes text content from websites.

**Parameters:**
- `urls`: List of URLs to scrape
- `selectors`: CSS selectors for content extraction
- `max_pages`: Maximum pages to scrape
- `rate_limit`: Requests per second
- `use_browser`: Use Selenium instead of requests
- `anti_detection`: Enable anti-detection measures

### TelegramScraperNode

Collects messages from Telegram channels.

**Parameters:**
- `channels`: List of Telegram channel usernames
- `api_id`: Telegram API ID
- `api_hash`: Telegram API hash
- `phone_number`: Phone number for authentication
- `max_messages`: Maximum messages per channel
- `hours_back`: Hours to look back

### DiscordScraperNode

Monitors Discord servers.

**Parameters:**
- `servers`: List of Discord server names
- `channels`: List of channel names
- `bot_token`: Discord bot token
- `max_messages`: Maximum messages per channel

### DataFilterNode

Filters and cleans scraped data.

**Parameters:**
- `min_length`: Minimum content length
- `include_keywords`: Keywords that must be present
- `exclude_keywords`: Keywords to filter out
- `remove_duplicates`: Remove duplicate content

### DataTransformerNode

Transforms data structure and format.

**Parameters:**
- `transformations`: List of transformations to apply
- `field_mappings`: Field renaming mappings
- `output_format`: Output format (json, csv, xml)

### DatabaseStorageNode

Stores data in databases.

**Parameters:**
- `db_type`: Database type (sqlite, postgresql, mongodb)
- `connection_string`: Database connection string
- `table_name`: Table/collection name
- `batch_size`: Batch insert size

## 🔧 Configuration

### Environment Variables

```bash
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=+1234567890

# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token
```

### Workflow Settings

```json
{
  "settings": {
    "max_execution_time": 300,
    "retry_failed_nodes": true
  }
}
```

## 📊 Monitoring & Logging

The system provides comprehensive logging and monitoring:

- Execution times for each node
- Success/failure rates
- Data collection statistics
- Error tracking and retry logic

## 🛠️ Development

### Adding New Nodes

1. Create a new node class inheriting from `BaseNode`
2. Implement required methods: `inputs`, `outputs`, `execute`
3. Add node type to `WorkflowEngine._get_node_class()`
4. Update imports in `__init__.py`

### Testing

```bash
# Run examples
python examples/python_workflow_example.py

# Test individual nodes
python -c "from n8n_scraper.nodes import WebScraperNode; print('Import successful')"
```

## 📝 Examples

See the `examples/` directory for:
- JSON workflow configurations
- Python API usage examples
- CLI usage examples

## ⚠️ Legal & Ethical Considerations

- Respect website terms of service
- Use appropriate rate limiting
- Obtain necessary permissions for private channels
- Comply with data protection regulations
- Use for legitimate research and analysis purposes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for data collection and analysis workflows**