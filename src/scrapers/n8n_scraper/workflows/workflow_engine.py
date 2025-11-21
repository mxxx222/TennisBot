#!/usr/bin/env python3
"""
Workflow Engine for N8N-Style Web Scraper

This module implements the workflow engine that orchestrates node execution,
similar to n8n's workflow execution system.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict, deque
import json

from ..nodes.base_node import BaseNode, NodeExecutionResult, NodeConnection

logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails"""
    pass


class WorkflowEngine:
    """
    Engine for executing n8n-style workflows.

    Manages node connections, execution order, and data flow between nodes.
    """

    def __init__(self, workflow_config: Dict[str, Any]):
        """
        Initialize workflow engine

        Args:
            workflow_config: Workflow configuration with nodes and connections
        """
        self.config = workflow_config
        self.workflow_id = workflow_config.get('id', 'unnamed_workflow')
        self.name = workflow_config.get('name', 'Unnamed Workflow')

        # Parse nodes and connections
        self.nodes = self._parse_nodes(workflow_config.get('nodes', []))
        self.connections = self._parse_connections(workflow_config.get('connections', []))

        # Execution state
        self.execution_history = []
        self.is_running = False
        self.start_time = None
        self.end_time = None

        # Build execution graph
        self.execution_graph = self._build_execution_graph()

        logger.info(f"✅ Workflow '{self.name}' initialized with {len(self.nodes)} nodes")

    def _parse_nodes(self, nodes_config: List[Dict[str, Any]]) -> Dict[str, BaseNode]:
        """Parse node configurations into node instances"""
        nodes = {}

        for node_config in nodes_config:
            try:
                node_id = node_config['id']
                node_type = node_config['type']
                node_params = node_config.get('parameters', {})

                # Import node class dynamically
                node_class = self._get_node_class(node_type)
                if not node_class:
                    raise ValueError(f"Unknown node type: {node_type}")

                # Create node instance
                node = node_class(node_id, node_params)
                nodes[node_id] = node

                logger.debug(f"Created node: {node_id} ({node_type})")

            except Exception as e:
                logger.error(f"Failed to create node {node_config.get('id', 'unknown')}: {e}")
                raise

        return nodes

    def _parse_connections(self, connections_config: List[Dict[str, Any]]) -> List[NodeConnection]:
        """Parse connection configurations"""
        connections = []

        for conn_config in connections_config:
            connection = NodeConnection(
                from_node=conn_config['from'],
                from_output=conn_config['fromOutput'],
                to_node=conn_config['to'],
                to_input=conn_config['toInput']
            )
            connections.append(connection)

        return connections

    def _get_node_class(self, node_type: str) -> Optional[type]:
        """Get node class by type name"""
        # Import all available node types
        from ..nodes import (
            WebScraperNode, TelegramScraperNode, DiscordScraperNode,
            DataFilterNode, DataTransformerNode, DatabaseStorageNode
        )

        node_types = {
            'webScraper': WebScraperNode,
            'telegramScraper': TelegramScraperNode,
            'discordScraper': DiscordScraperNode,
            'dataFilter': DataFilterNode,
            'dataTransformer': DataTransformerNode,
            'databaseStorage': DatabaseStorageNode,
        }

        return node_types.get(node_type)

    def _build_execution_graph(self) -> Dict[str, Set[str]]:
        """Build graph of node dependencies for execution order"""
        graph = defaultdict(set)  # node -> set of nodes that depend on it
        incoming = defaultdict(int)  # node -> number of incoming connections

        # Build dependency graph
        for conn in self.connections:
            graph[conn.from_node].add(conn.to_node)
            incoming[conn.to_node] += 1

        # Nodes with no incoming connections can start
        for node_id in self.nodes:
            if node_id not in incoming:
                incoming[node_id] = 0

        return dict(graph)

    async def execute(self, trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the workflow

        Args:
            trigger_data: Initial data to trigger workflow execution

        Returns:
            Execution results and metadata
        """
        if self.is_running:
            raise WorkflowExecutionError("Workflow is already running")

        self.is_running = True
        self.start_time = datetime.now()

        try:
            logger.info(f"🚀 Starting workflow execution: {self.name}")

            # Initialize execution state
            node_results = {}
            pending_nodes = deque()
            completed_nodes = set()

            # Find starting nodes (no incoming connections)
            for node_id, node in self.nodes.items():
                if not any(conn.to_node == node_id for conn in self.connections):
                    pending_nodes.append(node_id)

            # Execute nodes in topological order
            while pending_nodes:
                current_node_id = pending_nodes.popleft()

                if current_node_id in completed_nodes:
                    continue

                # Prepare input data for this node
                input_data = self._prepare_node_input(current_node_id, node_results, trigger_data)

                # Execute node
                node = self.nodes[current_node_id]
                result = await node.run(input_data)

                # Store result
                node_results[current_node_id] = result
                completed_nodes.add(current_node_id)

                # Record execution
                self._record_execution(current_node_id, result)

                if not result.success:
                    logger.error(f"❌ Node {current_node_id} failed: {result.error}")
                    # Continue with other branches if possible
                    # In a full implementation, you might want to handle failures differently

                # Add dependent nodes to queue
                for dependent_node in self.execution_graph.get(current_node_id, set()):
                    # Check if all dependencies are completed
                    if self._all_dependencies_completed(dependent_node, completed_nodes):
                        pending_nodes.append(dependent_node)

            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()

            logger.info(f"✅ Workflow completed in {execution_time:.2f}s")

            return {
                'success': True,
                'workflow_id': self.workflow_id,
                'execution_time': execution_time,
                'node_results': {k: v.__dict__ for k, v in node_results.items()},
                'completed_nodes': len(completed_nodes),
                'total_nodes': len(self.nodes)
            }

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            self.end_time = datetime.now()

            return {
                'success': False,
                'error': str(e),
                'workflow_id': self.workflow_id,
                'execution_time': (self.end_time - self.start_time).total_seconds() if self.start_time else 0
            }

        finally:
            self.is_running = False

    def _prepare_node_input(self, node_id: str, node_results: Dict[str, NodeExecutionResult],
                           trigger_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare input data for a node from previous nodes"""
        input_data = {}

        # Add trigger data if this is a starting node
        if trigger_data and not any(conn.to_node == node_id for conn in self.connections):
            input_data['trigger'] = trigger_data

        # Collect data from connected nodes
        for conn in self.connections:
            if conn.to_node == node_id:
                if conn.from_node in node_results:
                    result = node_results[conn.from_node]
                    if result.success and result.data:
                        # Map output to input
                        if isinstance(result.data, dict):
                            input_data[conn.to_input] = result.data.get(conn.from_output, result.data)
                        else:
                            input_data[conn.to_input] = result.data

        return input_data

    def _all_dependencies_completed(self, node_id: str, completed_nodes: Set[str]) -> bool:
        """Check if all dependencies of a node are completed"""
        dependencies = [conn.from_node for conn in self.connections if conn.to_node == node_id]
        return all(dep in completed_nodes for dep in dependencies)

    def _record_execution(self, node_id: str, result: NodeExecutionResult) -> None:
        """Record node execution for history"""
        execution_record = {
            'node_id': node_id,
            'timestamp': datetime.now().isoformat(),
            'success': result.success,
            'execution_time': result.execution_time,
            'error': result.error
        }

        self.execution_history.append(execution_record)

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'is_running': self.is_running,
            'node_count': len(self.nodes),
            'connection_count': len(self.connections),
            'last_execution': self.end_time.isoformat() if self.end_time else None,
            'execution_history_length': len(self.execution_history)
        }

    def get_node_status(self) -> Dict[str, Any]:
        """Get status of all nodes"""
        return {node_id: node.get_status() for node_id, node in self.nodes.items()}

    def reset(self) -> None:
        """Reset workflow state"""
        for node in self.nodes.values():
            node.reset()

        self.execution_history = []
        self.start_time = None
        self.end_time = None

    async def execute_node(self, node_id: str, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute a single node (for testing/debugging)"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")

        node = self.nodes[node_id]
        return await node.run(input_data)


class WorkflowManager:
    """
    Manager for multiple workflows
    """

    def __init__(self):
        self.workflows = {}
        self.active_workflows = set()

    def load_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Load a workflow from configuration"""
        workflow_id = workflow_config.get('id', f"workflow_{len(self.workflows)}")
        workflow = WorkflowEngine(workflow_config)
        self.workflows[workflow_id] = workflow
        return workflow_id

    def load_workflow_from_file(self, file_path: str) -> str:
        """Load workflow from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return self.load_workflow(config)

    async def execute_workflow(self, workflow_id: str, trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow by ID"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        self.active_workflows.add(workflow_id)

        try:
            result = await workflow.execute(trigger_data)
            return result
        finally:
            self.active_workflows.discard(workflow_id)

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        return self.workflows[workflow_id].get_status()

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all loaded workflows"""
        return [
            {
                'id': workflow_id,
                'name': workflow.name,
                'node_count': len(workflow.nodes),
                'is_running': workflow.is_running
            }
            for workflow_id, workflow in self.workflows.items()
        ]