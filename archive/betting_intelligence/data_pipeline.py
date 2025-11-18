#!/usr/bin/env python3
"""
🔧 DATA CLEANING AND VALIDATION PIPELINE
========================================

Comprehensive data processing pipeline with:
- Data cleaning and normalization
- Quality validation and filtering
- Duplicate detection and removal
- Statistical analysis and outlier detection
- Data enrichment and feature engineering

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics"""
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    missing_values: Dict[str, int] = None
    outliers_detected: int = 0
    data_completeness: float = 0.0
    quality_score: float = 0.0

    def __post_init__(self):
        if self.missing_values is None:
            self.missing_values = {}

class DataCleaningPipeline:
    """Comprehensive data cleaning and validation pipeline"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.quality_thresholds = {
            'min_completeness': 0.7,
            'max_missing_ratio': 0.3,
            'min_quality_score': 0.6
        }

        # Update with config values
        self.quality_thresholds.update(self.config.get('quality_thresholds', {}))

        # Cleaning rules
        self.cleaning_rules = {
            'team_names': self._clean_team_names,
            'odds': self._clean_odds,
            'scores': self._clean_scores,
            'dates': self._clean_dates,
            'leagues': self._clean_leagues
        }

    def process_scraped_data(self, raw_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], DataQualityMetrics]:
        """
        Process raw scraped data through the cleaning pipeline

        Args:
            raw_data: Raw scraped data as list of dictionaries

        Returns:
            Tuple of (cleaned_data, quality_metrics)
        """
        logger.info(f"🔧 Processing {len(raw_data)} raw records through cleaning pipeline...")

        # Initialize quality metrics
        metrics = DataQualityMetrics(total_records=len(raw_data))

        # Step 1: Initial validation and basic cleaning
        validated_data = []
        for record in raw_data:
            if self._basic_validation(record):
                validated_data.append(record)
            else:
                metrics.invalid_records += 1

        logger.info(f"✅ Basic validation: {len(validated_data)} valid, {metrics.invalid_records} invalid")

        # Step 2: Deduplication
        deduplicated_data, duplicate_count = self._remove_duplicates(validated_data)
        metrics.duplicate_records = duplicate_count

        logger.info(f"✅ Deduplication: {len(deduplicated_data)} unique records, {duplicate_count} duplicates removed")

        # Step 3: Data cleaning and normalization
        cleaned_data = []
        for record in deduplicated_data:
            cleaned_record = self._apply_cleaning_rules(record)
            if cleaned_record:
                cleaned_data.append(cleaned_record)

        logger.info(f"✅ Data cleaning: {len(cleaned_data)} records cleaned")

        # Step 4: Outlier detection and filtering
        filtered_data, outlier_count = self._detect_and_filter_outliers(cleaned_data)
        metrics.outliers_detected = outlier_count

        logger.info(f"✅ Outlier filtering: {len(filtered_data)} records kept, {outlier_count} outliers removed")

        # Step 5: Data enrichment
        enriched_data = self._enrich_data(filtered_data)

        logger.info(f"✅ Data enrichment: {len(enriched_data)} records enriched")

        # Step 6: Final quality assessment
        metrics.valid_records = len(enriched_data)
        metrics = self._calculate_quality_metrics(enriched_data, metrics)

        logger.info(f"📊 Final quality score: {metrics.quality_score:.2f} ({metrics.data_completeness:.1%} complete)")

        return enriched_data, metrics

    def _basic_validation(self, record: Dict[str, Any]) -> bool:
        """Perform basic validation on a record"""
        try:
            # Check for required fields
            required_fields = ['home_team', 'away_team']
            for field in required_fields:
                if field not in record or not record[field]:
                    return False

            # Check for minimum data quality
            data_fields = ['odds', 'score', 'statistics', 'date']
            has_data = any(field in record and record[field] for field in data_fields)

            if not has_data:
                return False

            return True

        except Exception as e:
            logger.debug(f"Basic validation error: {e}")
            return False

    def _remove_duplicates(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Remove duplicate records based on match signatures"""
        seen_signatures = set()
        unique_data = []
        duplicate_count = 0

        for record in data:
            # Create a signature for the record
            signature = self._create_record_signature(record)

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_data.append(record)
            else:
                duplicate_count += 1

        return unique_data, duplicate_count

    def _create_record_signature(self, record: Dict[str, Any]) -> str:
        """Create a unique signature for a record to detect duplicates"""
        try:
            # Use key identifying fields
            home_team = str(record.get('home_team', '')).lower().strip()
            away_team = str(record.get('away_team', '')).lower().strip()
            date = str(record.get('date', '')).strip()
            league = str(record.get('league', '')).lower().strip()

            # Create signature
            signature_parts = [home_team, away_team, date, league]
            signature = '|'.join(signature_parts)

            # Add hash for consistency
            return hashlib.md5(signature.encode()).hexdigest()

        except Exception as e:
            logger.debug(f"Error creating signature: {e}")
            return str(hash(str(record)))

    def _apply_cleaning_rules(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply all cleaning rules to a record"""
        try:
            cleaned_record = record.copy()

            # Apply each cleaning rule
            for field, cleaning_func in self.cleaning_rules.items():
                if field in cleaned_record:
                    cleaned_record[field] = cleaning_func(cleaned_record[field])

            # Additional general cleaning
            cleaned_record = self._general_cleaning(cleaned_record)

            return cleaned_record

        except Exception as e:
            logger.debug(f"Error applying cleaning rules: {e}")
            return None

    def _clean_team_names(self, name: str) -> str:
        """Clean and standardize team names"""
        if not isinstance(name, str):
            return str(name)

        # Remove extra whitespace
        name = ' '.join(name.split())

        # Remove special characters but keep spaces, hyphens, apostrophes
        name = re.sub(r'[^\w\s\-\']', '', name)

        # Standardize common abbreviations
        replacements = {
            'fc': 'FC',
            'ac': 'AC',
            'as': 'AS',
            'us': 'US',
            'cf': 'CF',
            'sc': 'SC',
            'rb': 'RB',
            'tsg': 'TSG'
        }

        words = name.split()
        standardized_words = []

        for word in words:
            lower_word = word.lower()
            if lower_word in replacements:
                # Preserve original case pattern
                if word.isupper():
                    standardized_words.append(replacements[lower_word].upper())
                else:
                    standardized_words.append(replacements[lower_word])
            else:
                standardized_words.append(word)

        return ' '.join(standardized_words).strip()

    def _clean_odds(self, odds: Any) -> Any:
        """Clean and validate odds values"""
        if isinstance(odds, dict):
            # Clean odds dictionary
            cleaned_odds = {}
            for key, value in odds.items():
                if isinstance(value, (int, float)):
                    if 1.01 <= value <= 100.0:  # Valid odds range
                        cleaned_odds[key] = round(float(value), 2)
                elif isinstance(value, str):
                    try:
                        numeric_value = float(value.replace(',', '.'))
                        if 1.01 <= numeric_value <= 100.0:
                            cleaned_odds[key] = round(numeric_value, 2)
                    except (ValueError, AttributeError):
                        continue
            return cleaned_odds if cleaned_odds else None

        elif isinstance(odds, (int, float)):
            if 1.01 <= odds <= 100.0:
                return round(float(odds), 2)

        return None

    def _clean_scores(self, score: Any) -> Any:
        """Clean and standardize score formats"""
        if not score:
            return None

        if isinstance(score, str):
            # Parse various score formats
            score = score.strip()

            # Handle common patterns
            patterns = [
                r'(\d+)[-\s](\d+)',  # 2-1 or 2 1
                r'(\d+):(\d+)',      # 2:1
                r'(\d+)\s*-\s*(\d+)' # 2 - 1
            ]

            for pattern in patterns:
                match = re.search(pattern, score)
                if match:
                    try:
                        home_score = int(match.group(1))
                        away_score = int(match.group(2))
                        return f"{home_score}-{away_score}"
                    except (ValueError, IndexError):
                        continue

        return str(score)

    def _clean_dates(self, date: Any) -> Any:
        """Clean and standardize date formats"""
        if not date:
            return None

        try:
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%m-%d-%Y'
            ]

            if isinstance(date, str):
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue

            elif isinstance(date, datetime):
                return date.strftime('%Y-%m-%d')

        except Exception as e:
            logger.debug(f"Date cleaning error: {e}")

        return str(date)

    def _clean_leagues(self, league: str) -> str:
        """Clean and standardize league names"""
        if not isinstance(league, str):
            return str(league)

        # Remove extra whitespace
        league = ' '.join(league.split())

        # Standardize common league names
        league_mappings = {
            'premier league': 'Premier League',
            'champions league': 'UEFA Champions League',
            'europa league': 'UEFA Europa League',
            'la liga': 'La Liga',
            'bundesliga': 'Bundesliga',
            'serie a': 'Serie A',
            'ligue 1': 'Ligue 1',
            'atp': 'ATP Tour',
            'wta': 'WTA Tour',
            'nba': 'NBA',
            'nfl': 'NFL'
        }

        lower_league = league.lower()
        if lower_league in league_mappings:
            return league_mappings[lower_league]

        return league

    def _general_cleaning(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply general cleaning rules"""
        cleaned = record.copy()

        # Remove empty or None values
        keys_to_remove = []
        for key, value in cleaned.items():
            if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del cleaned[key]

        # Normalize string values
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()

        return cleaned

    def _detect_and_filter_outliers(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Detect and filter statistical outliers"""
        if not data:
            return data, 0

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(data)

        outlier_indices = set()

        # Check odds for outliers
        if 'odds' in df.columns:
            odds_data = df['odds'].dropna()

            for idx, odds_dict in odds_data.items():
                if isinstance(odds_dict, dict):
                    odds_values = [v for v in odds_dict.values() if isinstance(v, (int, float))]

                    if len(odds_values) >= 3:  # Need minimum data for outlier detection
                        # Use IQR method for outlier detection
                        q1 = np.percentile(odds_values, 25)
                        q3 = np.percentile(odds_values, 75)
                        iqr = q3 - q1

                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        # Check if any odds are outliers
                        if any(odds < lower_bound or odds > upper_bound for odds in odds_values):
                            outlier_indices.add(idx)

        # Remove outliers
        filtered_data = [record for i, record in enumerate(data) if i not in outlier_indices]

        return filtered_data, len(outlier_indices)

    def _enrich_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich data with additional features and calculations"""
        enriched_data = []

        for record in data:
            enriched_record = record.copy()

            # Add derived features
            enriched_record = self._add_derived_features(enriched_record)

            # Add data quality indicators
            enriched_record = self._add_quality_indicators(enriched_record)

            enriched_data.append(enriched_record)

        return enriched_data

    def _add_derived_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add derived features to the record"""
        enriched = record.copy()

        # Calculate odds-related features
        if 'odds' in enriched and isinstance(enriched['odds'], dict):
            odds = enriched['odds']

            # Calculate implied probabilities
            implied_probs = {}
            for bookmaker, bookmaker_odds in odds.items():
                if isinstance(bookmaker_odds, dict):
                    probs = {}
                    for outcome, odds_value in bookmaker_odds.items():
                        if isinstance(odds_value, (int, float)) and odds_value > 1:
                            probs[outcome] = 1 / odds_value
                    if probs:
                        implied_probs[bookmaker] = probs

            if implied_probs:
                enriched['implied_probabilities'] = implied_probs

            # Calculate bookmaker margins
            margins = {}
            for bookmaker, bookmaker_odds in odds.items():
                if isinstance(bookmaker_odds, dict) and len(bookmaker_odds) >= 2:
                    margin = sum(1/odds_val for odds_val in bookmaker_odds.values() if isinstance(odds_val, (int, float)) and odds_val > 1)
                    margins[bookmaker] = margin - 1  # Overround

            if margins:
                enriched['bookmaker_margins'] = margins

        # Add match characteristics
        enriched = self._add_match_characteristics(enriched)

        return enriched

    def _add_match_characteristics(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add match characteristic features"""
        enriched = record.copy()

        # Determine match type
        sport = enriched.get('sport', '').lower()

        if sport == 'tennis':
            enriched['match_type'] = 'individual'
            enriched['max_sets'] = 3 if 'wta' in enriched.get('league', '').lower() else 5

        elif sport == 'football':
            enriched['match_type'] = 'team'
            enriched['max_goals'] = None  # No limit

        elif sport == 'basketball':
            enriched['match_type'] = 'team'
            enriched['max_points'] = None  # No limit

        # Add time-based features
        if 'date' in enriched:
            try:
                match_date = datetime.strptime(enriched['date'], '%Y-%m-%d')
                now = datetime.now()

                enriched['days_until_match'] = (match_date - now).days
                enriched['is_upcoming'] = match_date > now
                enriched['is_today'] = match_date.date() == now.date()

            except (ValueError, TypeError):
                pass

        return enriched

    def _add_quality_indicators(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add data quality indicators"""
        enriched = record.copy()

        # Calculate field completeness
        total_fields = len(record)
        non_empty_fields = sum(1 for v in record.values() if v is not None and v != "")

        enriched['field_completeness'] = non_empty_fields / total_fields if total_fields > 0 else 0

        # Data source diversity
        if 'data_sources' in enriched and isinstance(enriched['data_sources'], list):
            enriched['source_diversity'] = len(set(enriched['data_sources']))
        else:
            enriched['source_diversity'] = 1

        # Odds quality indicator
        if 'odds' in enriched and isinstance(enriched['odds'], dict):
            bookmaker_count = len(enriched['odds'])
            total_odds = sum(len(bookmaker_odds) for bookmaker_odds in enriched['odds'].values()
                           if isinstance(bookmaker_odds, dict))

            enriched['odds_coverage'] = bookmaker_count
            enriched['total_odds_points'] = total_odds

        return enriched

    def _calculate_quality_metrics(self, data: List[Dict[str, Any]], metrics: DataQualityMetrics) -> DataQualityMetrics:
        """Calculate comprehensive quality metrics"""
        if not data:
            return metrics

        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)

        # Calculate missing values
        for column in df.columns:
            missing_count = df[column].isnull().sum()
            if missing_count > 0:
                metrics.missing_values[column] = int(missing_count)

        # Calculate data completeness
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.notnull().sum().sum()
        metrics.data_completeness = non_null_cells / total_cells if total_cells > 0 else 0

        # Calculate quality score (weighted average of various factors)
        completeness_score = metrics.data_completeness
        validity_score = metrics.valid_records / metrics.total_records if metrics.total_records > 0 else 0
        uniqueness_score = 1 - (metrics.duplicate_records / metrics.total_records) if metrics.total_records > 0 else 0

        # Weighted quality score
        metrics.quality_score = (
            completeness_score * 0.4 +
            validity_score * 0.4 +
            uniqueness_score * 0.2
        )

        return metrics

    def validate_data_quality(self, data: List[Dict[str, Any]], metrics: DataQualityMetrics) -> bool:
        """Validate if data meets quality thresholds"""
        if metrics.quality_score < self.quality_thresholds['min_quality_score']:
            logger.warning(f"⚠️ Quality score {metrics.quality_score:.2f} below threshold {self.quality_thresholds['min_quality_score']}")
            return False

        if metrics.data_completeness < self.quality_thresholds['min_completeness']:
            logger.warning(f"⚠️ Data completeness {metrics.data_completeness:.1%} below threshold {self.quality_thresholds['min_completeness']:.1%}")
            return False

        # Check missing values ratio
        for field, missing_count in metrics.missing_values.items():
            missing_ratio = missing_count / metrics.total_records if metrics.total_records > 0 else 0
            if missing_ratio > self.quality_thresholds['max_missing_ratio']:
                logger.warning(f"⚠️ Field '{field}' has {missing_ratio:.1%} missing values (threshold: {self.quality_thresholds['max_missing_ratio']:.1%})")
                return False

        return True

    def export_cleaned_data(self, data: List[Dict[str, Any]], metrics: DataQualityMetrics,
                          filename: str = None) -> str:
        """Export cleaned data with quality metrics"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cleaned_sports_data_{timestamp}.json"

        output_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_records': len(data),
                'quality_metrics': asdict(metrics),
                'pipeline_version': '1.0.0'
            },
            'data': data
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Exported {len(data)} cleaned records to {filename}")
        return filename

# Convenience functions
def clean_scraped_data(raw_data: List[Dict[str, Any]], config: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], DataQualityMetrics]:
    """Convenience function to clean scraped data"""
    pipeline = DataCleaningPipeline(config)
    return pipeline.process_scraped_data(raw_data)

def validate_and_export_data(data: List[Dict[str, Any]], metrics: DataQualityMetrics,
                           config: Dict[str, Any] = None) -> bool:
    """Validate data quality and export if acceptable"""
    pipeline = DataCleaningPipeline(config)

    if pipeline.validate_data_quality(data, metrics):
        filename = pipeline.export_cleaned_data(data, metrics)
        logger.info(f"✅ Data quality validated and exported to {filename}")
        return True
    else:
        logger.error("❌ Data quality validation failed")
        return False

if __name__ == "__main__":
    # Test the data cleaning pipeline
    print("🔧 DATA CLEANING PIPELINE TEST")
    print("=" * 50)

    # Create sample raw data
    sample_data = [
        {
            'home_team': '  Manchester United  ',
            'away_team': 'Liverpool FC',
            'date': '2024-01-15',
            'odds': {
                'bet365': {'home': 2.10, 'away': 3.20, 'draw': 3.50},
                'pinnacle': {'home': 2.05, 'away': 3.25, 'draw': 3.45}
            },
            'score': '2-1',
            'league': 'premier league'
        },
        {
            'home_team': 'Manchester United',
            'away_team': 'Liverpool FC',
            'date': '2024-01-15',
            'odds': {
                'bet365': {'home': 2.10, 'away': 3.20, 'draw': 3.50}
            },
            'score': '2-1',
            'league': 'premier league'
        },  # Duplicate
        {
            'home_team': 'Chelsea',
            'away_team': 'Arsenal',
            'date': '2024-01-16',
            'odds': {
                'bet365': {'home': 500.0, 'away': 1.01}  # Outlier odds
            },
            'score': None,
            'league': 'premier league'
        }
    ]

    print(f"🧪 Testing with {len(sample_data)} sample records...")

    try:
        # Process data through pipeline
        cleaned_data, metrics = clean_scraped_data(sample_data)

        print(f"✅ Processing complete:")
        print(f"   Total records: {metrics.total_records}")
        print(f"   Valid records: {metrics.valid_records}")
        print(f"   Duplicates removed: {metrics.duplicate_records}")
        print(f"   Outliers detected: {metrics.outliers_detected}")
        print(f"   Data completeness: {metrics.data_completeness:.1%}")
        print(f"   Quality score: {metrics.quality_score:.2f}")

        # Validate and export
        if validate_and_export_data(cleaned_data, metrics):
            print("✅ Data validation and export successful")
        else:
            print("❌ Data validation failed")

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()