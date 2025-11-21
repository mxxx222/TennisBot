#!/usr/bin/env python3
"""
Data Filter Node for N8N-Style Scraper

Filters and cleans scraped data based on various criteria.
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta

from .base_node import DataNode, NodeExecutionResult

logger = logging.getLogger(__name__)


class DataFilterNode(DataNode):
    """
    Node for filtering and cleaning scraped data.

    Supports:
    - Content length filtering
    - Keyword filtering (include/exclude)
    - Duplicate removal
    - Language detection and filtering
    - Date/time filtering
    - Source filtering
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Filtering criteria
        self.filters = config.get('filters', {})
        self.remove_duplicates = config.get('remove_duplicates', True)
        self.min_length = config.get('min_length', 10)
        self.max_length = config.get('max_length', None)
        self.languages = config.get('languages', [])  # Language codes to keep
        self.exclude_languages = config.get('exclude_languages', [])

        # Content filtering
        self.include_keywords = config.get('include_keywords', [])
        self.exclude_keywords = config.get('exclude_keywords', [])
        self.case_sensitive = config.get('case_sensitive', False)

        # Time filtering
        self.max_age_hours = config.get('max_age_hours', None)
        self.min_age_hours = config.get('min_age_hours', None)

        # Source filtering
        self.allowed_sources = config.get('allowed_sources', [])
        self.excluded_sources = config.get('excluded_sources', [])

        # Quality filters
        self.min_quality_score = config.get('min_quality_score', 0.0)
        self.remove_empty = config.get('remove_empty', True)

        # Deduplication settings
        self.dedup_field = config.get('dedup_field', 'content')  # Field to check for duplicates
        self.dedup_method = config.get('dedup_method', 'exact')  # 'exact', 'similar', 'fuzzy'

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute data filtering"""
        try:
            # Get data from input
            data = input_data.get('data', {})

            if not data:
                return NodeExecutionResult(
                    success=True,
                    data={'processed_data': []},
                    metadata={'total_items': 0, 'filtered_items': 0},
                    node_id=self.node_id
                )

            # Extract items to filter
            items = self._extract_items_from_data(data)

            if not items:
                return NodeExecutionResult(
                    success=True,
                    data={'processed_data': []},
                    metadata={'total_items': 0, 'filtered_items': 0},
                    node_id=self.node_id
                )

            logger.info(f"Filtering {len(items)} items")

            # Apply filters
            filtered_items = []
            filter_stats = {
                'total_items': len(items),
                'passed_filters': 0,
                'removed_duplicates': 0,
                'removed_by_length': 0,
                'removed_by_keywords': 0,
                'removed_by_language': 0,
                'removed_by_age': 0,
                'removed_by_source': 0,
                'removed_by_quality': 0,
                'removed_empty': 0
            }

            # Remove duplicates first if enabled
            if self.remove_duplicates:
                items, dup_count = self._remove_duplicates(items)
                filter_stats['removed_duplicates'] = dup_count

            # Apply all other filters
            seen_hashes = set() if self.remove_duplicates else None

            for item in items:
                if self._passes_all_filters(item, seen_hashes):
                    filtered_items.append(item)
                    filter_stats['passed_filters'] += 1
                else:
                    # Track which filter removed this item
                    self._track_filter_removal(item, filter_stats)

            # Prepare output data
            output_data = {
                'processed_data': filtered_items,
                'original_count': len(items),
                'filtered_count': len(filtered_items)
            }

            # Add source-specific data back if it existed
            if isinstance(data, dict) and 'messages' in data:
                output_data['messages'] = filtered_items
            elif isinstance(data, dict) and 'content' in data:
                output_data['content'] = filtered_items

            return NodeExecutionResult(
                success=True,
                data=output_data,
                metadata={
                    **filter_stats,
                    'filter_criteria': self._get_filter_summary()
                },
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Data filtering failed: {e}")
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
            for key in ['messages', 'content', 'items', 'data', 'results']:
                if key in data and isinstance(data[key], list):
                    return data[key]

            # If single item dict, wrap in list
            return [data]
        else:
            return []

    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> tuple:
        """Remove duplicate items"""
        seen = set()
        unique_items = []

        for item in items:
            # Create hash based on dedup field
            content = self._get_item_field(item, self.dedup_field)
            if content:
                if self.dedup_method == 'exact':
                    item_hash = hash(str(content))
                elif self.dedup_method == 'similar':
                    # Simple similarity: remove exact duplicates after normalization
                    normalized = re.sub(r'\s+', ' ', str(content).lower().strip())
                    item_hash = hash(normalized)
                else:
                    item_hash = hash(str(content))

                if item_hash not in seen:
                    seen.add(item_hash)
                    unique_items.append(item)

        removed_count = len(items) - len(unique_items)
        return unique_items, removed_count

    def _passes_all_filters(self, item: Dict[str, Any], seen_hashes: Optional[Set] = None) -> bool:
        """Check if item passes all filters"""
        # Length filter
        if not self._passes_length_filter(item):
            return False

        # Keyword filters
        if not self._passes_keyword_filters(item):
            return False

        # Language filter
        if not self._passes_language_filter(item):
            return False

        # Age filter
        if not self._passes_age_filter(item):
            return False

        # Source filter
        if not self._passes_source_filter(item):
            return False

        # Quality filter
        if not self._passes_quality_filter(item):
            return False

        # Empty content filter
        if self.remove_empty and not self._has_content(item):
            return False

        return True

    def _passes_length_filter(self, item: Dict[str, Any]) -> bool:
        """Check content length"""
        content = self._get_content(item)
        if not content:
            return not self.remove_empty

        length = len(str(content))

        if self.min_length and length < self.min_length:
            return False

        if self.max_length and length > self.max_length:
            return False

        return True

    def _passes_keyword_filters(self, item: Dict[str, Any]) -> bool:
        """Check keyword filters"""
        content = self._get_content(item)
        if not content:
            return True

        text = str(content)
        if not self.case_sensitive:
            text = text.lower()

        # Exclude keywords
        if self.exclude_keywords:
            exclude_patterns = [kw.lower() if not self.case_sensitive else kw for kw in self.exclude_keywords]
            if any(pattern in text for pattern in exclude_patterns):
                return False

        # Include keywords (if specified, at least one must match)
        if self.include_keywords:
            include_patterns = [kw.lower() if not self.case_sensitive else kw for kw in self.include_keywords]
            if not any(pattern in text for pattern in include_patterns):
                return False

        return True

    def _passes_language_filter(self, item: Dict[str, Any]) -> bool:
        """Check language filters (placeholder - would need langdetect library)"""
        # For now, just check if languages are specified
        if not self.languages and not self.exclude_languages:
            return True

        # TODO: Implement actual language detection
        # This would require: pip install langdetect
        # from langdetect import detect

        # Placeholder: assume all pass if no detection available
        return True

    def _passes_age_filter(self, item: Dict[str, Any]) -> bool:
        """Check age filters"""
        if not self.max_age_hours and not self.min_age_hours:
            return True

        timestamp = self._get_timestamp(item)
        if not timestamp:
            return True  # If no timestamp, let it pass

        try:
            item_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now()
            age_hours = (now - item_time).total_seconds() / 3600

            if self.max_age_hours and age_hours > self.max_age_hours:
                return False

            if self.min_age_hours and age_hours < self.min_age_hours:
                return False

        except (ValueError, AttributeError):
            # If timestamp parsing fails, let it pass
            pass

        return True

    def _passes_source_filter(self, item: Dict[str, Any]) -> bool:
        """Check source filters"""
        source = self._get_item_field(item, 'source') or self._get_item_field(item, 'channel') or self._get_item_field(item, 'server')

        if not source:
            return True

        # Exclude sources
        if self.excluded_sources:
            if any(exc_src.lower() in str(source).lower() for exc_src in self.excluded_sources):
                return False

        # Include sources (if specified)
        if self.allowed_sources:
            if not any(inc_src.lower() in str(source).lower() for inc_src in self.allowed_sources):
                return False

        return True

    def _passes_quality_filter(self, item: Dict[str, Any]) -> bool:
        """Check quality score"""
        if self.min_quality_score <= 0:
            return True

        quality_score = self._get_item_field(item, 'quality_score') or self._get_item_field(item, 'confidence_score')
        if quality_score is None:
            return True  # If no quality score, let it pass

        try:
            return float(quality_score) >= self.min_quality_score
        except (ValueError, TypeError):
            return True

    def _has_content(self, item: Dict[str, Any]) -> bool:
        """Check if item has meaningful content"""
        content = self._get_content(item)
        if not content:
            return False

        text = str(content).strip()
        return len(text) > 0 and not text.isspace()

    def _get_content(self, item: Dict[str, Any]) -> Optional[str]:
        """Get content field from item"""
        return self._get_item_field(item, 'content') or self._get_item_field(item, 'text') or self._get_item_field(item, 'message')

    def _get_timestamp(self, item: Dict[str, Any]) -> Optional[str]:
        """Get timestamp field from item"""
        return (self._get_item_field(item, 'timestamp') or
                self._get_item_field(item, 'created_at') or
                self._get_item_field(item, 'date') or
                self._get_item_field(item, 'time'))

    def _get_item_field(self, item: Dict[str, Any], field: str) -> Any:
        """Safely get field from item"""
        return item.get(field)

    def _track_filter_removal(self, item: Dict[str, Any], stats: Dict[str, int]) -> None:
        """Track which filter caused removal (for debugging)"""
        # This could be enhanced to track specific reasons
        pass

    def _get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of active filters"""
        return {
            'remove_duplicates': self.remove_duplicates,
            'length_filter': {'min': self.min_length, 'max': self.max_length},
            'keyword_filters': {
                'include': self.include_keywords,
                'exclude': self.exclude_keywords,
                'case_sensitive': self.case_sensitive
            },
            'language_filters': {
                'allowed': self.languages,
                'excluded': self.exclude_languages
            },
            'age_filters': {
                'max_age_hours': self.max_age_hours,
                'min_age_hours': self.min_age_hours
            },
            'source_filters': {
                'allowed': self.allowed_sources,
                'excluded': self.excluded_sources
            },
            'quality_filter': {'min_score': self.min_quality_score},
            'remove_empty': self.remove_empty
        }