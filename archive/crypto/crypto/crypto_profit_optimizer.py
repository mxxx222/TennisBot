"""
Crypto Profit Optimizer - Integrates Trading Engine with Crypto Radar
=====================================================================

Yhdistää crypto-seurannan ja trading-enginen jatkuvaan rahantekoon.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .crypto_radar import CryptoRadar, CryptoPrice
from .crypto_trading_engine import (
    CryptoTradingEngine, TradingSignal, SignalType, 
    MarketTrend, TechnicalIndicators
)

logger = logging.getLogger(__name__)

class CryptoProfitOptimizer:
    """Optimized crypto trading system for continuous profit"""
    
    def __init__(self,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,
                 max_positions: int = 5,
                 config_path: Optional[Path] = None):
        """
        Initialize profit optimizer
        
        Args:
            initial_capital: Alkuperäinen pääoma
            risk_per_trade: Risk per kauppa
            max_positions: Maksimimäärä positioita
        """
        self.crypto_radar = CryptoRadar(config_path)
        self.trading_engine = CryptoTradingEngine(
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade,
            max_positions=max_positions,
            config_path=config_path
        )
        
        self.running = False
        self.monitoring_task = None
        
        logger.info("🚀 Crypto Profit Optimizer initialized")
    
    async def start(self):
        """Käynnistä optimoitu trading-järjestelmä"""
        if self.running:
            logger.warning("Optimizer already running")
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Crypto Profit Optimizer started")
    
    async def stop(self):
        """Pysäytä trading-järjestelmä"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Crypto Profit Optimizer stopped")
    
    async def _monitoring_loop(self):
        """Päämonitorointisilmukka"""
        update_interval = self.crypto_radar.update_interval
        
        while self.running:
            try:
                # Hae crypto-hinnat
                symbols = [s for s, config in self.crypto_radar.monitored_cryptos.items() 
                          if config.get('enabled', True)]
                
                if not symbols:
                    await asyncio.sleep(update_interval)
                    continue
                
                prices = await self.crypto_radar.fetch_crypto_prices(symbols)
                
                if not prices:
                    await asyncio.sleep(update_interval)
                    continue
                
                # Päivitä positiot
                price_dict = {p.symbol: p.price for p in prices}
                self.trading_engine.update_positions(price_dict)
                
                # Generoi signaalit jokaiselle cryptolle
                for price_data in prices:
                    signal = await self._analyze_and_generate_signal(price_data)
                    
                    if signal:
                        # Suorita signaali
                        executed = self.trading_engine.execute_signal(signal)
                        
                        if executed:
                            logger.info(f"📊 Signal executed: {signal.symbol} {signal.signal_type.value} @ ${signal.entry_price:,.2f}")
                
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(update_interval)
    
    async def _analyze_and_generate_signal(self, price_data: CryptoPrice) -> Optional[TradingSignal]:
        """Analysoi hinta ja generoi signaali"""
        symbol = price_data.symbol
        
        # Hae hintahistoria
        if symbol not in self.trading_engine.price_history:
            self.trading_engine.price_history[symbol] = []
        
        # Lisää uusi hinta
        self.trading_engine.price_history[symbol].append(price_data.price)
        
        # Tarvitaan tarpeeksi dataa indikaattoreille
        if len(self.trading_engine.price_history[symbol]) < 200:
            return None
        
        # Laske tekniset indikaattorit
        indicators = self.trading_engine.calculate_technical_indicators(
            self.trading_engine.price_history[symbol]
        )
        
        if not indicators:
            return None
        
        # Generoi signaali
        signal = self.trading_engine.generate_trading_signal(
            symbol=symbol,
            current_price=price_data.price,
            indicators=indicators
        )
        
        return signal
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Hae aktiiviset signaalit"""
        signals = []
        
        # Tarkista jokainen seurattu crypto
        for symbol, config in self.crypto_radar.monitored_cryptos.items():
            if not config.get('enabled', True):
                continue
            
            # Hae viimeisin hinta
            price_data = self.crypto_radar.price_history.get(symbol)
            if not price_data:
                continue
            
            # Laske indikaattorit
            if symbol not in self.trading_engine.price_history:
                continue
            
            if len(self.trading_engine.price_history[symbol]) < 200:
                continue
            
            indicators = self.trading_engine.calculate_technical_indicators(
                self.trading_engine.price_history[symbol]
            )
            
            if not indicators:
                continue
            
            # Generoi signaali
            signal = self.trading_engine.generate_trading_signal(
                symbol=symbol,
                current_price=price_data.price,
                indicators=indicators
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def get_portfolio_status(self) -> Dict:
        """Hae portfolion tila"""
        positions = []
        total_unrealized_pnl = 0.0
        
        for symbol, position in self.trading_engine.positions.items():
            positions.append({
                'symbol': symbol,
                'type': position.signal_type.value,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'unrealized_pnl_percent': position.unrealized_pnl_percent,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'opened_at': position.opened_at.isoformat()
            })
            total_unrealized_pnl += position.unrealized_pnl
        
        return {
            'capital': self.trading_engine.current_capital,
            'initial_capital': self.trading_engine.initial_capital,
            'total_return': (self.trading_engine.current_capital - self.trading_engine.initial_capital) / self.trading_engine.initial_capital * 100,
            'open_positions': len(positions),
            'positions': positions,
            'unrealized_pnl': total_unrealized_pnl,
            'performance': {
                'total_trades': self.trading_engine.performance.total_trades,
                'win_rate': self.trading_engine.performance.win_rate,
                'profit_factor': self.trading_engine.performance.profit_factor,
                'net_profit': self.trading_engine.performance.net_profit
            }
        }
    
    def format_portfolio_message(self) -> str:
        """Muotoile portfolio-tila Telegram-viestiksi"""
        status = self.get_portfolio_status()
        
        message = f"""
💰 **CRYPTO TRADING PORTFOLIO**

📊 **Capital:**
• Current: ${status['capital']:,.2f}
• Initial: ${status['initial_capital']:,.2f}
• Return: {status['total_return']:+.2f}%

📈 **Performance:**
• Total Trades: {status['performance']['total_trades']}
• Win Rate: {status['performance']['win_rate']:.1f}%
• Profit Factor: {status['performance']['profit_factor']:.2f}
• Net Profit: ${status['performance']['net_profit']:+,.2f}

🔷 **Open Positions:** {status['open_positions']}
"""
        
        if status['positions']:
            message += "\n**Active Positions:**\n"
            for pos in status['positions']:
                pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                message += f"""
{pnl_emoji} **{pos['symbol']}** {pos['type'].upper()}
   Entry: ${pos['entry_price']:,.2f}
   Current: ${pos['current_price']:,.2f}
   P&L: ${pos['unrealized_pnl']:+,.2f} ({pos['unrealized_pnl_percent']:+.2f}%)
   Stop Loss: ${pos['stop_loss']:,.2f}
   Take Profit: ${pos['take_profit']:,.2f}
"""
        
        message += "\n⚠️ For informational purposes only."
        
        return message
    
    def format_signal_message(self, signal: TradingSignal) -> str:
        """Muotoile signaali Telegram-viestiksi"""
        trend_emoji = "🟢" if signal.signal_type == SignalType.LONG else "🔴"
        signal_type_name = signal.signal_type.value.upper()
        
        message = f"""
{trend_emoji} **CRYPTO TRADING SIGNAL**

🎯 **{signal.symbol}** - {signal_type_name}

💰 **Entry:** ${signal.entry_price:,.2f}
🎯 **Target:** ${signal.target_price:,.2f}
🛑 **Stop Loss:** ${signal.stop_loss:,.2f}

📊 **Analysis:**
• Confidence: {signal.confidence*100:.1f}%
• Expected Profit: {signal.expected_profit:+.2f}%
• Risk/Reward: 1:{signal.risk_reward_ratio:.2f}
• Position Size: {signal.position_size*100:.2f}% of capital

📈 **Indicators:**
• RSI: {signal.indicators.rsi:.1f}
• MACD: {signal.indicators.macd:.4f}
• Trend Strength: {signal.indicators.trend_strength*100:.1f}%
• Momentum: {signal.indicators.momentum*100:+.2f}%

💡 **Reasoning:**
{signal.reasoning}

⏰ {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

⚠️ This is for informational purposes only. Not financial advice.
        """
        
        return message.strip()

