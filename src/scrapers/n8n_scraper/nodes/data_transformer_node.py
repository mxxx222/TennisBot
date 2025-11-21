#!/usr/bin/env python3
"""
Data Transformer Node for N8N-Style Scraper

Transforms and processes scraped data into different formats.
"""

import asyncio
import logging
import json
import csv
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from io import StringIO
import hashlib

from .base_node import DataNode, NodeExecutionResult

logger = logging.getLogger(__name__)


class DataTransformerNode(DataNode):
    """
    Node for transforming scraped data.

    Supports:
    - Format conversion (JSON, CSV, XML)
    - Data normalization and cleaning
    - Field mapping and renaming
    - Data aggregation and summarization
    - Content extraction and processing
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Transformation settings
        self.transformations = config.get('transformations', [])
        self.output_format = config.get('output_format', 'json')
        self.field_mappings = config.get('field_mappings', {})

        # Data processing
        self.normalize_text = config.get('normalize_text', True)
        self.extract_entities = config.get('extract_entities', False)
        self.generate_summaries = config.get('generate_summaries', False)

        # Aggregation settings
        self.group_by = config.get('group_by', None)
        self.aggregate_functions = config.get('aggregate_functions', {})

        # Custom transformations
        self.custom_transforms = config.get('custom_transforms', [])

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute data transformation"""
        try:
            # Get data from input
            data = input_data.get('data', {})

            if not data:
                return NodeExecutionResult(
                    success=True,
                    data={'processed_data': []},
                    metadata={'total_items': 0, 'transformations_applied': []},
                    node_id=self.node_id
                )

            # Extract items to transform
            items = self._extract_items_from_data(data)

            if not items:
                return NodeExecutionResult(
                    success=True,
                    data={'processed_data': []},
                    metadata={'total_items': 0, 'transformations_applied': []},
                    node_id=self.node_id
                )

            logger.info(f"Transforming {len(items)} items")

            # Apply transformations
            transformed_items = []
            applied_transformations = []

            for item in items:
                transformed_item = item.copy()

                # Apply field mappings
                if self.field_mappings:
                    transformed_item = self._apply_field_mappings(transformed_item)
                    applied_transformations.append('field_mappings')

                # Apply custom transformations
                for transform in self.transformations:
                    try:
                        transformed_item = self._apply_transformation(transformed_item, transform)
                        applied_transformations.append(transform)
                    except Exception as e:
                        logger.warning(f"Failed to apply transformation '{transform}': {e}")
                        continue

                # Apply custom transforms
                for custom_transform in self.custom_transforms:
                    try:
                        transformed_item = self._apply_custom_transform(transformed_item, custom_transform)
                        applied_transformations.append(f"custom_{custom_transform.get('name', 'unknown')}")
                    except Exception as e:
                        logger.warning(f"Failed to apply custom transform: {e}")
                        continue

                # Normalize text if enabled
                if self.normalize_text:
                    transformed_item = self._normalize_text_fields(transformed_item)
                    applied_transformations.append('text_normalization')

                # Extract entities if enabled
                if self.extract_entities:
                    transformed_item = self._extract_entities(transformed_item)
                    applied_transformations.append('entity_extraction')

                transformed_items.append(transformed_item)

            # Apply aggregation if specified
            if self.group_by:
                transformed_items = self._apply_aggregation(transformed_items)
                applied_transformations.append('aggregation')

            # Generate summaries if enabled
            summaries = {}
            if self.generate_summaries:
                summaries = self._generate_summaries(transformed_items)
                applied_transformations.append('summaries')

            # Convert to output format
            formatted_data = self._format_output(transformed_items, summaries)

            # Prepare output
            output_data = {
                'processed_data': formatted_data,
                'original_count': len(items),
                'transformed_count': len(transformed_items) if isinstance(transformed_items, list) else 1
            }

            # Add summaries if generated
            if summaries:
                output_data['summaries'] = summaries

            return NodeExecutionResult(
                success=True,
                data=output_data,
                metadata={
                    'total_items': len(items),
                    'transformations_applied': list(set(applied_transformations)),
                    'output_format': self.output_format,
                    'has_summaries': bool(summaries)
                },
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            return NodeExecutionResult(
                success=False,
                error=str(e),
                node_id=self.node_id
            )

    def _extract_items_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract list of items from various data formats"""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common keys
            for key in ['messages', 'content', 'items', 'data', 'results', 'processed_data']:
                if key in data and isinstance(data[key], list):
                    return data[key]

            # If single item dict, wrap in list
            return [data]
        else:
            return []

    def _apply_field_mappings(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mappings to rename or restructure fields"""
        transformed = {}

        for new_field, source in self.field_mappings.items():
            if isinstance(source, str):
                # Simple field mapping
                if source in item:
                    transformed[new_field] = item[source]
                elif '.' in source:
                    # Nested field access (e.g., "metadata.length")
                    value = self._get_nested_value(item, source.split('.'))
                    if value is not None:
                        transformed[new_field] = value
            elif isinstance(source, dict):
                # Complex mapping with transformation
                if 'field' in source:
                    value = self._get_nested_value(item, source['field'].split('.'))
                    if value is not None:
                        # Apply transformation if specified
                        if 'transform' in source:
                            value = self._apply_simple_transform(value, source['transform'])
                        transformed[new_field] = value

        # Keep unmapped fields
        for key, value in item.items():
            if key not in transformed:
                transformed[key] = value

        return transformed

    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get nested value from dict using path"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _apply_transformation(self, item: Dict[str, Any], transformation: str) -> Dict[str, Any]:
        """Apply a predefined transformation"""
        transform_funcs = {
            'lowercase': self._transform_lowercase,
            'uppercase': self._transform_uppercase,
            'strip_whitespace': self._transform_strip_whitespace,
            'remove_html': self._transform_remove_html,
            'extract_urls': self._transform_extract_urls,
            'extract_mentions': self._transform_extract_mentions,
            'calculate_length': self._transform_calculate_length,
            'hash_content': self._transform_hash_content,
            'merge_sources': self._transform_merge_sources,
        }

        func = transform_funcs.get(transformation)
        if func:
            return func(item)
        else:
            logger.warning(f"Unknown transformation: {transformation}")
            return item

    def _apply_custom_transform(self, item: Dict[str, Any], custom_transform: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a custom transformation"""
        transform_type = custom_transform.get('type')
        field = custom_transform.get('field')
        params = custom_transform.get('params', {})

        if not field or field not in item:
            return item

        if transform_type == 'regex_replace':
            pattern = params.get('pattern', '')
            replacement = params.get('replacement', '')
            item[field] = re.sub(pattern, replacement, str(item[field]))

        elif transform_type == 'substring':
            start = params.get('start', 0)
            end = params.get('end')
            content = str(item[field])
            item[field] = content[start:end]

        elif transform_type == 'split':
            separator = params.get('separator', ' ')
            item[field] = str(item[field]).split(separator)

        return item

    def _apply_simple_transform(self, value: Any, transform: str) -> Any:
        """Apply simple transformation to a value"""
        if transform == 'lowercase' and isinstance(value, str):
            return value.lower()
        elif transform == 'uppercase' and isinstance(value, str):
            return value.upper()
        elif transform == 'strip' and isinstance(value, str):
            return value.strip()
        elif transform == 'int' and isinstance(value, (str, float)):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return value
        else:
            return value

    # Transformation functions
    def _transform_lowercase(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text fields to lowercase"""
        text_fields = ['content', 'text', 'message', 'title']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                item[field] = item[field].lower()
        return item

    def _transform_uppercase(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text fields to uppercase"""
        text_fields = ['content', 'text', 'message', 'title']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                item[field] = item[field].upper()
        return item

    def _transform_strip_whitespace(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Strip whitespace from text fields"""
        text_fields = ['content', 'text', 'message', 'title', 'author']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                item[field] = item[field].strip()
        return item

    def _transform_remove_html(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Remove HTML tags from text fields"""
        text_fields = ['content', 'text', 'message']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                # Simple HTML tag removal
                item[field] = re.sub(r'<[^>]+>', '', item[field])
        return item

    def _transform_extract_urls(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract URLs from content"""
        text_fields = ['content', 'text', 'message']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                urls = re.findall(r'https?://[^\s]+', item[field])
                item[f'{field}_urls'] = urls
        return item

    def _transform_extract_mentions(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract mentions from content"""
        text_fields = ['content', 'text', 'message']
        for field in text_fields:
            if field in item and isinstance(item[field], str):
                # Extract @mentions and #hashtags
                mentions = re.findall(r'@(\w+)', item[field])
                hashtags = re.findall(r'#(\w+)', item[field])
                item[f'{field}_mentions'] = mentions
                item[f'{field}_hashtags'] = hashtags
        return item

    def _transform_calculate_length(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate content length"""
        text_fields = ['content', 'text', 'message']
        for field in text_fields:
            if field in item:
                content = str(item[field])
                item[f'{field}_length'] = len(content)
                item[f'{field}_word_count'] = len(content.split())
        return item

    def _transform_hash_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hash of content for deduplication"""
        text_fields = ['content', 'text', 'message']
        for field in text_fields:
            if field in item:
                content = str(item[field])
                item[f'{field}_hash'] = hashlib.md5(content.encode()).hexdigest()
        return item

    def _transform_merge_sources(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data from multiple sources (for aggregation)"""
        # This is a placeholder for more complex merging logic
        return item

    def _normalize_text_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize text fields"""
        text_fields = ['content', 'text', 'message', 'title', 'author']

        for field in text_fields:
            if field in item and isinstance(item[field], str):
                # Normalize whitespace
                item[field] = re.sub(r'\s+', ' ', item[field]).strip()

        return item

    def _extract_entities(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from text (placeholder)"""
        # This would require NLP libraries like spaCy
        # For now, just extract basic patterns
        text_fields = ['content', 'text', 'message']

        for field in text_fields:
            if field in item and isinstance(item[field], str):
                text = item[field]

                # Extract email addresses
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                item[f'{field}_emails'] = emails

                # Extract phone numbers (basic pattern)
                phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
                item[f'{field}_phones'] = phones

        return item

    def _apply_aggregation(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply aggregation to items"""
        if not self.group_by or not items:
            return items

        aggregated = {}

        for item in items:
            group_key = self._get_nested_value(item, self.group_by.split('.'))
            if group_key is None:
                group_key = 'unknown'

            group_key = str(group_key)

            if group_key not in aggregated:
                aggregated[group_key] = {
                    'group_key': group_key,
                    'count': 0,
                    'items': []
                }

            aggregated[group_key]['count'] += 1
            aggregated[group_key]['items'].append(item)

            # Apply aggregate functions
            for func_name, field in self.aggregate_functions.items():
                if func_name == 'sum' and field in item:
                    if 'sum_' + field not in aggregated[group_key]:
                        aggregated[group_key]['sum_' + field] = 0
                    try:
                        aggregated[group_key]['sum_' + field] += float(item[field])
                    except (ValueError, TypeError):
                        pass

                elif func_name == 'avg' and field in item:
                    if 'sum_' + field not in aggregated[group_key]:
                        aggregated[group_key]['sum_' + field] = 0
                    if 'count_' + field not in aggregated[group_key]:
                        aggregated[group_key]['count_' + field] = 0

                    try:
                        aggregated[group_key]['sum_' + field] += float(item[field])
                        aggregated[group_key]['count_' + field] += 1
                    except (ValueError, TypeError):
                        pass

        # Calculate averages
        for group_data in aggregated.values():
            for field in self.aggregate_functions.get('avg', []):
                sum_key = 'sum_' + field
                count_key = 'count_' + field
                if sum_key in group_data and count_key in group_data and group_data[count_key] > 0:
                    group_data['avg_' + field] = group_data[sum_key] / group_data[count_key]

        return list(aggregated.values())

    def _generate_summaries(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summaries of the data"""
        if not items:
            return {}

        summaries = {
            'total_items': len(items),
            'content_length_stats': {},
            'source_distribution': {},
            'time_distribution': {},
            'top_keywords': []
        }

        # Content length statistics
        lengths = []
        for item in items:
            content = self._get_nested_value(item, ['content']) or self._get_nested_value(item, ['text'])
            if content:
                lengths.append(len(str(content)))

        if lengths:
            summaries['content_length_stats'] = {
                'min': min(lengths),
                'max': max(lengths),
                'avg': sum(lengths) / len(lengths),
                'total': sum(lengths)
            }

        # Source distribution
        sources = {}
        for item in items:
            source = (self._get_nested_value(item, ['source']) or
                     self._get_nested_value(item, ['channel']) or
                     self._get_nested_value(item, ['server']) or
                     'unknown')
            sources[str(source)] = sources.get(str(source), 0) + 1

        summaries['source_distribution'] = sources

        return summaries

    def _format_output(self, items: Any, summaries: Dict[str, Any]) -> Any:
        """Format output according to specified format"""
        if self.output_format == 'json':
            return items
        elif self.output_format == 'csv':
            return self._format_as_csv(items)
        elif self.output_format == 'xml':
            return self._format_as_xml(items)
        else:
            return items

    def _format_as_csv(self, items: List[Dict[str, Any]]) -> str:
        """Format items as CSV string"""
        if not items:
            return ""

        # Get all unique keys
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())

        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(items)

        return output.getvalue()

    def _format_as_xml(self, items: List[Dict[str, Any]]) -> str:
        """Format items as XML string (basic implementation)"""
        if not items:
            return "<items></items>"

        xml_parts = ["<items>"]
        for item in items:
            xml_parts.append("  <item>")
            for key, value in item.items():
                # Escape XML characters
                escaped_value = str(value).replace('&', '&').replace('<', '<').replace('>', '>')
                xml_parts.append(f"    <{key}>{escaped_value}</{key}>")
            xml_parts.append("  </item>")
        xml_parts.append("</items>")

        return "\n".join(xml_parts)