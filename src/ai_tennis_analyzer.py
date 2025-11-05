#!/usr/bin/env python3
"""
🎾 AI TENNIS ANALYSIS SYSTEM
===========================

Educational AI-powered tennis betting analysis system
Uses OpenAI GPT-4 for expert tennis match analysis
Maximum ROI with proper risk management

Author: Betfury.io Educational Research System
Version: 1.0.0
Educational Purpose: NO REAL MONEY
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

# OpenAI integration with security
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Local imports with security
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security_manager import SecurityManager, APISecurityManager

class SurfaceType(Enum):
    CLAY = "Clay"
    HARD = "Hard"  
    GRASS = "Grass"
    INDOOR = "Indoor"

class BetType(Enum):
    MATCH_WIN = "Match Win"
    SETS_OVER = "Over 2.5 Sets"
    SETS_UNDER = "Under 2.5 Sets"
    GAME_TOTAL = "Total Games"
    HANDICAP = "Handicap"

@dataclass
class PlayerStats:
    name: str
    ranking: int
    win_rate_surface: Dict[str, float]
    recent_form: str
    h2h_record: Dict[str, int]
    surface_preference: float
    fitness_status: str
    mental_toughness: float
    serving_strength: float
    return_strength: float

@dataclass
class TennisMatch:
    player1: str
    player2: str
    tournament: str
    surface: SurfaceType
    date: str
    round: str
    odds: Dict[str, float]
    court_type: str = ""
    weather_conditions: str = ""

@dataclass
class BettingAnalysis:
    prediction: str
    confidence: float
    reasoning: str
    value_rating: str
    risk_level: str
    recommended_stake: float
    kelly_percentage: float
    expected_value: float
    match_analysis: Dict[str, any]
    key_factors: List[str]

@dataclass
class EducationalTip:
    match: TennisMatch
    analysis: BettingAnalysis
    educational_note: str
    risk_warning: str
    learning_objective: str

class OpenAITennisAnalyzer:
    """Educational AI Tennis Analysis System with GitHub Secrets Integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_manager = SecurityManager()
        self.api_manager = APISecurityManager()
        self.client = None
        
        if OPENAI_AVAILABLE:
            self._initialize_openai()
        else:
            self.logger.warning("OpenAI library not available - using educational mode")
    
    def _initialize_openai(self):
        """Initialize OpenAI client with GitHub Secrets"""
        try:
            # Get OpenAI API key from GitHub Secrets or environment
            api_key = self.security_manager.secrets_manager.get_secret('OPENAI_API_KEY')
            
            if not api_key:
                self.logger.error("OpenAI API key not found in GitHub Secrets or environment")
                return
            
            self.client = OpenAI(api_key=api_key)
            self.logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None
    
    def analyze_match_ai(self, match: TennisMatch, stats: Dict[str, PlayerStats]) -> Optional[BettingAnalysis]:
        """Analyze tennis match using OpenAI GPT-4"""
        
        if not self.client:
            return self._fallback_analysis(match, stats)
        
        # Rate limiting check
        if not self.api_manager.check_rate_limit('openai_tennis', limit=50):
            self.logger.warning("OpenAI rate limit exceeded")
            return self._fallback_analysis(match, stats)
        
        try:
            prompt = self._create_educational_analysis_prompt(match, stats)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_tennis_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                timeout=30
            )
            
            analysis_text = response.choices[0].message.content
            return self._parse_ai_analysis(analysis_text, match, stats)
            
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return self._fallback_analysis(match, stats)
    
    def _get_tennis_system_prompt(self) -> str:
        """Get comprehensive tennis analysis system prompt"""
        return """
        You are an expert tennis betting analyst and sports data scientist with 15+ years of experience.
        You specialize in educational tennis analysis for learning purposes.
        
        EDUCATIONAL OBJECTIVES:
        - Teach proper tennis match analysis methodology
        - Demonstrate risk assessment techniques  
        - Show value betting identification
        - Explain betting psychology and discipline
        
        ANALYSIS FRAMEWORK:
        1. Player Performance Analysis
           - Head-to-head records and patterns
           - Surface-specific performance metrics
           - Recent form and momentum
           - Physical and mental condition
        
        2. Match Context Analysis
           - Tournament importance and pressure
           - Surface and conditions impact
           - Playing style matchups
           - Historical patterns
        
        3. Market Analysis
           - Odds comparison and value identification
           - Public betting patterns impact
           - Line movement analysis
           - Risk-reward assessment
        
        4. Educational Commentary
           - Explain reasoning in educational terms
           - Highlight key learning points
           - Emphasize risk management importance
           - Stress gambling responsibility
        
        OUTPUT FORMAT (JSON):
        {
            "prediction": "detailed outcome prediction",
            "confidence": 0.75,
            "reasoning": "educational explanation of analysis",
            "value_rating": "HIGH/MEDIUM/LOW",
            "risk_level": "CONSERVATIVE/MODERATE/AGGRESSIVE", 
            "key_factors": ["factor1", "factor2", "factor3"],
            "match_analysis": {
                "player1_strengths": ["..."],
                "player2_strengths": ["..."],
                "key_matchup": "analysis",
                "surface_impact": "explanation",
                "psychological_factors": ["..."]
            },
            "educational_notes": "teaching points about the analysis"
        }
        
        FOCUS AREAS:
        - Emphasize educational value over pure prediction
        - Always include risk management advice
        - Highlight learning opportunities
        - Stress responsible gambling principles
        
        CRITICAL: This is for educational purposes. Always remind that real gambling involves real money risk.
        """
    
    def _create_educational_analysis_prompt(self, match: TennisMatch, stats: Dict[str, PlayerStats]) -> str:
        """Create comprehensive educational analysis prompt"""
        
        p1_stats = stats.get(match.player1)
        p2_stats = stats.get(match.player2)
        
        if not p1_stats or not p2_stats:
            return self._create_fallback_prompt(match)
        
        prompt = f"""
        EDUCATIONAL TENNIS MATCH ANALYSIS REQUEST
        
        MATCH DETAILS:
        - Players: {match.player1} vs {match.player2}
        - Tournament: {match.tournament} ({match.round})
        - Surface: {match.surface.value}
        - Date: {match.date}
        
        CURRENT ODDS (Educational Bookmaker):
        - {match.player1}: {match.odds.get('player1', 'N/A')}
        - {match.player2}: {match.odds.get('player2', 'N/A')}
        
        EDUCATIONAL ANALYSIS FOCUS:
        
        PLAYER 1: {match.player1}
        - Ranking: #{p1_stats.ranking}
        - Surface Win Rate: {p1_stats.win_rate_surface.get(match.surface.value, 0):.1%}
        - Recent Form: {p1_stats.recent_form}
        - Fitness Status: {p1_stats.fitness_status}
        - Mental Toughness: {p1_stats.mental_toughness:.1f}/10
        - Strengths: Serving({p1_stats.serving_strength:.1f}), Returning({p1_stats.return_strength:.1f})
        
        PLAYER 2: {match.player2}  
        - Ranking: #{p2_stats.ranking}
        - Surface Win Rate: {p2_stats.win_rate_surface.get(match.surface.value, 0):.1%}
        - Recent Form: {p2_stats.recent_form}
        - Fitness Status: {p2_stats.fitness_status}
        - Mental Toughness: {p2_stats.mental_toughness:.1f}/10
        - Strengths: Serving({p2_stats.serving_strength:.1f}), Returning({p2_stats.return_strength:.1f})
        
        HEAD-TO-HEAD:
        - Total Meetings: {p1_stats.h2h_record.get('total', 0)}
        - {match.player1} Wins: {p1_stats.h2h_record.get('wins', 0)}
        - {match.player2} Wins: {p2_stats.h2h_record.get('wins', 0)}
        
        EDUCATIONAL ANALYSIS TASKS:
        1. Identify the most probable outcome with confidence level
        2. Explain key factors influencing the match
        3. Assess value vs current odds
        4. Provide educational insights about tennis analysis
        5. Emphasize risk management principles
        
        OUTPUT FORMAT: JSON as specified in system prompt with educational emphasis.
        
        Remember: This is for educational purposes only. Always stress responsible analysis and gambling awareness.
        """
        
        return prompt
    
    def _parse_ai_analysis(self, analysis_text: str, match: TennisMatch, stats: Dict) -> BettingAnalysis:
        """Parse AI response into structured analysis"""
        try:
            # Extract JSON from response
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return self._fallback_analysis(match, stats)
            
            json_text = analysis_text[json_start:json_end]
            data = json.loads(json_text)
            
            # Calculate Kelly Criterion and stake
            confidence = data.get('confidence', 0.5)
            odds = match.odds.get('player1', 2.0)
            kelly = self._calculate_kelly_percentage(confidence, odds)
            stake = self._calculate_educational_stake(confidence, kelly)
            
            return BettingAnalysis(
                prediction=data.get('prediction', 'Analysis unavailable'),
                confidence=confidence,
                reasoning=data.get('reasoning', 'Educational analysis not available'),
                value_rating=data.get('value_rating', 'MEDIUM'),
                risk_level=data.get('risk_level', 'MODERATE'),
                recommended_stake=stake,
                kelly_percentage=kelly,
                expected_value=confidence * odds - 1,
                match_analysis=data.get('match_analysis', {}),
                key_factors=data.get('key_factors', [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI analysis: {e}")
            return self._fallback_analysis(match, stats)
    
    def _fallback_analysis(self, match: TennisMatch, stats: Dict) -> BettingAnalysis:
        """Fallback analysis when AI is unavailable"""
        p1_stats = stats.get(match.player1)
        p2_stats = stats.get(match.player2)
        
        if not p1_stats or not p2_stats:
            # Return basic analysis when stats are missing
            return self._basic_analysis(match)
        
        # Simple statistical analysis
        surface_rate1 = p1_stats.win_rate_surface.get(match.surface.value, 0.5)
        surface_rate2 = p2_stats.win_rate_surface.get(match.surface.value, 0.5)
        
        # Combined factors
        p1_strength = (surface_rate1 + p1_stats.mental_toughness/10) / 2
        p2_strength = (surface_rate2 + p2_stats.mental_toughness/10) / 2
        
        # Calculate confidence
        confidence = 0.5 + (p1_strength - p2_strength) * 0.3
        confidence = max(0.3, min(0.95, confidence))  # Clamp between 30% and 95%
        
        # Determine winner
        if p1_strength > p2_strength:
            prediction = f"{match.player1} wins"
            odds = match.odds.get('player1', 2.0)
        else:
            prediction = f"{match.player2} wins"
            odds = match.odds.get('player2', 2.0)
        
        kelly = self._calculate_kelly_percentage(confidence, odds)
        stake = self._calculate_educational_stake(confidence, kelly)
        
        return BettingAnalysis(
            prediction=prediction,
            confidence=confidence,
            reasoning=f"Based on surface performance: {match.player1} ({surface_rate1:.1%}) vs {match.player2} ({surface_rate2:.1%})",
            value_rating="MEDIUM" if confidence > 0.6 else "LOW",
            risk_level="CONSERVATIVE" if confidence > 0.7 else "MODERATE",
            recommended_stake=stake,
            kelly_percentage=kelly,
            expected_value=confidence * odds - 1,
            match_analysis={
                "player1_strengths": ["Surface preference", "Mental toughness"],
                "player2_strengths": ["Ranking advantage", "Recent form"],
                "key_matchup": f"Surface analysis: {match.surface.value}",
                "surface_impact": f"Both players' {match.surface.value} performance",
                "psychological_factors": ["Tournament pressure", "Form confidence"]
            },
            key_factors=[f"{match.surface.value} surface performance", "Mental strength", "Recent form"]
        )
    
    def _create_fallback_prompt(self, match: TennisMatch) -> str:
        """Create basic prompt for fallback analysis"""
        return f"""
        Basic tennis analysis for educational purposes:
        
        Match: {match.player1} vs {match.player2}
        Surface: {match.surface.value}
        Tournament: {match.tournament}
        
        Provide educational analysis focusing on general tennis factors.
        """
    
    def _basic_analysis(self, match: TennisMatch) -> BettingAnalysis:
        """Basic analysis when insufficient data"""
        return BettingAnalysis(
            prediction="Insufficient data for analysis",
            confidence=0.50,
            reasoning="Educational note: This demonstrates why thorough research is essential before making any betting decisions.",
            value_rating="LOW",
            risk_level="HIGH",
            recommended_stake=0,
            kelly_percentage=0,
            expected_value=0,
            match_analysis={
                "player1_strengths": ["Research needed"],
                "player2_strengths": ["Research needed"],
                "key_matchup": "Insufficient data available",
                "surface_impact": "Analysis requires more information",
                "psychological_factors": ["Cannot assess without research"]
            },
            key_factors=["Research essential", "Data availability", "Risk awareness"]
        )
    
    def _calculate_kelly_percentage(self, probability: float, odds: float) -> float:
        """Calculate Kelly Criterion percentage"""
        if probability >= 1 or odds <= 1:
            return 0
        
        kelly = (probability * odds - 1) / (odds - 1)
        return max(0, min(0.25, kelly))  # Conservative Kelly (max 25%)
    
    def _calculate_educational_stake(self, confidence: float, kelly: float) -> float:
        """Calculate educational stake with safety limits"""
        # Educational bankroll: 1000 units
        bankroll = 1000
        base_stake = bankroll * 0.02  # 2% base stake
        
        # Adjust based on confidence
        confidence_multiplier = confidence * 1.5
        kelly_multiplier = max(0.25, kelly * 4)  # Conservative Kelly multiplier
        
        stake = base_stake * confidence_multiplier * kelly_multiplier
        return max(5, min(50, stake))  # Educational limits: 5-50 units
    
    def get_high_value_educational_tips(self, matches: List[TennisMatch]) -> List[EducationalTip]:
        """Generate high-value educational betting tips"""
        
        tips = []
        
        for match in matches:
            # Get player statistics (mock for educational purposes)
            stats = self._generate_educational_stats(match.player1, match.player2)
            
            analysis = self.analyze_match_ai(match, stats)
            
            if analysis and analysis.confidence >= 0.65:  # Educational threshold
                educational_tip = EducationalTip(
                    match=match,
                    analysis=analysis,
                    educational_note=self._generate_educational_note(analysis),
                    risk_warning=self._generate_risk_warning(analysis),
                    learning_objective=self._generate_learning_objective(analysis)
                )
                tips.append(educational_tip)
        
        # Sort by confidence and educational value
        tips.sort(key=lambda x: (x.analysis.confidence, x.analysis.expected_value), reverse=True)
        return tips[:5]  # Top 5 educational tips
    
    def _generate_educational_stats(self, player1: str, player2: str) -> Dict[str, PlayerStats]:
        """Generate educational player statistics"""
        
        # Mock data for educational purposes
        return {
            player1: PlayerStats(
                name=player1,
                ranking=15,
                win_rate_surface={"Hard": 0.72, "Clay": 0.65, "Grass": 0.58},
                recent_form="WWLWWWWLWW",
                h2h_record={"total": 8, "wins": 5, "losses": 3},
                surface_preference=0.68,
                fitness_status="100%",
                mental_toughness=8.2,
                serving_strength=8.5,
                return_strength=7.8
            ),
            player2: PlayerStats(
                name=player2,
                ranking=12,
                win_rate_surface={"Hard": 0.68, "Clay": 0.75, "Grass": 0.62},
                recent_form="WLWWLWLWLW",
                h2h_record={"total": 8, "wins": 3, "losses": 5},
                surface_preference=0.73,
                fitness_status="95% (minor concern)",
                mental_toughness=7.8,
                serving_strength=7.9,
                return_strength=8.2
            )
        }
    
    def _generate_educational_note(self, analysis: BettingAnalysis) -> str:
        """Generate educational notes for learning"""
        notes = {
            "HIGH": "This analysis shows strong statistical correlation. Study the key factors that led to this confidence level.",
            "MEDIUM": "This is a moderate confidence analysis. Consider the risk factors mentioned in the reasoning.",
            "LOW": "Low confidence indicates high uncertainty. Use this as a learning example of difficult-to-analyze matches."
        }
        return notes.get(analysis.value_rating, "Analyze the reasoning carefully to understand the prediction factors.")
    
    def _generate_risk_warning(self, analysis: BettingAnalysis) -> str:
        """Generate educational risk warnings"""
        return f"""
        🚨 EDUCATIONAL RISK WARNING:
        • This is an educational analysis with NO REAL MONEY involved
        • Never bet more than you can afford to lose
        • Always use proper bankroll management (2% rule)
        • Past performance does not guarantee future results
        • Consider this as a learning tool for tennis analysis methodology
        """
    
    def _generate_learning_objective(self, analysis: BettingAnalysis) -> str:
        """Generate learning objectives"""
        return f"""
        🎓 LEARNING OBJECTIVES:
        • Understand how surface affects player performance
        • Learn to assess confidence levels in sports analysis
        • Practice risk-reward evaluation using the Kelly Criterion
        • Develop disciplined approach to betting analysis
        • Study the importance of proper bankroll management
        """
    
    def create_educational_report(self, tips: List[EducationalTip]) -> Dict:
        """Create comprehensive educational analysis report"""
        
        if not tips:
            return {
                "message": "No high-confidence educational tips found today",
                "analysis_date": datetime.now().isoformat(),
                "educational_focus": "Risk management and discipline"
            }
        
        report = {
            "educational_analysis_date": datetime.now().isoformat(),
            "total_tips": len(tips),
            "average_confidence": sum(t.analysis.confidence for t in tips) / len(tips),
            "educational_summary": {
                "methodology": "AI-powered tennis analysis with educational safeguards",
                "risk_management": "Kelly Criterion with conservative multipliers",
                "learning_focus": "Statistical analysis, risk assessment, and responsible gambling education"
            },
            "tips": [asdict(tip) for tip in tips],
            "educational_notes": [
                "Always research thoroughly before making any betting decisions",
                "Use proper bankroll management regardless of analysis confidence",
                "This system is for educational purposes only",
                "Real gambling involves real financial risk"
            ]
        }
        
        return report

def main():
    """Educational demonstration of AI Tennis Analysis System"""
    
    print("🎾 AI TENNIS ANALYSIS SYSTEM - EDUCATIONAL DEMO")
    print("=" * 60)
    print("⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = OpenAITennisAnalyzer()
    
    # Create sample educational matches
    matches = [
        TennisMatch(
            player1="Novak Djokovic",
            player2="Carlos Alcaraz",
            tournament="ATP Masters 1000 Paris",
            surface=SurfaceType.HARD,
            date="2025-11-06",
            round="Quarterfinals",
            odds={"player1": 1.85, "player2": 1.95}
        ),
        TennisMatch(
            player1="Iga Swiatek",
            player2="Aryna Sabalenka", 
            tournament="WTA Finals",
            surface=SurfaceType.HARD,
            date="2025-11-06",
            round="Semifinals",
            odds={"player1": 1.75, "player2": 2.10}
        )
    ]
    
    # Generate educational tips
    print("🔍 Generating educational tennis analysis...")
    tips = analyzer.get_high_value_educational_tips(matches)
    
    # Display results
    if tips:
        print(f"\n✅ Generated {len(tips)} educational tips:")
        print("-" * 40)
        
        for i, tip in enumerate(tips, 1):
            print(f"\n🎾 EDUCATIONAL TIP #{i}")
            print(f"Match: {tip.match.player1} vs {tip.match.player2}")
            print(f"Prediction: {tip.analysis.prediction}")
            print(f"Confidence: {tip.analysis.confidence:.1%}")
            print(f"Value Rating: {tip.analysis.value_rating}")
            print(f"Educational Note: {tip.educational_note}")
    else:
        print("\n📚 No high-confidence tips found.")
        print("This demonstrates the importance of selective analysis.")
    
    # Generate educational report
    report = analyzer.create_educational_report(tips)
    print(f"\n📊 Educational Report Generated:")
    print(f"- Total Analysis: {report.get('total_tips', 0)} matches")
    print(f"- Average Confidence: {report.get('average_confidence', 0):.1%}")
    print(f"- Educational Focus: {report['educational_summary']['learning_focus']}")
    
    print("\n🎓 EDUCATIONAL VALUE:")
    print("✅ Learned AI-powered sports analysis methodology")
    print("✅ Understood confidence assessment techniques")
    print("✅ Studied risk management principles")
    print("✅ Explored educational gambling awareness")
    
    print("\n🔐 SECURITY INTEGRATION:")
    print("✅ GitHub Secrets protection for API keys")
    print("✅ Rate limiting and security monitoring")
    print("✅ Educational safeguards and warnings")
    print("✅ Responsible gambling emphasis")
    
    return len(tips) > 0

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ Educational demo successful!' if success else '📚 Educational analysis complete'}")