#!/usr/bin/env python3
"""
Basic Test Script for N8N-Style Web Scraper

Tests the core functionality without external dependencies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the n8n_scraper module to path
sys.path.insert(0, str(Path(__file__).parent))

from workflows.workflow_engine import WorkflowManager
from config.workflow_config import WorkflowConfig, WorkflowNodeConfig, WorkflowConnectionConfig


async def test_basic_workflow():
    """Test a basic workflow with mock data"""
    print("🧪 Testing Basic Workflow Functionality")
    print("=" * 50)

    # Create a simple test workflow
    workflow_config = WorkflowConfig(
        id="test_workflow",
        name="Test Workflow",
        description="Basic functionality test",
        nodes=[
            WorkflowNodeConfig(
                id="mock_scraper",
                type="webScraper",
                name="Mock Web Scraper",
                parameters={
                    "urls": ["https://httpbin.org/html"],
                    "selectors": {"content": "body"},
                    "max_pages": 1,
                    "rate_limit": 1.0
                }
            ),
            WorkflowNodeConfig(
                id="mock_filter",
                type="dataFilter",
                name="Mock Data Filter",
                parameters={
                    "min_length": 10,
                    "remove_duplicates": True
                }
            )
        ],
        connections=[
            WorkflowConnectionConfig("mock_scraper", "data", "mock_filter", "data")
        ]
    )

    # Initialize workflow manager
    manager = WorkflowManager()

    try:
        # Load workflow
        workflow_id = manager.load_workflow(workflow_config.to_dict())
        print(f"✅ Workflow loaded: {workflow_id}")

        # Get workflow status
        status = manager.get_workflow_status(workflow_id)
        print(f"✅ Workflow status: {status['is_running']}")

        # List workflows
        workflows = manager.list_workflows()
        print(f"✅ Available workflows: {len(workflows)}")

        print("✅ Basic workflow functionality test passed!")
        return True

    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_node_imports():
    """Test that all nodes can be imported"""
    print("\n🧪 Testing Node Imports")
    print("=" * 50)

    try:
        from nodes.base_node import BaseNode, SourceNode, DataNode
        print("✅ Base nodes imported")

        from nodes.web_scraper_node import WebScraperNode
        print("✅ WebScraperNode imported")

        from nodes.telegram_scraper_node import TelegramScraperNode
        print("✅ TelegramScraperNode imported")

        from nodes.discord_scraper_node import DiscordScraperNode
        print("✅ DiscordScraperNode imported")

        from nodes.data_filter_node import DataFilterNode
        print("✅ DataFilterNode imported")

        from nodes.data_transformer_node import DataTransformerNode
        print("✅ DataTransformerNode imported")

        from nodes.database_storage_node import DatabaseStorageNode
        print("✅ DatabaseStorageNode imported")

        print("✅ All node imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Node import failed: {e}")
        return False


async def test_config_validation():
    """Test workflow configuration validation"""
    print("\n🧪 Testing Configuration Validation")
    print("=" * 50)

    try:
        from config.workflow_config import WorkflowConfigValidator

        # Valid config
        valid_config = {
            "id": "test",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "webScraper",
                    "parameters": {"urls": ["https://example.com"]}
                }
            ]
        }

        errors = WorkflowConfigValidator.validate_workflow(valid_config)
        if not errors:
            print("✅ Valid configuration accepted")
        else:
            print(f"❌ Valid config rejected: {errors}")
            return False

        # Invalid config (missing required fields)
        invalid_config = {
            "name": "Test Workflow",
            "nodes": []
        }

        errors = WorkflowConfigValidator.validate_workflow(invalid_config)
        if errors:
            print("✅ Invalid configuration properly rejected")
        else:
            print("❌ Invalid config incorrectly accepted")
            return False

        print("✅ Configuration validation test passed!")
        return True

    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


async def test_workflow_creation():
    """Test programmatic workflow creation"""
    print("\n🧪 Testing Programmatic Workflow Creation")
    print("=" * 50)

    try:
        from config.workflow_config import create_web_scraper_workflow

        workflow = create_web_scraper_workflow(
            name="Test Scraper",
            urls=["https://example.com"],
            database_config={"db_type": "sqlite", "connection_string": "test.db"}
        )

        if workflow.id and workflow.name and len(workflow.nodes) > 0:
            print("✅ Programmatic workflow creation successful")
            print(f"   Workflow: {workflow.name}")
            print(f"   Nodes: {len(workflow.nodes)}")
            print(f"   Connections: {len(workflow.connections)}")
        else:
            print("❌ Workflow creation failed - missing required fields")
            return False

        print("✅ Programmatic workflow creation test passed!")
        return True

    except Exception as e:
        print(f"❌ Programmatic workflow creation test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🎯 N8N-Style Web Scraper - Basic Tests")
    print("=" * 60)

    tests = [
        ("Node Imports", test_node_imports),
        ("Basic Workflow", test_basic_workflow),
        ("Configuration Validation", test_config_validation),
        ("Workflow Creation", test_workflow_creation)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*10} {test_name} {'='*10}")
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The N8N-style scraper core is working correctly.")
        print("\nNext steps:")
        print("1. Configure API keys for Telegram/Discord scraping")
        print("2. Test with real websites (respect terms of service)")
        print("3. Create custom workflows for your specific needs")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)