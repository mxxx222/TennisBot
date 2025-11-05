"""
High-Accuracy Signal Generation & Notification System - Educational Framework
Comprehensive signal management with safety protocols and educational notifications

⚠️ EDUCATIONAL USE ONLY - NO REAL MONEY BETTING ⚠️
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import os

# Mock classes for standalone testing (to be replaced with real implementations)
@dataclass
class AnalysisResult:
    """Mock AnalysisResult for testing"""
    pattern_name: str
    confidence: float
    bet: str
    reasoning: str
    key_factors: List[str]
    odds_range: tuple
    expected_hitrate: float
    risk_level: str

class PatternManager:
    """Mock PatternManager for testing"""
    
    def analyze_match(self, match_data: Dict) -> List[AnalysisResult]:
        """Mock analyze_match method"""
        # Return mock result for testing
        result = AnalysisResult(
            pattern_name="LateGameProtection",
            confidence=0.78,
            bet="Home Win",
            reasoning="Leading team showing strong defensive stability in final quarter",
            key_factors=["strong_home_form", "defensive_stability", "late_game_advantage"],
            odds_range=(1.15, 1.85),
            expected_hitrate=0.80,
            risk_level="LOW"
        )
        return [result]
    
    def get_best_signal(self, match: Dict, min_confidence: float = 0.75) -> Optional[AnalysisResult]:
        """Mock get_best_signal method"""
        results = self.analyze_match(match)
        if results and results[0].confidence >= min_confidence:
            return results[0]
        return None
    
    def get_pattern_performance(self) -> Dict:
        """Mock get_pattern_performance method"""
        return {
            'total_patterns': 5,
            'active_patterns': 5,
            'average_confidence': 0.78
        }

class APIFootballScraper:
    """Mock APIFootballScraper for testing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get_live_fixtures(self) -> List[Dict]:
        """Mock get_live_fixtures method"""
        # Return sample live matches for testing
        return [
            {
                'fixture_id': '123',
                'home_team': 'Test Team A',
                'away_team': 'Test Team B',
                'league': 'Educational League',
                'home_score': 1,
                'away_score': 0,
                'minute': 78
            }
        ]
    
    async def enrich_live_matches(self, matches: List[Dict]) -> List[Dict]:
        """Mock enrich_live_matches method"""
        # Add mock prematch data to matches
        for match in matches:
            match['prematch_data'] = {
                'elo_difference': 120,
                'home_form': {'win_rate': 0.70},
                'away_form': {'win_rate': 0.30},
                'head_to_head': {'team1_wins': 3, 'total_matches': 5},
                'home_ratings': {'avg_goals_for': 1.8, 'clean_sheet_rate': 0.4},
                'away_ratings': {'avg_goals_for': 1.2, 'clean_sheet_rate': 0.2}
            }
            match['statistics'] = {
                'home_stats': {'Expected goals (xG)': '1.2', 'Total Shots': '8', 'Ball Possession': '65%'},
                'away_stats': {'Expected goals (xG)': '0.4', 'Total Shots': '3', 'Ball Possession': '35%'}
            }
        return matches

@dataclass
class Signal:
    """High-confidence betting signal"""
    signal_id: str
    match_data: Dict
    pattern_result: AnalysisResult
    timestamp: datetime
    confidence_level: str
    odds_range: tuple
    expected_hitrate: float
    risk_assessment: str
    educational_context: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'odds_range': list(self.odds_range)
        }

class SafetyProtocols:
    """Safety and educational protocols"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Safety thresholds
        self.safety_config = {
            'max_daily_signals': 10,
            'min_confidence_threshold': 0.75,
            'max_odds_range': (1.10, 2.00),
            'educational_mode': True,
            'require_confirmation': True,
            'daily_reset_hour': 6  # 6 AM reset
        }
        
        # Educational disclaimers
        self.disclaimers = {
            'general': "⚠️ EDUCATIONAL USE ONLY - NO REAL MONEY BETTING",
            'analysis': "This is educational analysis for learning purposes only",
            'historical': "Past performance does not guarantee future results",
            'pattern': "Pattern analysis is for educational understanding",
            'risk': "All betting involves risk - never bet more than you can afford to lose"
        }
    
    def validate_signal(self, signal: Signal) -> tuple[bool, List[str]]:
        """Validate signal against safety criteria"""
        
        violations = []
        
        # Confidence threshold
        if signal.pattern_result.confidence < self.safety_config['min_confidence_threshold']:
            violations.append(f"Confidence below threshold: {signal.pattern_result.confidence:.2f}")
        
        # Odds range validation
        odds_min, odds_max = signal.odds_range
        safety_min, safety_max = self.safety_config['max_odds_range']
        
        if odds_min < safety_min or odds_max > safety_max:
            violations.append(f"Odds outside safe range: {signal.odds_range}")
        
        # Educational mode requirement
        if not self.safety_config['educational_mode']:
            violations.append("System not in educational mode")
        
        # Pattern confidence vs expected hitrate check
        if signal.pattern_result.confidence > signal.expected_hitrate + 0.1:
            violations.append("Confidence significantly exceeds historical hitrate")
        
        is_safe = len(violations) == 0
        return is_safe, violations
    
    def generate_educational_context(self, signal: Signal) -> str:
        """Generate educational context for the signal"""
        
        pattern_name = signal.pattern_result.pattern_name
        confidence = signal.pattern_result.confidence
        expected_hitrate = signal.expected_hitrate
        
        contexts = {
            'LateGameProtection': """
🧠 **EDUCATIONAL CONTEXT - Late Game Protection Pattern**

This pattern identifies situations where a leading team is likely to maintain their advantage in the final 20-30 minutes of a match. Key educational points:

**Why This Pattern Works:**
- Late game fatigue affects both teams, but the leading team can "manage" the game
- Home advantage becomes more significant in the final 20 minutes
- Teams with better recent form are more likely to hold leads
- Goal difference of 1 is psychologically manageable

**Learning Objective:**
Understand how time pressure, fatigue, and team psychology interact in live betting scenarios.
            """,
            
            'DefensiveStalemate': """
🧠 **EDUCATIONAL CONTEXT - Defensive Stalemate Pattern**

This pattern identifies matches where both teams struggle to create clear scoring chances, leading to low-scoring outcomes.

**Why This Pattern Works:**
- Two defensive teams can neutralize each other's attacking threats
- Lack of quality chances in open play suggests few goals
- Goalkeeper quality and defensive structure are key factors
- Time passing without goals reduces probability of late scoring

**Learning Objective:**
Learn to identify defensive vs attacking matchups and their impact on goal expectations.
            """,
            
            'DominantFavorite': """
🧠 **EDUCATIONAL CONTEXT - Dominant Favorite Pattern**

This pattern identifies matches where one team significantly outperforms the other across multiple metrics.

**Why This Pattern Works:**
- Stronger teams maintain dominance across possession, shots, and territory
- Quality differences become more apparent as matches progress
- Multiple indicators (ELO, form, H2H) align to support the favorite
- Home advantage compounds the natural quality gap

**Learning Objective:**
Understand how to analyze team strength differentials and their live manifestation.
            """,
            
            'GoalContinuation': """
🧠 **EDUCATIONAL CONTEXT - Goal Continuation Pattern**

This pattern identifies matches where early goals suggest more goals are likely to follow.

**Why This Pattern Works:**
- Open games with space tend to produce more goals
- High xG suggests quality chances are being created regularly
- Time remaining allows for additional goals
- Team scoring tendencies tend to continue in the same match

**Learning Objective:**
Learn to recognize goal-scoring patterns and momentum in live matches.
            """,
            
            'SafeBTTS': """
🧠 **EDUCATIONAL CONTEXT - Safe BTTS Pattern**

This pattern identifies matches where both teams have scoring capabilities and defensive vulnerabilities.

**Why This Pattern Works:**
- Both teams showing attacking threat in current match
- Historical data suggests both teams can score
- Losing team creating chances (not completely dominated)
- Time remaining allows for the trailing team to equalize

**Learning Objective:**
Understand how to assess whether both teams are likely to score based on live indicators.
            """
        }
        
        base_context = contexts.get(pattern_name, "Educational pattern analysis context")
        
        educational_note = f"""
**LEARNING OBJECTIVE:**
This signal demonstrates how {confidence:.0%} confidence can be calculated using multiple data points. The historical success rate for this pattern is {expected_hitrate:.0%}, but individual results vary.

**⚠️ REMEMBER:** This is for educational analysis only. No real money betting.
        """
        
        return base_context + educational_note

class NotificationManager:
    """Manage signal notifications with educational focus"""
    
    def __init__(self, safety_protocols: SafetyProtocols):
        self.safety = safety_protocols
        self.logger = logging.getLogger(__name__)
        self.notification_history = []
        self.daily_signal_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Telegram bot configuration (educational mode)
        self.telegram_config = {
            'enabled': False,  # Disabled for educational mode
            'bot_token': None,
            'chat_id': None,
            'educational_mode': True
        }
    
    def reset_daily_counters(self):
        """Reset daily counters at configured hour"""
        now = datetime.now()
        if (now.hour >= self.safety.safety_config['daily_reset_hour'] and 
            self.last_reset_date != now.date()):
            self.daily_signal_count = 0
            self.last_reset_date = now.date()
            self.logger.info("Daily counters reset")
    
    def format_signal_message(self, signal: Signal) -> str:
        """Format educational signal message"""
        
        match = signal.match_data
        result = signal.pattern_result
        
        # Basic match info
        home_team = match.get('home_team', 'Unknown')
        away_team = match.get('away_team', 'Unknown')
        league = match.get('league', 'Unknown League')
        minute = match.get('minute', 0)
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        
        # Confidence level formatting
        confidence = result.confidence
        if confidence >= 0.85:
            confidence_emoji = "🔥"
            confidence_text = "VERY HIGH"
        elif confidence >= 0.80:
            confidence_emoji = "⚡"
            confidence_text = "HIGH"
        elif confidence >= 0.75:
            confidence_emoji = "📊"
            confidence_text = "MODERATE-HIGH"
        else:
            confidence_emoji = "⚠️"
            confidence_text = "BELOW THRESHOLD"
        
        message = f"""
🎯 **EDUCATIONAL SIGNAL** - {confidence_emoji}

{'='*60}
⚽ **{home_team} vs {away_team}**
🏆 {league}
⏱️ {minute}' | Score: {home_score}-{away_score}

💡 **PATTERN:** {result.pattern_name}
🎰 **BET:** {result.bet}
💰 **ODDS RANGE:** {signal.odds_range[0]:.2f} - {signal.odds_range[1]:.2f}
📊 **CONFIDENCE:** {confidence:.0%} ({confidence_text})
🎯 **EXPECTED HITRATE:** {signal.expected_hitrate:.0%}
🔍 **RISK LEVEL:** {signal.risk_assessment}

📈 **ANALYSIS REASONING:**
{result.reasoning}

🔑 **KEY FACTORS:**
{', '.join(result.key_factors)}

{self.safety.disclaimers['general']}
{self.safety.disclaimers['analysis']}

**⚠️ EDUCATIONAL NOTICE:** This is simulated analysis for learning purposes only.
**DO NOT:** Place real money bets based on this analysis.
**LEARN FROM:** Pattern recognition, confidence calculation, risk assessment.
        """
        
        return message
    
    async def send_notification(self, signal: Signal) -> bool:
        """Send educational notification (simulated in educational mode)"""
        
        try:
            # Reset daily counters if needed
            self.reset_daily_counters()
            
            # Check daily limits
            if self.daily_signal_count >= self.safety.safety_config['max_daily_signals']:
                self.logger.warning("Daily signal limit reached")
                return False
            
            # Format message
            message = self.format_signal_message(signal)
            
            # Simulate notification (educational mode)
            self.logger.info(f"EDUCATIONAL SIGNAL GENERATED:")
            self.logger.info(f"Signal ID: {signal.signal_id}")
            self.logger.info(f"Pattern: {signal.pattern_result.pattern_name}")
            self.logger.info(f"Confidence: {signal.pattern_result.confidence:.0%}")
            self.logger.info(f"Match: {signal.match_data.get('home_team')} vs {signal.match_data.get('away_team')}")
            
            # Add to notification history
            self.notification_history.append({
                'timestamp': signal.timestamp.isoformat(),
                'signal_id': signal.signal_id,
                'pattern': signal.pattern_result.pattern_name,
                'confidence': signal.pattern_result.confidence,
                'match': f"{signal.match_data.get('home_team')} vs {signal.match_data.get('away_team')}"
            })
            
            # Save to file for educational review
            await self.save_signal_to_file(signal)
            
            # Increment counter
            self.daily_signal_count += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
    async def save_signal_to_file(self, signal: Signal):
        """Save signal to file for educational analysis"""
        
        try:
            # Ensure directory exists
            os.makedirs('educational_signals', exist_ok=True)
            
            # Save individual signal
            filename = f"educational_signals/signal_{signal.signal_id}.json"
            with open(filename, 'w') as f:
                json.dump(signal.to_dict(), f, indent=2)
            
            # Append to daily log
            daily_log = f"educational_signals/daily_signals_{datetime.now().strftime('%Y%m%d')}.csv"
            
            signal_data = {
                'timestamp': signal.timestamp.isoformat(),
                'signal_id': signal.signal_id,
                'home_team': signal.match_data.get('home_team'),
                'away_team': signal.match_data.get('away_team'),
                'league': signal.match_data.get('league'),
                'minute': signal.match_data.get('minute'),
                'score': f"{signal.match_data.get('home_score', 0)}-{signal.match_data.get('away_score', 0)}",
                'pattern': signal.pattern_result.pattern_name,
                'bet': signal.pattern_result.bet,
                'confidence': signal.pattern_result.confidence,
                'expected_hitrate': signal.expected_hitrate,
                'risk_level': signal.risk_assessment,
                'reasoning': signal.pattern_result.reasoning
            }
            
            # Create DataFrame and append
            df_new = pd.DataFrame([signal_data])
            
            if os.path.exists(daily_log):
                df_existing = pd.read_csv(daily_log)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
            
            df_combined.to_csv(daily_log, index=False)
            
        except Exception as e:
            self.logger.error(f"Error saving signal to file: {e}")
    
    def get_notification_stats(self) -> Dict:
        """Get notification statistics for educational analysis"""
        
        total_signals = len(self.notification_history)
        today_signals = sum(1 for h in self.notification_history 
                          if h['timestamp'][:10] == datetime.now().strftime('%Y-%m-%d'))
        
        # Pattern distribution
        pattern_counts = {}
        for h in self.notification_history:
            pattern = h['pattern']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Confidence distribution
        confidence_ranges = {
            'Very High (85%+)': sum(1 for h in self.notification_history if h['confidence'] >= 0.85),
            'High (80-84%)': sum(1 for h in self.notification_history if 0.80 <= h['confidence'] < 0.85),
            'Moderate (75-79%)': sum(1 for h in self.notification_history if 0.75 <= h['confidence'] < 0.80)
        }
        
        return {
            'total_signals_generated': total_signals,
            'today_signals': today_signals,
            'daily_limit': self.safety.safety_config['max_daily_signals'],
            'pattern_distribution': pattern_counts,
            'confidence_distribution': confidence_ranges,
            'educational_mode': self.safety.safety_config['educational_mode']
        }

class SignalGenerator:
    """Main signal generation system"""
    
    def __init__(self, api_football_key: str):
        self.api_key = api_football_key
        self.safety = SafetyProtocols()
        self.notification = NotificationManager(self.safety)
        self.pattern_manager = PatternManager()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config = {
            'update_interval': 60,  # seconds
            'min_confidence': 0.75,
            'max_signals_per_hour': 5,
            'pattern_cooldown': 300  # 5 minutes between same pattern signals
        }
        
        # State tracking
        self.last_signals = {}
        self.signal_history = []
        
    async def generate_signals(self) -> List[Signal]:
        """Generate signals from live data"""
        
        signals = []
        
        try:
            # Get live matches
            async with APIFootballScraper(self.api_key) as scraper:
                live_matches = await scraper.get_live_fixtures()
                
                if not live_matches:
                    self.logger.info("No live matches found")
                    return signals
                
                self.logger.info(f"Analyzing {len(live_matches)} live matches")
                
                # Enrich matches with prematch data
                enriched_matches = await scraper.enrich_live_matches(live_matches)
                
                # Analyze each match
                for match in enriched_matches:
                    match_signals = await self.analyze_match_signals(match)
                    signals.extend(match_signals)
                
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
        
        return signals
    
    async def analyze_match_signals(self, match: Dict) -> List[Signal]:
        """Analyze individual match for signals"""
        
        match_signals = []
        
        try:
            # Get best signal from patterns
            best_signal = self.pattern_manager.get_best_signal(
                match, 
                min_confidence=self.config['min_confidence']
            )
            
            if not best_signal:
                return match_signals
            
            # Check cooldown
            match_key = f"{match.get('home_team', '')}vs{match.get('away_team', '')}"
            if self.is_in_cooldown(match_key, best_signal.pattern_name):
                return match_signals
            
            # Create signal
            signal = Signal(
                signal_id=f"{match.get('fixture_id', 'unknown')}_{best_signal.pattern_name}_{int(datetime.now().timestamp())}",
                match_data=match,
                pattern_result=best_signal,
                timestamp=datetime.now(),
                confidence_level=self.get_confidence_level(best_signal.confidence),
                odds_range=best_signal.odds_range,
                expected_hitrate=best_signal.expected_hitrate,
                risk_assessment=best_signal.risk_level,
                educational_context=self.safety.generate_educational_context(
                    Signal("", match, best_signal, datetime.now(), "", best_signal.odds_range, best_signal.expected_hitrate, "", "")
                )
            )
            
            # Validate signal
            is_safe, violations = self.safety.validate_signal(signal)
            
            if is_safe:
                match_signals.append(signal)
                self.last_signals[match_key] = {
                    'pattern': best_signal.pattern_name,
                    'timestamp': datetime.now()
                }
            else:
                self.logger.warning(f"Signal failed safety validation: {violations}")
                
        except Exception as e:
            self.logger.error(f"Error analyzing match signals: {e}")
        
        return match_signals
    
    def is_in_cooldown(self, match_key: str, pattern_name: str) -> bool:
        """Check if signal is in cooldown period"""
        
        if match_key not in self.last_signals:
            return False
        
        last_signal = self.last_signals[match_key]
        cooldown_end = last_signal['timestamp'] + timedelta(seconds=self.config['pattern_cooldown'])
        
        return datetime.now() < cooldown_end
    
    def get_confidence_level(self, confidence: float) -> str:
        """Get confidence level string"""
        
        if confidence >= 0.85:
            return "VERY_HIGH"
        elif confidence >= 0.80:
            return "HIGH"
        elif confidence >= 0.75:
            return "MODERATE_HIGH"
        else:
            return "BELOW_THRESHOLD"
    
    async def run_signal_generation(self):
        """Run continuous signal generation"""
        
        self.logger.info("Starting educational signal generation system")
        self.logger.info("⚠️ EDUCATIONAL MODE - NO REAL MONEY BETTING")
        
        while True:
            try:
                # Generate signals
                signals = await self.generate_signals()
                
                if signals:
                    self.logger.info(f"Generated {len(signals)} educational signals")
                    
                    # Send notifications
                    for signal in signals:
                        success = await self.notification.send_notification(signal)
                        if success:
                            self.signal_history.append(signal)
                
                # Wait before next iteration
                await asyncio.sleep(self.config['update_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Signal generation stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        
        return {
            'pattern_manager_stats': self.pattern_manager.get_pattern_performance(),
            'notification_stats': self.notification.get_notification_stats(),
            'config': self.config,
            'safety_config': self.safety.safety_config,
            'total_signals_generated': len(self.signal_history)
        }
    
    async def test_system(self, sample_match_data: Dict = None) -> Dict:
        """Test the system with sample data"""
        
        if not sample_match_data:
            # Create sample match data for testing
            sample_match_data = {
                'fixture_id': 'test_123',
                'home_team': 'Test Team A',
                'away_team': 'Test Team B',
                'league': 'Educational League',
                'home_score': 1,
                'away_score': 0,
                'minute': 78,
                'prematch_data': {
                    'elo_difference': 120,
                    'home_form': {'win_rate': 0.70},
                    'away_form': {'win_rate': 0.30},
                    'head_to_head': {'team1_wins': 3, 'total_matches': 5},
                    'home_ratings': {'avg_goals_for': 1.8, 'clean_sheet_rate': 0.4},
                    'away_ratings': {'avg_goals_for': 1.2, 'clean_sheet_rate': 0.2}
                },
                'statistics': {
                    'home_stats': {'Expected goals (xG)': '1.2', 'Total Shots': '8', 'Ball Possession': '65%'},
                    'away_stats': {'Expected goals (xG)': '0.4', 'Total Shots': '3', 'Ball Possession': '35%'}
                }
            }
        
        # Test pattern analysis
        results = self.pattern_manager.analyze_match(sample_match_data)
        
        # Test signal generation
        signal = None
        if results and results[0].confidence >= self.config['min_confidence']:
            best_result = results[0]
            signal = Signal(
                signal_id="test_signal_001",
                match_data=sample_match_data,
                pattern_result=best_result,
                timestamp=datetime.now(),
                confidence_level=self.get_confidence_level(best_result.confidence),
                odds_range=best_result.odds_range,
                expected_hitrate=best_result.expected_hitrate,
                risk_assessment=best_result.risk_level,
                educational_context=self.safety.generate_educational_context(
                    Signal("", sample_match_data, best_result, datetime.now(), "", best_result.odds_range, best_result.expected_hitrate, "", "")
                )
            )
            
            is_safe, violations = self.safety.validate_signal(signal)
            
            return {
                'test_successful': True,
                'patterns_analyzed': len(results),
                'signals_generated': 1 if signal else 0,
                'safety_validation': {
                    'passed': is_safe,
                    'violations': violations
                },
                'best_pattern': {
                    'name': best_result.pattern_name,
                    'confidence': best_result.confidence,
                    'bet': best_result.bet,
                    'reasoning': best_result.reasoning
                },
                'system_ready': is_safe and len(results) > 0
            }
        else:
            return {
                'test_successful': True,
                'patterns_analyzed': len(results),
                'signals_generated': 0,
                'reason': 'No patterns met confidence threshold',
                'system_ready': False
            }