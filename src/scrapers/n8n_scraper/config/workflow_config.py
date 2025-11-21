#!/usr/bin/env python3
"""
Workflow Configuration System

This module handles workflow configuration validation and management,
supporting both JSON configurations and programmatic workflow creation.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import jsonschema
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WorkflowNodeConfig:
    """Configuration for a single workflow node"""
    id: str
    type: str
    name: str
    parameters: Dict[str, Any]
    position: Optional[Dict[str, float]] = None  # For UI positioning

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowConnectionConfig:
    """Configuration for a workflow connection"""
    from_node: str
    from_output: str
    to_node: str
    to_input: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'from': self.from_node,
            'fromOutput': self.from_output,
            'to': self.to_node,
            'toInput': self.to_input
        }


@dataclass
class WorkflowConfig:
    """Complete workflow configuration"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNodeConfig] = None
    connections: List[WorkflowConnectionConfig] = None
    settings: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
        if self.connections is None:
            self.connections = []
        if self.settings is None:
            self.settings = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'nodes': [node.to_dict() for node in self.nodes],
            'connections': [conn.to_dict() for conn in self.connections],
            'settings': self.settings,
            'metadata': self.metadata
        }


class WorkflowConfigValidator:
    """Validates workflow configurations"""

    # JSON Schema for workflow configuration
    WORKFLOW_SCHEMA = {
        "type": "object",
        "required": ["id", "name", "nodes"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "type"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string"},
                        "name": {"type": "string"},
                        "parameters": {"type": "object"},
                        "position": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"}
                            }
                        }
                    }
                }
            },
            "connections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["from", "fromOutput", "to", "toInput"],
                    "properties": {
                        "from": {"type": "string"},
                        "fromOutput": {"type": "string"},
                        "to": {"type": "string"},
                        "toInput": {"type": "string"}
                    }
                }
            },
            "settings": {"type": "object"},
            "metadata": {"type": "object"}
        }
    }

    # Node type schemas
    NODE_SCHEMAS = {
        "webScraper": {
            "type": "object",
            "properties": {
                "urls": {"type": "array", "items": {"type": "string"}},
                "selectors": {"type": "object"},
                "max_pages": {"type": "integer", "minimum": 1},
                "rate_limit": {"type": "number", "minimum": 0.1},
                "use_browser": {"type": "boolean"},
                "anti_detection": {"type": "boolean"}
            }
        },
        "telegramScraper": {
            "type": "object",
            "properties": {
                "channels": {"type": "array", "items": {"type": "string"}},
                "api_id": {"type": "string"},
                "api_hash": {"type": "string"},
                "max_messages": {"type": "integer", "minimum": 1},
                "hours_back": {"type": "integer", "minimum": 1}
            }
        },
        "discordScraper": {
            "type": "object",
            "properties": {
                "servers": {"type": "array", "items": {"type": "string"}},
                "channels": {"type": "array", "items": {"type": "string"}},
                "token": {"type": "string"},
                "max_messages": {"type": "integer", "minimum": 1},
                "hours_back": {"type": "integer", "minimum": 1}
            }
        },
        "dataFilter": {
            "type": "object",
            "properties": {
                "filters": {"type": "object"},
                "remove_duplicates": {"type": "boolean"},
                "min_length": {"type": "integer", "minimum": 0}
            }
        },
        "dataTransformer": {
            "type": "object",
            "properties": {
                "transformations": {"type": "array"},
                "output_format": {"type": "string"}
            }
        },
        "databaseStorage": {
            "type": "object",
            "properties": {
                "connection_string": {"type": "string"},
                "table_name": {"type": "string"},
                "batch_size": {"type": "integer", "minimum": 1},
                "on_conflict": {"type": "string", "enum": ["update", "ignore", "error"]}
            }
        }
    }

    @classmethod
    def validate_workflow(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate complete workflow configuration

        Args:
            config: Workflow configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Validate overall structure
            jsonschema.validate(config, cls.WORKFLOW_SCHEMA)
        except jsonschema.ValidationError as e:
            errors.append(f"Workflow structure error: {e.message}")
            return errors

        # Validate individual nodes
        for node in config.get('nodes', []):
            node_errors = cls.validate_node(node)
            errors.extend(node_errors)

        # Validate connections
        connection_errors = cls.validate_connections(config)
        errors.extend(connection_errors)

        return errors

    @classmethod
    def validate_node(cls, node: Dict[str, Any]) -> List[str]:
        """Validate individual node configuration"""
        errors = []

        node_type = node.get('type')
        if not node_type:
            errors.append(f"Node {node.get('id', 'unknown')} missing type")
            return errors

        if node_type not in cls.NODE_SCHEMAS:
            errors.append(f"Unknown node type: {node_type}")
            return errors

        parameters = node.get('parameters', {})

        try:
            jsonschema.validate(parameters, cls.NODE_SCHEMAS[node_type])
        except jsonschema.ValidationError as e:
            errors.append(f"Node {node.get('id', node_type)} parameter error: {e.message}")

        return errors

    @classmethod
    def validate_connections(cls, config: Dict[str, Any]) -> List[str]:
        """Validate workflow connections"""
        errors = []
        nodes = {node['id']: node for node in config.get('nodes', [])}
        connections = config.get('connections', [])

        for conn in connections:
            from_node = conn.get('from')
            to_node = conn.get('to')
            from_output = conn.get('fromOutput')
            to_input = conn.get('toInput')

            # Check if nodes exist
            if from_node not in nodes:
                errors.append(f"Connection references unknown source node: {from_node}")
            if to_node not in nodes:
                errors.append(f"Connection references unknown target node: {to_node}")
                continue

            # Validate input/output compatibility (basic check)
            if from_node in nodes and to_node in nodes:
                # This would be expanded with actual node interface checking
                pass

        return errors


class WorkflowConfigManager:
    """Manages workflow configurations"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / 'workflows'
        self.config_dir.mkdir(exist_ok=True)

    def save_workflow(self, config: WorkflowConfig, filename: Optional[str] = None) -> str:
        """Save workflow configuration to file"""
        if filename is None:
            filename = f"{config.id}.json"

        filepath = self.config_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Saved workflow '{config.name}' to {filepath}")
        return str(filepath)

    def load_workflow(self, workflow_id: str) -> WorkflowConfig:
        """Load workflow configuration from file"""
        filepath = self.config_dir / f"{workflow_id}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Workflow config not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.parse_workflow_config(data)

    def parse_workflow_config(self, data: Dict[str, Any]) -> WorkflowConfig:
        """Parse dictionary into WorkflowConfig object"""
        nodes = [
            WorkflowNodeConfig(**node_data)
            for node_data in data.get('nodes', [])
        ]

        connections = [
            WorkflowConnectionConfig(**conn_data)
            for conn_data in data.get('connections', [])
        ]

        return WorkflowConfig(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            nodes=nodes,
            connections=connections,
            settings=data.get('settings', {}),
            metadata=data.get('metadata', {})
        )

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflow configurations"""
        workflows = []

        for filepath in self.config_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                workflows.append({
                    'id': data.get('id', filepath.stem),
                    'name': data.get('name', 'Unnamed'),
                    'description': data.get('description', ''),
                    'node_count': len(data.get('nodes', [])),
                    'connection_count': len(data.get('connections', [])),
                    'filepath': str(filepath)
                })

            except Exception as e:
                logger.warning(f"Failed to load workflow {filepath}: {e}")

        return workflows

    def validate_workflow_file(self, workflow_id: str) -> List[str]:
        """Validate a workflow configuration file"""
        try:
            config = self.load_workflow(workflow_id)
            return WorkflowConfigValidator.validate_workflow(config.to_dict())
        except Exception as e:
            return [f"Failed to load workflow: {e}"]


# Convenience functions for programmatic workflow creation
def create_web_scraper_workflow(name: str, urls: List[str], database_config: Dict[str, Any]) -> WorkflowConfig:
    """Create a simple web scraper workflow"""
    return WorkflowConfig(
        id=f"web_scraper_{name.lower().replace(' ', '_')}",
        name=name,
        description=f"Web scraper workflow for {name}",
        nodes=[
            WorkflowNodeConfig(
                id="web_scraper_1",
                type="webScraper",
                name="Web Scraper",
                parameters={
                    "urls": urls,
                    "selectors": {"content": "body", "title": "h1, h2, title"},
                    "max_pages": 10,
                    "rate_limit": 1.0,
                    "use_browser": False,
                    "anti_detection": True
                }
            ),
            WorkflowNodeConfig(
                id="data_filter_1",
                type="dataFilter",
                name="Data Filter",
                parameters={
                    "filters": {"min_length": 50},
                    "remove_duplicates": True
                }
            ),
            WorkflowNodeConfig(
                id="db_storage_1",
                type="databaseStorage",
                name="Database Storage",
                parameters={
                    "table_name": f"{name.lower().replace(' ', '_')}_data",
                    **database_config
                }
            )
        ],
        connections=[
            WorkflowConnectionConfig("web_scraper_1", "data", "data_filter_1", "data"),
            WorkflowConnectionConfig("data_filter_1", "processed_data", "db_storage_1", "data")
        ]
    )


def create_social_media_workflow(name: str, telegram_channels: List[str] = None,
                               discord_servers: List[str] = None, database_config: Dict[str, Any] = None) -> WorkflowConfig:
    """Create a social media monitoring workflow"""
    nodes = []
    connections = []

    node_counter = 1

    # Add Telegram scraper
    if telegram_channels:
        nodes.append(WorkflowNodeConfig(
            id=f"telegram_scraper_{node_counter}",
            type="telegramScraper",
            name="Telegram Scraper",
            parameters={
                "channels": telegram_channels,
                "max_messages": 100,
                "hours_back": 24
            }
        ))
        node_counter += 1

    # Add Discord scraper
    if discord_servers:
        nodes.append(WorkflowNodeConfig(
            id=f"discord_scraper_{node_counter}",
            type="discordScraper",
            name="Discord Scraper",
            parameters={
                "servers": discord_servers,
                "max_messages": 100,
                "hours_back": 24
            }
        ))
        node_counter += 1

    # Add data merger if multiple sources
    if len(nodes) > 1:
        nodes.append(WorkflowNodeConfig(
            id=f"data_merger_{node_counter}",
            type="dataTransformer",
            name="Data Merger",
            parameters={
                "transformations": ["merge_sources"],
                "output_format": "unified"
            }
        ))

        # Connect all sources to merger
        for i, node in enumerate(nodes[:-1]):
            connections.append(WorkflowConnectionConfig(
                node.id, "data", f"data_merger_{node_counter}", f"input_{i+1}"
            ))

        # Connect merger to storage
        connections.append(WorkflowConnectionConfig(
            f"data_merger_{node_counter}", "processed_data", f"db_storage_{node_counter+1}", "data"
        ))
    else:
        # Single source connects directly to storage
        connections.append(WorkflowConnectionConfig(
            nodes[0].id, "data", f"db_storage_{node_counter+1}", "data"
        ))

    # Add database storage
    nodes.append(WorkflowNodeConfig(
        id=f"db_storage_{node_counter+1}",
        type="databaseStorage",
        name="Database Storage",
        parameters={
            "table_name": f"{name.lower().replace(' ', '_')}_social_data",
            **(database_config or {})
        }
    ))

    return WorkflowConfig(
        id=f"social_media_{name.lower().replace(' ', '_')}",
        name=name,
        description=f"Social media monitoring workflow for {name}",
        nodes=nodes,
        connections=connections
    )