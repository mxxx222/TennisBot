#!/usr/bin/env python3
"""
N8N-Style Web Scraper

A modular, workflow-based web scraping system inspired by n8n.
Supports scraping from websites, forums, Telegram groups, and Discord servers.
"""

from .workflows.workflow_engine import WorkflowEngine, WorkflowManager
from .config.workflow_config import (
    WorkflowConfig, WorkflowConfigManager,
    create_web_scraper_workflow, create_social_media_workflow
)

__version__ = "1.0.0"
__author__ = "TennisBot AI"

__all__ = [
    'WorkflowEngine',
    'WorkflowManager',
    'WorkflowConfig',
    'WorkflowConfigManager',
    'create_web_scraper_workflow',
    'create_social_media_workflow'
]