"""
Real-time alerts for opportunities
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ALERT_EMAIL, GMAIL_USER, GMAIL_PASS

logger = logging.getLogger(__name__)


class AlertSystem:
    """Real-time alerts for opportunities"""

    def __init__(self):
        self.email = ALERT_EMAIL
        self.gmail_user = GMAIL_USER
        self.gmail_pass = GMAIL_PASS

    def alert_arbitrage(self, arb_data: Dict):
        """
        URGENT: Arbitrage found
        
        Args:
            arb_data: Dict with arbitrage information
        """
        message = f"""
        ⚡ ARBITRAGE OPPORTUNITY DETECTED

        Match: {arb_data.get('match_name', 'Unknown')}
        Book A: {arb_data.get('book_a', 'Unknown')} @ {arb_data.get('odds_a', 0):.2f}
        Book B: {arb_data.get('book_b', 'Unknown')} @ {arb_data.get('odds_b', 0):.2f}
        Guaranteed profit: {arb_data.get('arbitrage_percent', 0):.2f}% (€{arb_data.get('expected_profit', 0):.2f})

        ACTION: Place both bets immediately!
        """
        self.send_alert(message, level="CRITICAL", subject="⚡ Arbitrage Opportunity")

    def alert_line_movement(self, movement_data: Dict):
        """
        Line moved in our favor
        
        Args:
            movement_data: Dict with line movement information
        """
        if movement_data.get('recommendation') == "LAYER_BET":
            message = f"""
            📈 LINE MOVEMENT OPPORTUNITY

            Match: {movement_data.get('match_name', 'Unknown')}
            Original odds: {movement_data.get('original_odds', 0):.2f}
            Current odds: {movement_data.get('current_odds', 0):.2f}
            Movement: {movement_data.get('movement_magnitude', 0):.1f}%
            Additional edge: {movement_data.get('edge_opportunity', 0):.1f}%

            ACTION: Layer bet (add €{movement_data.get('suggested_stake', 0):.0f})
            """
            self.send_alert(message, level="HIGH", subject="📈 Line Movement Opportunity")

    def alert_high_confidence_play(self, play_data: Dict):
        """
        High-confidence play found
        
        Args:
            play_data: Dict with play information
        """
        if play_data.get('total_edge', 0) > 10 and play_data.get('confidence', 0) >= 8:
            message = f"""
            ✨ ELITE PLAY IDENTIFIED

            Match: {play_data.get('match_name', 'Unknown')}
            Total edge: {play_data.get('total_edge', 0):.1f}%
            Confidence: {play_data.get('confidence', 0)}/10
            Best book: {play_data.get('best_book', 'Unknown')}
            Odds: {play_data.get('best_odds', 0):.2f}
            Stake: €{play_data.get('stake', 0):.0f}
            Expected win: €{play_data.get('potential_win', 0):.0f}

            ACTION: Place immediately
            """
            self.send_alert(message, level="CRITICAL", subject="✨ Elite Play Identified")

    def send_alert(self, message: str, level: str = "INFO", subject: str = None):
        """
        Send email alert
        
        Args:
            message: Alert message
            level: Alert level (INFO, HIGH, CRITICAL)
            subject: Email subject (optional)
        """
        logger.info(f"[{level}] {message}")

        if not self.email or not self.gmail_user or not self.gmail_pass:
            logger.warning("Email credentials not configured. Skipping email alert.")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.email
            msg['Subject'] = subject or f"[BetFlow Pro] {level}"

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_pass)
            server.send_message(msg)
            server.quit()

            logger.info(f"Alert email sent to {self.email}")

        except Exception as e:
            logger.error(f"Error sending alert email: {e}")

    def send_sms(self, message: str, phone: str = None):
        """
        Send SMS alert (requires Twilio or similar service)
        
        Args:
            message: Alert message
            phone: Phone number (optional, uses config if not provided)
        """
        # SMS implementation would require Twilio or similar service
        # Placeholder for future implementation
        logger.info(f"SMS alert (not implemented): {message}")
        pass

