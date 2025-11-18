#!/usr/bin/env python3
"""
🎾 FILTERED MATCHES AI ANALYZER
================================

Analyzes only filtered matches from Notion (Screening = "🟢 KIINNOSTAVA")
Uses GPT-4 for deep analysis with enriched data from Player Cards relations.

Cost: ~$0.03 per match (GPT-4)
Expected: 10-15 matches/day (vs 100 previously) = 90% cost savings
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

# Notion API
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ ERROR: notion-client not installed")
    print("   Install: pip install notion-client")
    exit(1)

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("❌ ERROR: openai library not installed")
    print("   Install: pip install openai")
    exit(1)

# Import Notion updater
from src.notion.itf_database_updater import ITFDatabaseUpdater

logger = logging.getLogger(__name__)

# CONFIG
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
TENNIS_PREMATCH_DB_ID = (
    os.getenv('NOTION_TENNIS_PREMATCH_DB_ID') or
    os.getenv('NOTION_PREMATCH_DB_ID')
)
MODEL = 'gpt-4o'  # Use gpt-4o for better performance/cost ratio

if not OPENAI_API_KEY:
    logger.error("❌ ERROR: OPENAI_API_KEY not set")
    logger.info("   Set it in telegram_secrets.env")
    logger.info("   Get key: https://platform.openai.com/api-keys")
    exit(1)

if not NOTION_API_KEY:
    logger.error("❌ ERROR: NOTION_API_KEY not set")
    logger.info("   Set it in telegram_secrets.env")
    exit(1)

if not TENNIS_PREMATCH_DB_ID:
    logger.error("❌ ERROR: NOTION_TENNIS_PREMATCH_DB_ID not set")
    logger.info("   Set it in telegram_secrets.env")
    exit(1)

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
notion_client = Client(auth=NOTION_API_KEY)


def get_filtered_matches() -> List[Dict[str, Any]]:
    """
    Query Notion for matches where:
    - Screening = "🟢 KIINNOSTAVA"
    - AI Recommendation is empty (not yet analyzed)
    
    Returns:
        List of match page data from Notion
    """
    try:
        # Query for filtered matches that haven't been analyzed
        response = notion_client.databases.query(
            database_id=TENNIS_PREMATCH_DB_ID,
            filter={
                "and": [
                    {
                        "property": "Screening",
                        "formula": {
                            "string": {
                                "equals": "🟢 KIINNOSTAVA"
                            }
                        }
                    },
                    {
                        "or": [
                            {
                                "property": "AI Recommendation",
                                "select": {
                                    "is_empty": True
                                }
                            },
                            {
                                "property": "AI Recommendation",
                                "select": {
                                    "equals": None
                                }
                            }
                        ]
                    }
                ]
            }
        )
        
        matches = response.get('results', [])
        logger.info(f"📊 Found {len(matches)} filtered matches to analyze")
        
        return matches
        
    except Exception as e:
        logger.error(f"❌ Error querying Notion: {e}")
        import traceback
        traceback.print_exc()
        return []


def enrich_match_with_player_data(match: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich match data with Player Cards relation data (ELO, rankings, form)
    
    Args:
        match: Notion match page data
    
    Returns:
        Enriched match data dictionary
    """
    enriched = {
        'match_id': match['id'],
        'player_a_name': None,
        'player_b_name': None,
        'player_a_odds': None,
        'player_b_odds': None,
        'tournament': None,
        'tournament_tier': None,
        'surface': None,
        'player_a_elo': None,
        'player_b_elo': None,
        'player_a_rank': None,
        'player_b_rank': None,
        'player_a_surface_win_pct': None,
        'player_a_form': None,
    }
    
    try:
        props = match.get('properties', {})
        
        # Extract basic match data
        player_a_prop = props.get('Pelaaja A nimi', {})
        if player_a_prop.get('rich_text'):
            enriched['player_a_name'] = player_a_prop['rich_text'][0]['plain_text']
        
        player_b_prop = props.get('Pelaaja B nimi', {})
        if player_b_prop.get('rich_text'):
            enriched['player_b_name'] = player_b_prop['rich_text'][0]['plain_text']
        
        # Extract odds
        player_a_odds_prop = props.get('Player A Odds', {})
        if player_a_odds_prop.get('number'):
            enriched['player_a_odds'] = player_a_odds_prop['number']
        
        player_b_odds_prop = props.get('Player B Odds', {})
        if player_b_odds_prop.get('number'):
            enriched['player_b_odds'] = player_b_odds_prop['number']
        
        # Extract tournament info
        tournament_prop = props.get('Turnaus', {})
        if tournament_prop.get('rich_text'):
            enriched['tournament'] = tournament_prop['rich_text'][0]['plain_text']
        
        tier_prop = props.get('Tournament Tier', {})
        if tier_prop.get('select'):
            enriched['tournament_tier'] = tier_prop['select']['name']
        
        surface_prop = props.get('Kenttä', {})
        if surface_prop.get('select'):
            enriched['surface'] = surface_prop['select']['name']
        
        # Extract Player Cards relation data (rollups)
        # Note: These should be rollup properties in Notion
        player_a_elo_prop = props.get('Player A ELO', {})
        if player_a_elo_prop.get('rollup', {}).get('number'):
            enriched['player_a_elo'] = player_a_elo_prop['rollup']['number']
        
        player_b_elo_prop = props.get('Player B ELO', {})
        if player_b_elo_prop.get('rollup', {}).get('number'):
            enriched['player_b_elo'] = player_b_elo_prop['rollup']['number']
        
        player_a_rank_prop = props.get('Player A Rank', {})
        if player_a_rank_prop.get('rollup', {}).get('number'):
            enriched['player_a_rank'] = player_a_rank_prop['rollup']['number']
        
        player_b_rank_prop = props.get('Player B Rank', {})
        if player_b_rank_prop.get('rollup', {}).get('number'):
            enriched['player_b_rank'] = player_b_rank_prop['rollup']['number']
        
        player_a_surface_win_prop = props.get('Player A Surface Win%', {})
        if player_a_surface_win_prop.get('rollup', {}).get('number'):
            enriched['player_a_surface_win_pct'] = player_a_surface_win_prop['rollup']['number']
        
        player_a_form_prop = props.get('Player A Form', {})
        if player_a_form_prop.get('rollup', {}).get('rich_text'):
            enriched['player_a_form'] = player_a_form_prop['rollup']['rich_text'][0]['plain_text']
        
    except Exception as e:
        logger.error(f"❌ Error enriching match data: {e}")
        import traceback
        traceback.print_exc()
    
    return enriched


def analyze_match_with_gpt(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze match using GPT-4 with tennis-specific prompt
    
    Args:
        match_data: Enriched match data
    
    Returns:
        Analysis result with recommendation, confidence, reasoning, cost
    """
    try:
        # Prepare tennis-specific prompt
        prompt = f"""You are an elite tennis betting analyst specializing in ITF Women's tournaments (W15, W35).

**MATCH DETAILS:**
- Player A: {match_data.get('player_a_name', 'Unknown')}
- Player B: {match_data.get('player_b_name', 'Unknown')}
- Tournament: {match_data.get('tournament', 'Unknown')} ({match_data.get('tournament_tier', 'Unknown')})
- Surface: {match_data.get('surface', 'Unknown')}
- Player A Odds: {match_data.get('player_a_odds', 'N/A')}
- Player B Odds: {match_data.get('player_b_odds', 'N/A')}

**PLAYER DATA:**
- Player A ELO: {match_data.get('player_a_elo', 'N/A')}
- Player B ELO: {match_data.get('player_b_elo', 'N/A')}
- Player A Rank: {match_data.get('player_a_rank', 'N/A')}
- Player B Rank: {match_data.get('player_b_rank', 'N/A')}
- Player A Surface Win%: {match_data.get('player_a_surface_win_pct', 'N/A')}%
- Player A Recent Form: {match_data.get('player_a_form', 'N/A')}

**ANALYSIS FRAMEWORK:**

1. **ELO Analysis**: Compare ELO ratings to assess true probability
2. **Ranking Differential**: {abs((match_data.get('player_a_rank') or 500) - (match_data.get('player_b_rank') or 500))} ranking spots difference
3. **Surface Specialization**: Evaluate surface win% and playing style fit
4. **Value Assessment**: Calculate expected value (odds vs true probability)
5. **Risk Factors**: Identify key risks (form, fatigue, data quality)

**OUTPUT (MUST be valid JSON):**
{{
    "recommendation": "Bet" | "Skip" | "Monitor",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed 3-4 sentence explanation",
    "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
    "expected_value_pct": -10 to 20,
    "risk_level": "Low" | "Medium" | "High"
}}

**Guidelines:**
- Be selective: Only recommend "Bet" if expected value > 5%
- Consider ITF W15/W35 volatility and data quality
- Factor in surface specialization
- Account for ranking gaps and form
"""

        # Call OpenAI API
        start_time = datetime.now()
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an elite tennis betting analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        # Parse response
        content = response.choices[0].message.content
        analysis = json.loads(content)
        
        # Calculate cost (GPT-4o pricing: $2.50/$10 per 1M tokens)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        input_cost = (input_tokens / 1_000_000) * 2.50
        output_cost = (output_tokens / 1_000_000) * 10.00
        total_cost = input_cost + output_cost
        
        result = {
            'recommendation': analysis.get('recommendation', 'Skip'),
            'confidence': float(analysis.get('confidence', 0.5)),
            'reasoning': analysis.get('reasoning', 'Analysis completed'),
            'key_factors': analysis.get('key_factors', []),
            'expected_value_pct': analysis.get('expected_value_pct', 0),
            'risk_level': analysis.get('risk_level', 'Medium'),
            'cost': total_cost,
            'tokens_used': input_tokens + output_tokens,
            'analysis_time': analysis_time
        }
        
        logger.info(f"✅ Analyzed {match_data.get('player_a_name')} vs {match_data.get('player_b_name')}: "
                   f"{result['recommendation']} (Confidence: {result['confidence']:.2f}, Cost: ${result['cost']:.4f})")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse GPT response as JSON: {e}")
        return {
            'recommendation': 'Skip',
            'confidence': 0.0,
            'reasoning': 'Analysis failed: Invalid JSON response',
            'key_factors': [],
            'expected_value_pct': 0,
            'risk_level': 'High',
            'cost': 0.0,
            'tokens_used': 0,
            'analysis_time': 0
        }
    except Exception as e:
        logger.error(f"❌ Error analyzing match: {e}")
        import traceback
        traceback.print_exc()
        return {
            'recommendation': 'Skip',
            'confidence': 0.0,
            'reasoning': f'Analysis failed: {str(e)}',
            'key_factors': [],
            'expected_value_pct': 0,
            'risk_level': 'High',
            'cost': 0.0,
            'tokens_used': 0,
            'analysis_time': 0
        }


def update_notion_with_analysis(match_id: str, analysis: Dict[str, Any]) -> bool:
    """
    Update Notion match page with AI analysis results
    
    Args:
        match_id: Notion page ID
        analysis: Analysis result dictionary
    
    Returns:
        True if successful
    """
    try:
        properties = {
            'AI Recommendation': {
                'select': {
                    'name': analysis['recommendation']
                }
            },
            'AI Confidence': {
                'number': analysis['confidence']
            },
            'AI Reasoning': {
                'rich_text': [{
                    'text': {
                        'content': analysis['reasoning']
                    }
                }]
            },
            'Analysis Cost': {
                'number': analysis['cost']
            },
            'Analyzed At': {
                'date': {
                    'start': datetime.now().isoformat()
                }
            }
        }
        
        notion_client.pages.update(
            page_id=match_id,
            properties=properties
        )
        
        logger.info(f"✅ Updated Notion page {match_id[:8]}... with analysis")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Notion: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to analyze filtered matches"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Starting Filtered Matches AI Analyzer...")
    logger.info(f"   Model: {MODEL}")
    logger.info(f"   Database: {TENNIS_PREMATCH_DB_ID[:8]}...")
    
    # Get filtered matches
    matches = get_filtered_matches()
    
    if not matches:
        logger.info("ℹ️ No filtered matches to analyze")
        return
    
    logger.info(f"📊 Analyzing {len(matches)} matches...")
    
    total_cost = 0.0
    analyzed_count = 0
    failed_count = 0
    
    for match in matches:
        try:
            # Enrich match with Player Cards data
            enriched = enrich_match_with_player_data(match)
            
            # Analyze with GPT
            analysis = analyze_match_with_gpt(enriched)
            
            # Update Notion
            if update_notion_with_analysis(match['id'], analysis):
                analyzed_count += 1
                total_cost += analysis['cost']
            else:
                failed_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing match {match.get('id', 'unknown')}: {e}")
            failed_count += 1
    
    logger.info(f"\n✅ Analysis complete!")
    logger.info(f"   Analyzed: {analyzed_count}")
    logger.info(f"   Failed: {failed_count}")
    logger.info(f"   Total cost: ${total_cost:.4f}")
    logger.info(f"   Avg cost per match: ${total_cost / max(analyzed_count, 1):.4f}")


if __name__ == "__main__":
    main()

