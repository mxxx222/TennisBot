#!/usr/bin/env python3
"""
Base Node Class for N8N-Style Web Scraper

This module defines the base Node class that all scraper nodes inherit from.
Similar to n8n nodes, each node has inputs, outputs, and configuration.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class NodeExecutionResult:
    """Result of node execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    node_id: str = ""
    timestamp: str = ""


@dataclass
class NodeConnection:
    """Represents a connection between nodes"""
    from_node: str
    from_output: str
    to_node: str
    to_input: str


class BaseNode(ABC):
    """
    Base class for all scraper nodes.

    Similar to n8n nodes, each node:
    - Has defined inputs and outputs
    - Can be configured with parameters
    - Processes data and passes it to next nodes
    - Has error handling and retry logic
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        Initialize node

        Args:
            node_id: Unique identifier for this node instance
            config: Node configuration parameters
        """
        self.node_id = node_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Node metadata
        self.name = config.get('name', self.__class__.__name__)
        self.description = config.get('description', '')
        self.category = config.get('category', 'general')

        # Execution settings
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        self.timeout = config.get('timeout', 30.0)

        # Rate limiting
        self.rate_limit = config.get('rate_limit', 1.0)  # requests per second
        self.last_execution = 0.0

        # State
        self.is_active = True
        self.execution_count = 0
        self.error_count = 0
        self.last_error = None

    @property
    @abstractmethod
    def inputs(self) -> List[str]:
        """Define input names for this node"""
        pass

    @property
    @abstractmethod
    def outputs(self) -> List[str]:
        """Define output names for this node"""
        pass

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """
        Execute the node's main logic

        Args:
            input_data: Data from previous nodes, keyed by input name

        Returns:
            NodeExecutionResult with success status and output data
        """
        pass

    async def run(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """
        Run the node with error handling and retries

        Args:
            input_data: Input data from previous nodes

        Returns:
            Execution result
        """
        if not self.is_active:
            return NodeExecutionResult(
                success=False,
                error="Node is inactive",
                node_id=self.node_id
            )

        # Rate limiting
        await self._apply_rate_limit()

        start_time = asyncio.get_event_loop().time()
        result = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Executing {self.name} (attempt {attempt + 1})")

                # Validate inputs
                self._validate_inputs(input_data)

                # Execute node logic
                result = await self.execute(input_data)

                # Set metadata
                result.node_id = self.node_id
                result.timestamp = datetime.now().isoformat()
                result.execution_time = asyncio.get_event_loop().time() - start_time

                self.execution_count += 1

                if result.success:
                    self.logger.info(f"✅ {self.name} executed successfully")
                    return result
                else:
                    self.logger.warning(f"⚠️ {self.name} returned failure: {result.error}")

            except Exception as e:
                error_msg = f"Error in {self.name}: {str(e)}"
                self.logger.error(error_msg)

                self.error_count += 1
                self.last_error = error_msg

                if attempt < self.max_retries:
                    self.logger.info(f"Retrying {self.name} in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    result = NodeExecutionResult(
                        success=False,
                        error=error_msg,
                        node_id=self.node_id,
                        execution_time=asyncio.get_event_loop().time() - start_time
                    )
                    break

        return result

    def _validate_inputs(self, input_data: Dict[str, Any]) -> None:
        """Validate that required inputs are present"""
        required_inputs = [inp for inp in self.inputs if not inp.startswith('optional_')]

        for required_input in required_inputs:
            if required_input not in input_data:
                raise ValueError(f"Missing required input: {required_input}")

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting"""
        if self.rate_limit > 0:
            elapsed = asyncio.get_event_loop().time() - self.last_execution
            min_interval = 1.0 / self.rate_limit

            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            self.last_execution = asyncio.get_event_loop().time()

    def get_status(self) -> Dict[str, Any]:
        """Get node status information"""
        return {
            'node_id': self.node_id,
            'name': self.name,
            'is_active': self.is_active,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'category': self.category
        }

    def reset(self) -> None:
        """Reset node state"""
        self.execution_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_execution = 0.0

    def activate(self) -> None:
        """Activate the node"""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the node"""
        self.is_active = False


class DataNode(BaseNode):
    """
    Base class for nodes that handle data flow (filter, transform, store)
    """

    @property
    def inputs(self) -> List[str]:
        return ['data']

    @property
    def outputs(self) -> List[str]:
        return ['processed_data']


class SourceNode(BaseNode):
    """
    Base class for nodes that generate data (scrapers, API clients)
    """

    @property
    def inputs(self) -> List[str]:
        return ['trigger']  # Can be triggered by schedule or other nodes

    @property
    def outputs(self) -> List[str]:
        return ['data', 'metadata']