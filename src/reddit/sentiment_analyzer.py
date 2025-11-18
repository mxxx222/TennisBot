"""
Sentiment Analyzer

NLP-based sentiment analysis for Reddit posts and comments
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Sentiment analysis using VADER and TextBlob"""
    
    def __init__(self):
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
            except Exception as e:
                logger.warning(f"Failed to initialize VADER: {e}")
        
        logger.info("✅ Sentiment Analyzer initialized")
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text
        
        Returns:
            Dictionary with sentiment scores:
            - compound: Overall sentiment (-1 to 1)
            - positive: Positive sentiment (0 to 1)
            - negative: Negative sentiment (0 to 1)
            - neutral: Neutral sentiment (0 to 1)
            - polarity: TextBlob polarity (-1 to 1)
            - subjectivity: TextBlob subjectivity (0 to 1)
        """
        if not text or len(text.strip()) < 3:
            return {
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'polarity': 0.0,
                'subjectivity': 0.5
            }
        
        results = {
            'compound': 0.0,
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 0.0,
            'polarity': 0.0,
            'subjectivity': 0.5
        }
        
        # VADER sentiment
        if self.vader_analyzer:
            try:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                results.update({
                    'compound': vader_scores['compound'],
                    'positive': vader_scores['pos'],
                    'negative': vader_scores['neg'],
                    'neutral': vader_scores['neu']
                })
            except Exception as e:
                logger.debug(f"VADER analysis error: {e}")
        
        # TextBlob sentiment
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                results['polarity'] = blob.sentiment.polarity
                results['subjectivity'] = blob.sentiment.subjectivity
            except Exception as e:
                logger.debug(f"TextBlob analysis error: {e}")
        
        return results
    
    def get_sentiment_label(self, sentiment_scores: Dict[str, float]) -> str:
        """Get sentiment label from scores"""
        compound = sentiment_scores.get('compound', 0.0)
        
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_match_sentiment(
        self,
        posts: List[Dict[str, Any]],
        home_team: str,
        away_team: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific match from Reddit posts
        
        Returns:
            Dictionary with sentiment analysis:
            - home_sentiment: Sentiment towards home team
            - away_sentiment: Sentiment towards away team
            - home_percentage: Percentage favoring home team
            - away_percentage: Percentage favoring away team
            - neutral_percentage: Percentage neutral
            - total_mentions: Total mentions of the match
            - confidence: Confidence in sentiment analysis
        """
        home_mentions = []
        away_mentions = []
        neutral_mentions = []
        
        home_keywords = self._extract_team_keywords(home_team)
        away_keywords = self._extract_team_keywords(away_team)
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
            
            # Check if post mentions the match
            mentions_home = any(kw in text for kw in home_keywords)
            mentions_away = any(kw in text for kw in away_keywords)
            
            if not (mentions_home or mentions_away):
                continue
            
            # Analyze sentiment
            full_text = f"{post.get('title', '')} {post.get('selftext', '')}"
            sentiment = self.analyze_sentiment(full_text)
            
            # Categorize
            if mentions_home and mentions_away:
                # Mentions both teams - check which is favored
                if sentiment['compound'] > 0.1:
                    # Positive sentiment - check which team is mentioned more positively
                    if text.count(home_team.lower()) > text.count(away_team.lower()):
                        home_mentions.append(sentiment)
                    else:
                        away_mentions.append(sentiment)
                elif sentiment['compound'] < -0.1:
                    # Negative sentiment - opposite team benefits
                    if text.count(home_team.lower()) > text.count(away_team.lower()):
                        away_mentions.append(sentiment)
                    else:
                        home_mentions.append(sentiment)
                else:
                    neutral_mentions.append(sentiment)
            elif mentions_home:
                home_mentions.append(sentiment)
            elif mentions_away:
                away_mentions.append(sentiment)
        
        # Calculate percentages
        total_mentions = len(home_mentions) + len(away_mentions) + len(neutral_mentions)
        
        if total_mentions == 0:
            return {
                'home_sentiment': 0.0,
                'away_sentiment': 0.0,
                'home_percentage': 50.0,
                'away_percentage': 50.0,
                'neutral_percentage': 0.0,
                'total_mentions': 0,
                'confidence': 0.0
            }
        
        home_percentage = (len(home_mentions) / total_mentions) * 100
        away_percentage = (len(away_mentions) / total_mentions) * 100
        neutral_percentage = (len(neutral_mentions) / total_mentions) * 100
        
        # Calculate average sentiment
        home_avg_sentiment = (
            sum(m.get('compound', 0) for m in home_mentions) / len(home_mentions)
            if home_mentions else 0.0
        )
        away_avg_sentiment = (
            sum(m.get('compound', 0) for m in away_mentions) / len(away_mentions)
            if away_mentions else 0.0
        )
        
        # Confidence based on number of mentions
        confidence = min(1.0, total_mentions / 20.0)  # Max confidence at 20+ mentions
        
        return {
            'home_sentiment': round(home_avg_sentiment, 3),
            'away_sentiment': round(away_avg_sentiment, 3),
            'home_percentage': round(home_percentage, 1),
            'away_percentage': round(away_percentage, 1),
            'neutral_percentage': round(neutral_percentage, 1),
            'total_mentions': total_mentions,
            'confidence': round(confidence, 2),
            'home_mentions_count': len(home_mentions),
            'away_mentions_count': len(away_mentions)
        }
    
    def _extract_team_keywords(self, team_name: str) -> List[str]:
        """Extract keywords from team name for matching"""
        keywords = [team_name.lower()]
        
        # Split team name into words
        words = team_name.lower().split()
        keywords.extend(words)
        
        # Add common variations
        if len(words) > 1:
            # First word only
            keywords.append(words[0])
            # Last word only
            keywords.append(words[-1])
        
        return keywords

