#!/usr/bin/env python3
"""
Command Line Interface for N8N-Style Web Scraper

Usage:
    python -m n8n_scraper.cli run-workflow <workflow_file.json>
    python -m n8n_scraper.cli list-workflows
    python -m n8n_scraper.cli create-workflow <type> <name>
    python -m n8n_scraper.cli validate-workflow <workflow_file.json>
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any

from .workflows.workflow_engine import WorkflowManager
from .config.workflow_config import (
    WorkflowConfigManager, create_web_scraper_workflow,
    create_social_media_workflow, WorkflowConfigValidator
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class N8NScraperCLI:
    """Command line interface for the N8N-style scraper"""

    def __init__(self):
        self.workflow_manager = WorkflowManager()
        self.config_manager = WorkflowConfigManager()

    async def run_workflow(self, workflow_file: str, trigger_data: Dict[str, Any] = None) -> None:
        """Run a workflow from JSON file"""
        try:
            # Load workflow
            workflow_id = self.workflow_manager.load_workflow_from_file(workflow_file)
            workflow = self.workflow_manager.workflows[workflow_id]

            print(f"🚀 Executing workflow: {workflow.name}")
            print(f"   Description: {workflow.config.get('description', 'No description')}")
            print(f"   Nodes: {len(workflow.nodes)}")
            print(f"   Connections: {len(workflow.connections)}")
            print()

            # Execute workflow
            result = await self.workflow_manager.execute_workflow(workflow_id, trigger_data)

            # Display results
            if result['success']:
                print("✅ Workflow completed successfully!")
                print(".2f"                print(f"   Nodes executed: {result['completed_nodes']}/{result['total_nodes']}")

                # Show node results
                node_results = result.get('node_results', {})
                print("\n📊 Node Results:")
                for node_id, node_result in node_results.items():
                    status = "✅" if node_result.get('success') else "❌"
                    execution_time = node_result.get('execution_time', 0)
                    metadata = node_result.get('metadata', {})

                    items_processed = (
                        metadata.get('total_items') or
                        metadata.get('stored_count') or
                        metadata.get('message_count') or
                        0
                    )

                    print(".2f"
                # Show workflow summary
                print("
📈 Workflow Summary:"                total_scraped = sum(
                    node_result.get('metadata', {}).get('total_items', 0)
                    for node_result in node_results.values()
                    if node_result.get('success')
                )
                total_stored = sum(
                    node_result.get('metadata', {}).get('stored_count', 0)
                    for node_result in node_results.values()
                    if node_result.get('success')
                )

                print(f"   Total items scraped: {total_scraped}")
                print(f"   Total items stored: {total_stored}")

            else:
                print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Failed to run workflow: {e}")
            sys.exit(1)

    def list_workflows(self) -> None:
        """List available workflow configurations"""
        workflows = self.config_manager.list_workflows()

        if not workflows:
            print("No workflow configurations found.")
            return

        print("📋 Available Workflows:")
        print("-" * 60)

        for workflow in workflows:
            print(f"ID: {workflow['id']}")
            print(f"Name: {workflow['name']}")
            print(f"Description: {workflow.get('description', 'No description')}")
            print(f"Nodes: {workflow['node_count']}")
            print(f"Connections: {workflow['connection_count']}")
            print(f"File: {workflow['filepath']}")
            print("-" * 60)

    def create_workflow(self, workflow_type: str, name: str) -> None:
        """Create a new workflow configuration"""
        try:
            if workflow_type == "web":
                workflow_config = create_web_scraper_workflow(
                    name=name,
                    urls=["https://example-forum.com"],
                    database_config={
                        "db_type": "sqlite",
                        "connection_string": f"{name.lower().replace(' ', '_')}.db"
                    }
                )
            elif workflow_type == "social":
                workflow_config = create_social_media_workflow(
                    name=name,
                    telegram_channels=["@YourChannel"],
                    discord_servers=["YourServer"],
                    database_config={
                        "db_type": "sqlite",
                        "connection_string": f"{name.lower().replace(' ', '_')}_social.db"
                    }
                )
            else:
                print(f"❌ Unknown workflow type: {workflow_type}")
                print("Available types: web, social")
                sys.exit(1)

            # Save workflow
            filename = self.config_manager.save_workflow(workflow_config)
            print(f"✅ Created workflow: {name}")
            print(f"   File: {filename}")
            print("\n📝 Next steps:")
            print("1. Edit the workflow configuration file")
            print("2. Add your actual URLs/channels")
            print("3. Configure API keys if needed")
            print("4. Run with: python -m n8n_scraper.cli run-workflow <filename>")

        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            sys.exit(1)

    def validate_workflow(self, workflow_file: str) -> None:
        """Validate a workflow configuration file"""
        try:
            errors = self.config_manager.validate_workflow_file(Path(workflow_file).stem)

            if not errors:
                print("✅ Workflow configuration is valid!")
                return

            print("❌ Workflow configuration has errors:")
            for error in errors:
                print(f"   - {error}")

            sys.exit(1)

        except Exception as e:
            logger.error(f"Failed to validate workflow: {e}")
            sys.exit(1)

    def show_help(self) -> None:
        """Show help information"""
        print("🎯 N8N-Style Web Scraper CLI")
        print("=" * 40)
        print()
        print("USAGE:")
        print("  python -m n8n_scraper.cli <command> [options]")
        print()
        print("COMMANDS:")
        print("  run-workflow <file.json>    Run a workflow from JSON file")
        print("  list-workflows              List available workflow configurations")
        print("  create-workflow <type> <name>  Create a new workflow")
        print("  validate-workflow <file.json> Validate workflow configuration")
        print("  help                        Show this help message")
        print()
        print("WORKFLOW TYPES:")
        print("  web     - Web scraper workflow")
        print("  social  - Social media monitoring workflow")
        print()
        print("EXAMPLES:")
        print("  python -m n8n_scraper.cli create-workflow web 'My Forum Scraper'")
        print("  python -m n8n_scraper.cli run-workflow workflows/my_workflow.json")
        print("  python -m n8n_scraper.cli validate-workflow workflows/my_workflow.json")


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        N8NScraperCLI().show_help()
        sys.exit(1)

    command = sys.argv[1]
    cli = N8NScraperCLI()

    try:
        if command == "run-workflow":
            if len(sys.argv) < 3:
                print("❌ Missing workflow file argument")
                sys.exit(1)

            workflow_file = sys.argv[2]
            trigger_data = None

            # Check for additional trigger data
            if len(sys.argv) > 3:
                try:
                    trigger_data = json.loads(sys.argv[3])
                except json.JSONDecodeError:
                    print("❌ Invalid JSON trigger data")
                    sys.exit(1)

            await cli.run_workflow(workflow_file, trigger_data)

        elif command == "list-workflows":
            cli.list_workflows()

        elif command == "create-workflow":
            if len(sys.argv) < 4:
                print("❌ Missing workflow type or name arguments")
                sys.exit(1)

            workflow_type = sys.argv[2]
            name = sys.argv[3]
            cli.create_workflow(workflow_type, name)

        elif command == "validate-workflow":
            if len(sys.argv) < 3:
                print("❌ Missing workflow file argument")
                sys.exit(1)

            workflow_file = sys.argv[2]
            cli.validate_workflow(workflow_file)

        elif command in ["help", "-h", "--help"]:
            cli.show_help()

        else:
            print(f"❌ Unknown command: {command}")
            print("Run 'python -m n8n_scraper.cli help' for usage information")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())