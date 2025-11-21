#!/usr/bin/env python3
"""
Python Example: Using N8N-Style Web Scraper Programmatically

This example demonstrates how to create and execute workflows using Python code
instead of JSON configuration files.
"""

import asyncio
import logging
from datetime import datetime

from ..workflows.workflow_engine import WorkflowManager
from ..config.workflow_config import (
    WorkflowConfig, WorkflowNodeConfig, WorkflowConnectionConfig,
    create_web_scraper_workflow, create_social_media_workflow
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_web_scraper_workflow():
    """Example: Create and execute a web scraper workflow programmatically"""
    print("🌐 Web Scraper Workflow Example")
    print("=" * 50)

    # Create workflow configuration
    workflow_config = create_web_scraper_workflow(
        name="Tennis Forum Scraper",
        urls=[
            "https://tennis-forum.example.com/matches",
            "https://betting-discussion.example.com/tennis"
        ],
        database_config={
            "db_type": "sqlite",
            "connection_string": "tennis_forum_data.db",
            "table_name": "forum_posts"
        }
    )

    # Initialize workflow manager
    manager = WorkflowManager()
    workflow_id = manager.load_workflow(workflow_config.to_dict())

    print(f"✅ Loaded workflow: {workflow_id}")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await manager.execute_workflow(workflow_id)

    if result['success']:
        print("✅ Workflow completed successfully!"        print(f"   Execution time: {result['execution_time']:.2f}s")
        print(f"   Nodes executed: {result['completed_nodes']}/{result['total_nodes']}")

        # Show node results
        node_results = result.get('node_results', {})
        for node_id, node_result in node_results.items():
            if node_result.get('success'):
                print(f"   ✅ {node_id}: {node_result.get('metadata', {}).get('total_items', 0)} items processed")
            else:
                print(f"   ❌ {node_id}: {node_result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")

    return result


async def example_social_media_workflow():
    """Example: Create and execute a social media monitoring workflow"""
    print("\n📱 Social Media Monitoring Workflow Example")
    print("=" * 50)

    # Create workflow configuration
    workflow_config = create_social_media_workflow(
        name="Tennis Intelligence Monitor",
        telegram_channels=["@TennisTipsChannel", "@BettingInsider"],
        discord_servers=["TennisBettingServer"],
        database_config={
            "db_type": "sqlite",
            "connection_string": "tennis_intelligence.db",
            "table_name": "intelligence_data"
        }
    )

    # Initialize workflow manager
    manager = WorkflowManager()
    workflow_id = manager.load_workflow(workflow_config.to_dict())

    print(f"✅ Loaded workflow: {workflow_id}")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await manager.execute_workflow(workflow_id)

    if result['success']:
        print("✅ Workflow completed successfully!"        print(f"   Execution time: {result['execution_time']:.2f}s")
        print(f"   Nodes executed: {result['completed_nodes']}/{result['total_nodes']}")

        # Show intelligence summary
        node_results = result.get('node_results', {})
        for node_id, node_result in node_results.items():
            if 'scraper' in node_id and node_result.get('success'):
                metadata = node_result.get('metadata', {})
                messages = metadata.get('total_messages', 0)
                print(f"   📊 {node_id}: {messages} messages collected")
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")

    return result


async def example_custom_workflow():
    """Example: Create a custom workflow with specific node configurations"""
    print("\n🔧 Custom Workflow Example")
    print("=" * 50)

    # Create custom workflow configuration
    workflow_config = WorkflowConfig(
        id="custom_tennis_analyzer",
        name="Custom Tennis Analysis Workflow",
        description="Analyze tennis discussions from multiple sources",
        nodes=[
            # Web scraper for tennis forums
            WorkflowNodeConfig(
                id="forum_scraper",
                type="webScraper",
                name="Tennis Forum Scraper",
                parameters={
                    "urls": ["https://tennis-forum.example.com"],
                    "selectors": {
                        "posts": ".post-content",
                        "threads": ".thread-title"
                    },
                    "max_pages": 3,
                    "rate_limit": 2.0
                }
            ),

            # Telegram scraper for tipster channels
            WorkflowNodeConfig(
                id="telegram_tips",
                type="telegramScraper",
                name="Telegram Tipsters",
                parameters={
                    "channels": ["@TennisProTips"],
                    "max_messages": 50,
                    "keywords": ["ATP", "WTA", "tennis"]
                }
            ),

            # Data merger
            WorkflowNodeConfig(
                id="data_merge",
                type="dataTransformer",
                name="Data Merger",
                parameters={
                    "transformations": ["merge_sources", "lowercase"],
                    "generate_summaries": True
                }
            ),

            # Quality filter
            WorkflowNodeConfig(
                id="quality_filter",
                type="dataFilter",
                name="Quality Filter",
                parameters={
                    "min_length": 25,
                    "include_keywords": ["match", "player", "tournament"],
                    "exclude_keywords": ["spam", "fake"]
                }
            ),

            # Database storage
            WorkflowNodeConfig(
                id="db_store",
                type="databaseStorage",
                name="Database Storage",
                parameters={
                    "db_type": "sqlite",
                    "connection_string": "tennis_analysis.db",
                    "table_name": "tennis_discussions"
                }
            )
        ],
        connections=[
            WorkflowConnectionConfig("forum_scraper", "data", "data_merge", "input_1"),
            WorkflowConnectionConfig("telegram_tips", "data", "data_merge", "input_2"),
            WorkflowConnectionConfig("data_merge", "processed_data", "quality_filter", "data"),
            WorkflowConnectionConfig("quality_filter", "processed_data", "db_store", "data")
        ]
    )

    # Initialize and execute
    manager = WorkflowManager()
    workflow_id = manager.load_workflow(workflow_config.to_dict())

    print(f"✅ Loaded custom workflow: {workflow_id}")

    result = await manager.execute_workflow(workflow_id)

    if result['success']:
        print("✅ Custom workflow completed!"        print(f"   Total execution time: {result['execution_time']:.2f}s")

        # Show detailed results
        node_results = result.get('node_results', {})
        for node_id, node_result in node_results.items():
            status = "✅" if node_result.get('success') else "❌"
            metadata = node_result.get('metadata', {})
            items = metadata.get('total_items', metadata.get('stored_count', 0))
            print(f"   {status} {node_id}: {items} items")
    else:
        print(f"❌ Custom workflow failed: {result.get('error')}")

    return result


async def example_workflow_from_json():
    """Example: Load and execute workflow from JSON file"""
    print("\n📄 JSON Workflow Example")
    print("=" * 50)

    try:
        manager = WorkflowManager()
        workflow_id = manager.load_workflow_from_file(
            "src/scrapers/n8n_scraper/examples/workflows/web_scraper_example.json"
        )

        print(f"✅ Loaded workflow from JSON: {workflow_id}")

        # Execute with custom trigger data
        trigger_data = {
            "custom_urls": ["https://additional-forum.example.com"],
            "priority": "high"
        }

        result = await manager.execute_workflow(workflow_id, trigger_data)

        if result['success']:
            print("✅ JSON workflow executed successfully!"        else:
            print(f"❌ JSON workflow failed: {result.get('error')}")

        return result

    except FileNotFoundError:
        print("❌ JSON workflow file not found")
        return None
    except Exception as e:
        print(f"❌ Error loading JSON workflow: {e}")
        return None


async def main():
    """Run all examples"""
    print("🎯 N8N-Style Web Scraper - Python Examples")
    print("=" * 60)

    examples = [
        ("Web Scraper Workflow", example_web_scraper_workflow),
        ("Social Media Workflow", example_social_media_workflow),
        ("Custom Workflow", example_custom_workflow),
        ("JSON Workflow", example_workflow_from_json)
    ]

    results = []

    for name, example_func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            result = await example_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")
            results.append((name, None))

    # Summary
    print("\n" + "="*60)
    print("📊 EXECUTION SUMMARY")
    print("="*60)

    successful = 0
    for name, result in results:
        if result and result.get('success'):
            successful += 1
            print(f"✅ {name}: SUCCESS")
        else:
            print(f"❌ {name}: FAILED")

    print(f"\n🎯 {successful}/{len(results)} examples completed successfully")

    if successful == len(results):
        print("\n🎉 All examples completed! Your N8N-style scraper is ready to use.")
        print("\nNext steps:")
        print("1. Configure your API keys for Telegram/Discord")
        print("2. Create custom workflows for your specific needs")
        print("3. Set up scheduled execution with cron jobs")
        print("4. Monitor workflow performance and adjust configurations")


if __name__ == "__main__":
    asyncio.run(main())