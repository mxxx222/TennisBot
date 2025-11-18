# AI Analysis Module

This module provides AI-powered analysis capabilities for tennis match evaluation and betting opportunity assessment.

## Components

- **hybrid_router.py** - Smart routing between Venice AI and OpenAI based on analysis criteria
- **venice_client.py** - Venice AI integration for cost-effective analysis
- **openai_client.py** - OpenAI GPT-4 integration for premium analysis
- **match_analyzer.py** - Main match analysis orchestrator
- **pattern_detector.py** - Pattern detection and analysis
- **quality_validator.py** - Quality validation for AI analysis results
- **cost_tracker.py** - Cost tracking for AI API usage
- **ai_config.py** - Configuration for AI services

## Usage

The module is used by:
- `enhanced_live_monitor.py` - Live match monitoring
- `tennis_itf_screener_enhanced.py` - ITF match screening
- `monitors/value_detector.py` - Value detection
- Various test files

## Features

- Hybrid AI routing (90% Venice AI, 10% OpenAI)
- Cost optimization
- Quality validation
- Pattern detection
- Match analysis with confidence scoring

