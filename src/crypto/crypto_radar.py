"""
Crypto Radar - Reaaliaikainen crypto-hintaseuranta
Integroitu TennisBot-projektiin
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class CryptoPrice:
    """Crypto-hinnan datamalli"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: str = "coingecko"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class CryptoAlert:
    """Crypto-hälytyksen datamalli"""
    symbol: str
    alert_type: str  # 'buy', 'sell', 'price_reached'
    current_price: float
    target_price: float
    timestamp: datetime
    message: str
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CryptoRadar:
    """Crypto-hintaseuranta ja hälytysjärjestelmä"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / 'config' / 'crypto_config.json'
        self.config = self._load_config()
        self.monitored_cryptos = self.config.get('monitored_cryptos', {})
        self.price_history: Dict[str, CryptoPrice] = {}
        self.active_alerts: List[CryptoAlert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.update_interval = self.config.get('update_interval', 60)
        
        logger.info(f"🔷 CryptoRadar initialized with {len(self.monitored_cryptos)} monitored cryptos")
    
    def _load_config(self) -> Dict:
        """Lataa crypto-asetukset"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load crypto config: {e}. Using defaults.")
        
        # Oletusasetukset
        return {
            'monitored_cryptos': {
                'BTC': {'buy_threshold': 50000, 'sell_threshold': 60000, 'enabled': True},
                'ETH': {'buy_threshold': 3000, 'sell_threshold': 4000, 'enabled': True}
            },
            'update_interval': 60,  # sekuntia
            'api_provider': 'coingecko',
            'notifications': {
                'enabled': True,
                'min_change_percent': 5.0,
                'cooldown_seconds': 300
            }
        }
    
    def _symbol_to_id(self, symbol: str) -> str:
        """Muunna symboli CoinGecko ID:ksi"""
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu'
        }
        return mapping.get(symbol.upper(), symbol.lower())
    
    async def fetch_crypto_prices(self, symbols: List[str]) -> List[CryptoPrice]:
        """Hae crypto-hinnat API:sta"""
        try:
            # CoinGecko API (ilmainen, ei API-avainta tarvita)
            coin_ids = [self._symbol_to_id(s) for s in symbols]
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = []
                        for symbol in symbols:
                            coin_id = self._symbol_to_id(symbol)
                            if coin_id in data:
                                coin_data = data[coin_id]
                                prices.append(CryptoPrice(
                                    symbol=symbol,
                                    price=coin_data.get('usd', 0),
                                    change_24h=coin_data.get('usd_24h_change', 0) or 0,
                                    volume_24h=coin_data.get('usd_24h_vol', 0),
                                    timestamp=datetime.now(),
                                    source='coingecko'
                                ))
                        return prices
                    else:
                        logger.error(f"API error: {response.status}")
                        return []
        except asyncio.TimeoutError:
            logger.error("Timeout fetching crypto prices")
            return []
        except Exception as e:
            logger.error(f"Error fetching crypto prices: {e}")
            return []
    
    async def check_alerts(self, prices: List[CryptoPrice]) -> List[CryptoAlert]:
        """Tarkista onko hinnat saavuttaneet hälytysrajoja"""
        alerts = []
        cooldown = self.config.get('notifications', {}).get('cooldown_seconds', 300)
        
        for price in prices:
            symbol = price.symbol
            if symbol not in self.monitored_cryptos:
                continue
            
            crypto_config = self.monitored_cryptos[symbol]
            if not crypto_config.get('enabled', True):
                continue
            
            # Tarkista cooldown
            last_alert = self.last_alert_time.get(symbol)
            if last_alert:
                time_since = (datetime.now() - last_alert).total_seconds()
                if time_since < cooldown:
                    continue
            
            buy_threshold = crypto_config.get('buy_threshold', 0)
            sell_threshold = crypto_config.get('sell_threshold', float('inf'))
            
            # Tarkista osto-hälytys (hinta alle rajan)
            if buy_threshold > 0 and price.price <= buy_threshold:
                alert = CryptoAlert(
                    symbol=symbol,
                    alert_type='buy',
                    current_price=price.price,
                    target_price=buy_threshold,
                    timestamp=datetime.now(),
                    message=f"🟢 {symbol} BUY ALERT: Price ${price.price:,.2f} below buy threshold ${buy_threshold:,.2f}"
                )
                alerts.append(alert)
                self.last_alert_time[symbol] = datetime.now()
            
            # Tarkista myynti-hälytys (hinta yli rajan)
            if sell_threshold < float('inf') and price.price >= sell_threshold:
                alert = CryptoAlert(
                    symbol=symbol,
                    alert_type='sell',
                    current_price=price.price,
                    target_price=sell_threshold,
                    timestamp=datetime.now(),
                    message=f"🔴 {symbol} SELL ALERT: Price ${price.price:,.2f} above sell threshold ${sell_threshold:,.2f}"
                )
                alerts.append(alert)
                self.last_alert_time[symbol] = datetime.now()
        
        return alerts
    
    async def start_monitoring(self) -> AsyncGenerator[List[CryptoAlert], None]:
        """Käynnistä jatkuva crypto-seuranta"""
        symbols = [s for s, config in self.monitored_cryptos.items() 
                  if config.get('enabled', True)]
        
        if not symbols:
            logger.warning("No enabled cryptos to monitor")
            return
        
        logger.info(f"🚀 Starting crypto monitoring for: {', '.join(symbols)}")
        
        while True:
            try:
                # Hae hinnat
                prices = await self.fetch_crypto_prices(symbols)
                
                if not prices:
                    logger.warning("No prices fetched, retrying...")
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # Päivitä historia
                for price in prices:
                    self.price_history[price.symbol] = price
                
                # Tarkista hälytykset
                alerts = await self.check_alerts(prices)
                
                # Palauta hälytykset (lähetetään Telegram-botissa)
                if alerts:
                    self.active_alerts.extend(alerts)
                    yield alerts
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in crypto monitoring: {e}")
                await asyncio.sleep(self.update_interval)
    
    def get_current_prices(self) -> Dict[str, CryptoPrice]:
        """Hae nykyiset hinnat historiasta"""
        return self.price_history.copy()
    
    def get_active_alerts(self) -> List[CryptoAlert]:
        """Hae aktiiviset hälytykset"""
        return self.active_alerts.copy()
    
    def format_price_message(self, prices: List[CryptoPrice]) -> str:
        """Muotoile hinnat Telegram-viestiksi"""
        if not prices:
            return "❌ No crypto prices available"
        
        message = "📊 **CURRENT CRYPTO PRICES**\n\n"
        for price in prices:
            change_emoji = "🟢" if price.change_24h >= 0 else "🔴"
            message += f"{change_emoji} **{price.symbol}**: ${price.price:,.2f}\n"
            message += f"   24h Change: {price.change_24h:+.2f}%\n"
            if price.volume_24h:
                message += f"   Volume: ${price.volume_24h/1e9:.2f}B\n"
            message += "\n"
        
        return message
    
    def format_alert_message(self, alert: CryptoAlert) -> str:
        """Muotoile hälytys Telegram-viestiksi"""
        price = self.price_history.get(alert.symbol)
        change_info = ""
        if price:
            change_info = f"\n📊 24h Change: {price.change_24h:+.2f}%"
            if price.volume_24h:
                change_info += f"\n📈 Volume: ${price.volume_24h/1e9:.2f}B"
        
        message = f"""
🚨 **CRYPTO ALERT**

{alert.message}

💰 Current Price: ${alert.current_price:,.2f}
🎯 Target Price: ${alert.target_price:,.2f}
⏰ Time: {alert.timestamp.strftime('%H:%M:%S')}
{change_info}

⚠️ This is for informational purposes only.
        """
        return message.strip()

