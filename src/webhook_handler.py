#!/usr/bin/env python3
"""
Webhook Handler - Vastaanottaa ja käsittelee webhookit Zapier/Make.com:sta
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


class WebhookHandler:
    """Käsittelee webhookit ja synkronoi Notioniin"""
    
    def __init__(self, config_path: str = "config/zapier_webhooks.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.notion_sync = None
        
        # Initialize Notion sync if configured
        try:
            from src.notion_football_sync import NotionFootballSync
            self.notion_sync = NotionFootballSync()
            
            if self.notion_sync.is_configured():
                logger.info("✅ Notion sync initialized")
            else:
                logger.warning("⚠️ Notion not configured")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Notion sync: {e}")
    
    def _load_config(self) -> Dict:
        """Lataa webhook-konfiguraatio"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def handle_match_result_update(self, data: Dict) -> Dict:
        """
        Käsittele ottelutuloksen päivitys
        
        Expected data:
        {
            "match_id": str,
            "home_team": str,
            "away_team": str,
            "home_goals": int,
            "away_goals": int,
            "status": "Finished"
        }
        """
        try:
            logger.info(f"📊 Processing match result update: {data.get('home_team')} vs {data.get('away_team')}")
            
            if not self.notion_sync or not self.notion_sync.is_configured():
                return {"status": "error", "message": "Notion not configured"}
            
            # Update match in Notion
            # Note: This requires finding the match by ID or teams
            # For now, we'll log the update
            logger.info(f"✅ Match result: {data.get('home_goals')}-{data.get('away_goals')}")
            
            # TODO: Implement Notion update logic
            # 1. Find match in Notion Ottelut database
            # 2. Update Status = Finished
            # 3. Update Koti maalit, Vieras maalit
            # 4. Find related bets in Vedot database
            # 5. Update Tulos = Won/Lost based on bet type
            
            return {
                "status": "success",
                "message": "Match result updated",
                "match": f"{data.get('home_team')} {data.get('home_goals')}-{data.get('away_goals')} {data.get('away_team')}"
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling match result update: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_odds_update(self, data: Dict) -> Dict:
        """
        Käsittele kerroinpäivitys
        
        Expected data:
        {
            "match_id": str,
            "market": str,
            "odds": {
                "home": float,
                "draw": float,
                "away": float
            }
        }
        """
        try:
            logger.info(f"💰 Processing odds update for match: {data.get('match_id')}")
            
            if not self.notion_sync or not self.notion_sync.is_configured():
                return {"status": "error", "message": "Notion not configured"}
            
            # Calculate market probability
            odds = data.get('odds', {})
            if 'home' in odds:
                market_prob = (1 / odds['home']) * 100
                logger.info(f"📈 Market probability (home): {market_prob:.1f}%")
            
            # TODO: Implement Notion update logic
            # 1. Find match in Notion Analytiikka database
            # 2. Update Markkina probability %
            # 3. Check if Edge % > 4%
            # 4. If yes, send Telegram notification
            
            return {
                "status": "success",
                "message": "Odds updated",
                "match_id": data.get('match_id')
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling odds update: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_strategy_alert(self, data: Dict) -> Dict:
        """
        Käsittele strategia-alert
        
        Expected data:
        {
            "strategy_name": str,
            "alert": str,
            "win_rate": float,
            "roi": float
        }
        """
        try:
            logger.info(f"⚠️ Processing strategy alert: {data.get('strategy_name')}")
            
            alert = data.get('alert', '')
            
            if '⚠️' in alert or '❌' in alert:
                logger.warning(f"🚨 Strategy alert: {data.get('strategy_name')} - {alert}")
                
                # TODO: Send Telegram notification
                # self._send_telegram_notification(
                #     f"🚨 Strategy Alert\n\n"
                #     f"Strategy: {data.get('strategy_name')}\n"
                #     f"Alert: {alert}\n"
                #     f"Win Rate: {data.get('win_rate')}%\n"
                #     f"ROI: {data.get('roi')}%"
                # )
            
            return {
                "status": "success",
                "message": "Strategy alert processed",
                "strategy": data.get('strategy_name')
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling strategy alert: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_telegram_notification(self, message: str) -> bool:
        """Lähetä Telegram-notifikaatio"""
        try:
            import requests
            
            bot_token = self.config.get('telegram', {}).get('bot_token', '')
            chat_id = self.config.get('telegram', {}).get('chat_id', '')
            
            if not bot_token or bot_token == "PASTE_TELEGRAM_BOT_TOKEN_HERE":
                logger.warning("⚠️ Telegram not configured")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            logger.info("✅ Telegram notification sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")
            return False


# Initialize handler
webhook_handler = WebhookHandler()


# Flask routes
@app.route('/webhook/match-result', methods=['POST'])
def webhook_match_result():
    """Webhook endpoint for match results"""
    try:
        data = request.get_json()
        result = webhook_handler.handle_match_result_update(data)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook/odds-update', methods=['POST'])
def webhook_odds_update():
    """Webhook endpoint for odds updates"""
    try:
        data = request.get_json()
        result = webhook_handler.handle_odds_update(data)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook/strategy-alert', methods=['POST'])
def webhook_strategy_alert():
    """Webhook endpoint for strategy alerts"""
    try:
        data = request.get_json()
        result = webhook_handler.handle_strategy_alert(data)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "notion_configured": webhook_handler.notion_sync.is_configured() if webhook_handler.notion_sync else False
    }), 200


if __name__ == "__main__":
    logger.info("🚀 Starting Webhook Handler...")
    logger.info("📡 Listening for webhooks on http://0.0.0.0:5000")
    logger.info("")
    logger.info("Available endpoints:")
    logger.info("  POST /webhook/match-result")
    logger.info("  POST /webhook/odds-update")
    logger.info("  POST /webhook/strategy-alert")
    logger.info("  GET  /health")
    logger.info("")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

