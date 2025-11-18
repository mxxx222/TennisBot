"""
Crypto Trading Engine - Optimized for Continuous Profit
=======================================================

Automaattinen crypto-trading-järjestelmä joka:
- Tunnistaa bull/bear markkinat
- Generoi long/short signaaleja
- Optimoi position sizing Kelly Criterion -menetelmällä
- Hallitsee riskiä jatkuvasti
- Tuottaa rahaa molemmissa markkinasuunnissa
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)

class MarketTrend(Enum):
    """Markkinatrendin tyyppi"""
    BULL = "bull"  # Nouseva markkina
    BEAR = "bear"  # Laskeva markkina
    SIDEWAYS = "sideways"  # Sivusuuntainen
    UNKNOWN = "unknown"

class SignalType(Enum):
    """Kauppasignaalin tyyppi"""
    LONG = "long"  # Osta (nouseva trendi)
    SHORT = "short"  # Myy (laskeva trendi)
    CLOSE_LONG = "close_long"  # Sulje long-positio
    CLOSE_SHORT = "close_short"  # Sulje short-positio
    HOLD = "hold"  # Pidä nykyinen positio

@dataclass
class TechnicalIndicators:
    """Tekniset indikaattorit"""
    rsi: float  # Relative Strength Index (0-100)
    macd: float  # MACD line
    macd_signal: float  # MACD signal line
    macd_histogram: float  # MACD histogram
    sma_20: float  # 20-päivän liukuva keskiarvo
    sma_50: float  # 50-päivän liukuva keskiarvo
    sma_200: float  # 200-päivän liukuva keskiarvo
    bollinger_upper: float  # Bollinger Bands yläraja
    bollinger_lower: float  # Bollinger Bands alaraja
    volume_ma: float  # Volyymin liukuva keskiarvo
    atr: float  # Average True Range (volatiliteetti)
    trend_strength: float  # Trendin vahvuus (0-1)
    momentum: float  # Hinnan momentum

@dataclass
class TradingSignal:
    """Kauppasignaali"""
    symbol: str
    signal_type: SignalType
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float  # 0-1
    expected_profit: float  # Odotettu voitto %
    risk_reward_ratio: float  # Risk/palkkio-suhde
    position_size: float  # Position koko (% bankrollista)
    reasoning: str
    indicators: TechnicalIndicators
    timestamp: datetime

@dataclass
class Position:
    """Avoin positio"""
    symbol: str
    signal_type: SignalType
    entry_price: float
    current_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    unrealized_pnl: float  # Realisoitumaton voitto/tappio
    unrealized_pnl_percent: float
    opened_at: datetime
    risk_amount: float  # Riskillä oleva summa

@dataclass
class TradingPerformance:
    """Trading-suorituskyky"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float  # Voittojen summa / tappioiden summa
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float

class CryptoTradingEngine:
    """Optimized crypto trading engine for continuous profit"""
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.02,  # 2% risk per trade
                 max_positions: int = 5,
                 config_path: Optional[Path] = None):
        """
        Initialize trading engine
        
        Args:
            initial_capital: Alkuperäinen pääoma
            risk_per_trade: Risk per kauppa (% pääomasta)
            max_positions: Maksimimäärä avoimia positioita
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.price_history: Dict[str, List[float]] = {}  # Symbol -> [prices]
        self.performance = TradingPerformance(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0.0, total_profit=0.0, total_loss=0.0,
            net_profit=0.0, max_drawdown=0.0, sharpe_ratio=0.0,
            profit_factor=0.0, avg_win=0.0, avg_loss=0.0,
            best_trade=0.0, worst_trade=0.0
        )
        
        self.config_path = config_path or Path(__file__).parent.parent.parent / 'config' / 'crypto_trading_config.json'
        self.config = self._load_config()
        
        logger.info(f"🚀 Crypto Trading Engine initialized with ${initial_capital:,.2f}")
    
    def _load_config(self) -> Dict:
        """Lataa trading-konfiguraatio"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load trading config: {e}. Using defaults.")
        
        return {
            'indicators': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'sma_periods': [20, 50, 200],
                'bollinger_period': 20,
                'bollinger_std': 2,
                'atr_period': 14
            },
            'signals': {
                'min_confidence': 0.6,
                'min_risk_reward': 2.0,  # Min 2:1 risk/reward
                'max_position_size': 0.1,  # Max 10% per position
                'use_kelly': True,
                'kelly_fraction': 0.25  # Use 25% of Kelly
            },
            'risk_management': {
                'stop_loss_percent': 0.02,  # 2% stop loss
                'take_profit_ratio': 3.0,  # 3x stop loss
                'trailing_stop': True,
                'trailing_stop_percent': 0.01
            }
        }
    
    def calculate_technical_indicators(self, prices: List[float]) -> Optional[TechnicalIndicators]:
        """Laske tekniset indikaattorit"""
        if len(prices) < 200:
            return None
        
        prices_array = np.array(prices)
        
        # RSI
        rsi = self._calculate_rsi(prices_array, period=14)
        
        # MACD
        macd, macd_signal, macd_hist = self._calculate_macd(prices_array)
        
        # Moving Averages
        sma_20 = np.mean(prices_array[-20:])
        sma_50 = np.mean(prices_array[-50:])
        sma_200 = np.mean(prices_array[-200:])
        
        # Bollinger Bands
        bb_upper, bb_lower = self._calculate_bollinger_bands(prices_array, period=20, std=2)
        
        # ATR (Average True Range)
        atr = self._calculate_atr(prices_array, period=14)
        
        # Trend strength
        trend_strength = self._calculate_trend_strength(prices_array, sma_20, sma_50, sma_200)
        
        # Momentum
        momentum = (prices_array[-1] - prices_array[-10]) / prices_array[-10] if len(prices_array) >= 10 else 0
        
        return TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_histogram=macd_hist,
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            bollinger_upper=bb_upper,
            bollinger_lower=bb_lower,
            volume_ma=0.0,  # Volume data tarvitaan erikseen
            atr=atr,
            trend_strength=trend_strength,
            momentum=momentum
        )
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Laske RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Laske MACD"""
        if len(prices) < slow + signal:
            return 0.0, 0.0, 0.0
        
        # Calculate EMAs for each period
        ema_fast_values = []
        ema_slow_values = []
        
        for i in range(slow, len(prices)):
            ema_fast = self._calculate_ema(prices[i-fast:i+1] if i >= fast else prices[:i+1], fast)
            ema_slow = self._calculate_ema(prices[i-slow:i+1], slow)
            ema_fast_values.append(ema_fast)
            ema_slow_values.append(ema_slow)
        
        if not ema_fast_values or not ema_slow_values:
            return 0.0, 0.0, 0.0
        
        # Current MACD line
        macd_line = ema_fast_values[-1] - ema_slow_values[-1]
        
        # MACD values for signal line
        macd_values = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast_values, ema_slow_values)]
        
        # MACD signal line (EMA of MACD values)
        if len(macd_values) >= signal:
            macd_signal_line = np.mean(macd_values[-signal:])
        else:
            macd_signal_line = np.mean(macd_values) if macd_values else macd_line
        
        macd_histogram = macd_line - macd_signal_line
        
        return macd_line, macd_signal_line, macd_histogram
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Laske EMA (Exponential Moving Average)"""
        if len(prices) == 0:
            return 0.0
        
        if len(prices) < period:
            return np.mean(prices)
        
        # Use only the last 'period' prices for EMA
        prices_to_use = prices[-period:] if len(prices) > period else prices
        
        multiplier = 2 / (period + 1)
        ema = prices_to_use[0]
        
        for price in prices_to_use[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std: float = 2) -> Tuple[float, float]:
        """Laske Bollinger Bands"""
        if len(prices) < period:
            return prices[-1], prices[-1]
        
        sma = np.mean(prices[-period:])
        std_dev = np.std(prices[-period:])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, lower
    
    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Laske ATR (Average True Range)"""
        if len(prices) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(prices)):
            tr = abs(prices[i] - prices[i-1])
            true_ranges.append(tr)
        
        if len(true_ranges) >= period:
            return np.mean(true_ranges[-period:])
        return np.mean(true_ranges) if true_ranges else 0.0
    
    def _calculate_trend_strength(self, prices: np.ndarray, sma_20: float, sma_50: float, sma_200: float) -> float:
        """Laske trendin vahvuus (0-1)"""
        current_price = prices[-1]
        
        # Bullish alignment
        if current_price > sma_20 > sma_50 > sma_200:
            strength = min(1.0, (current_price - sma_200) / sma_200)
            return max(0.0, strength)
        
        # Bearish alignment
        elif current_price < sma_20 < sma_50 < sma_200:
            strength = min(1.0, (sma_200 - current_price) / sma_200)
            return max(0.0, strength)
        
        # Sideways
        return 0.3
    
    def detect_market_trend(self, indicators: TechnicalIndicators, current_price: float) -> MarketTrend:
        """Tunnista markkinatrendi"""
        # Bull market signals
        bull_signals = 0
        if current_price > indicators.sma_20 > indicators.sma_50 > indicators.sma_200:
            bull_signals += 2
        if indicators.macd > indicators.macd_signal:
            bull_signals += 1
        if indicators.rsi > 50 and indicators.rsi < 70:
            bull_signals += 1
        if indicators.momentum > 0:
            bull_signals += 1
        
        # Bear market signals
        bear_signals = 0
        if current_price < indicators.sma_20 < indicators.sma_50 < indicators.sma_200:
            bear_signals += 2
        if indicators.macd < indicators.macd_signal:
            bear_signals += 1
        if indicators.rsi < 50 and indicators.rsi > 30:
            bear_signals += 1
        if indicators.momentum < 0:
            bear_signals += 1
        
        if bull_signals >= 3:
            return MarketTrend.BULL
        elif bear_signals >= 3:
            return MarketTrend.BEAR
        elif abs(bull_signals - bear_signals) <= 1:
            return MarketTrend.SIDEWAYS
        else:
            return MarketTrend.UNKNOWN
    
    def generate_trading_signal(self, 
                               symbol: str,
                               current_price: float,
                               indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """Generoi kauppasignaali"""
        trend = self.detect_market_trend(indicators, current_price)
        
        # Päivitä hintahistoria
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(current_price)
        if len(self.price_history[symbol]) > 500:
            self.price_history[symbol] = self.price_history[symbol][-500:]
        
        # Tarkista onko avoin positio
        existing_position = self.positions.get(symbol)
        
        # Long signal (bull market)
        if trend == MarketTrend.BULL and indicators.rsi < 70:
            if existing_position and existing_position.signal_type == SignalType.LONG:
                return None  # Already in long
            
            # Long entry
            stop_loss_pct = self.config['risk_management']['stop_loss_percent']
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit_ratio = self.config['risk_management']['take_profit_ratio']
            target_price = current_price + (current_price - stop_loss) * take_profit_ratio
            
            risk_reward = (target_price - current_price) / (current_price - stop_loss)
            
            if risk_reward < self.config['signals']['min_risk_reward']:
                return None
            
            confidence = self._calculate_confidence(indicators, trend, SignalType.LONG)
            
            if confidence < self.config['signals']['min_confidence']:
                return None
            
            position_size = self._calculate_position_size(
                current_price, stop_loss, confidence, risk_reward
            )
            
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.LONG,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                confidence=confidence,
                expected_profit=(target_price - current_price) / current_price * 100,
                risk_reward_ratio=risk_reward,
                position_size=position_size,
                reasoning=self._generate_reasoning(indicators, trend, SignalType.LONG),
                indicators=indicators,
                timestamp=datetime.now()
            )
        
        # Short signal (bear market)
        elif trend == MarketTrend.BEAR and indicators.rsi > 30:
            if existing_position and existing_position.signal_type == SignalType.SHORT:
                return None  # Already in short
            
            # Short entry
            stop_loss_pct = self.config['risk_management']['stop_loss_percent']
            stop_loss = current_price * (1 + stop_loss_pct)
            take_profit_ratio = self.config['risk_management']['take_profit_ratio']
            target_price = current_price - (stop_loss - current_price) * take_profit_ratio
            
            risk_reward = (current_price - target_price) / (stop_loss - current_price)
            
            if risk_reward < self.config['signals']['min_risk_reward']:
                return None
            
            confidence = self._calculate_confidence(indicators, trend, SignalType.SHORT)
            
            if confidence < self.config['signals']['min_confidence']:
                return None
            
            position_size = self._calculate_position_size(
                current_price, stop_loss, confidence, risk_reward
            )
            
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SHORT,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                confidence=confidence,
                expected_profit=(current_price - target_price) / current_price * 100,
                risk_reward_ratio=risk_reward,
                position_size=position_size,
                reasoning=self._generate_reasoning(indicators, trend, SignalType.SHORT),
                indicators=indicators,
                timestamp=datetime.now()
            )
        
        # Close signals
        elif existing_position:
            # Close long if bearish
            if existing_position.signal_type == SignalType.LONG and trend == MarketTrend.BEAR:
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    entry_price=current_price,
                    target_price=current_price,
                    stop_loss=current_price,
                    confidence=0.8,
                    expected_profit=0,
                    risk_reward_ratio=0,
                    position_size=0,
                    reasoning="Bear market detected, closing long position",
                    indicators=indicators,
                    timestamp=datetime.now()
                )
            
            # Close short if bullish
            elif existing_position.signal_type == SignalType.SHORT and trend == MarketTrend.BULL:
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_SHORT,
                    entry_price=current_price,
                    target_price=current_price,
                    stop_loss=current_price,
                    confidence=0.8,
                    expected_profit=0,
                    risk_reward_ratio=0,
                    position_size=0,
                    reasoning="Bull market detected, closing short position",
                    indicators=indicators,
                    timestamp=datetime.now()
                )
        
        return None
    
    def _calculate_confidence(self, 
                             indicators: TechnicalIndicators,
                             trend: MarketTrend,
                             signal_type: SignalType) -> float:
        """Laske signaalin luottamus (0-1)"""
        confidence = 0.5  # Base confidence
        
        # Trend strength
        confidence += indicators.trend_strength * 0.2
        
        # RSI confirmation
        if signal_type == SignalType.LONG:
            if 40 < indicators.rsi < 60:
                confidence += 0.15
            elif 30 < indicators.rsi < 70:
                confidence += 0.1
        elif signal_type == SignalType.SHORT:
            if 40 < indicators.rsi < 60:
                confidence += 0.15
            elif 30 < indicators.rsi < 70:
                confidence += 0.1
        
        # MACD confirmation
        if signal_type == SignalType.LONG and indicators.macd > indicators.macd_signal:
            confidence += 0.1
        elif signal_type == SignalType.SHORT and indicators.macd < indicators.macd_signal:
            confidence += 0.1
        
        # Momentum
        if signal_type == SignalType.LONG and indicators.momentum > 0:
            confidence += 0.05
        elif signal_type == SignalType.SHORT and indicators.momentum < 0:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _calculate_position_size(self,
                                entry_price: float,
                                stop_loss: float,
                                confidence: float,
                                risk_reward: float) -> float:
        """Laske position koko Kelly Criterion -menetelmällä"""
        # Risk amount
        risk_amount = self.current_capital * self.risk_per_trade
        
        # Price risk per unit
        if entry_price > stop_loss:  # Long
            price_risk = entry_price - stop_loss
        else:  # Short
            price_risk = stop_loss - entry_price
        
        # Base position size
        base_size = risk_amount / price_risk if price_risk > 0 else 0
        position_value = base_size * entry_price
        base_position_pct = position_value / self.current_capital
        
        # Kelly Criterion adjustment
        if self.config['signals']['use_kelly']:
            # Win probability estimate from confidence
            win_prob = confidence
            
            # Expected return
            expected_return = (risk_reward * win_prob) - ((1 - win_prob))
            
            if expected_return > 0:
                kelly_fraction = expected_return / risk_reward
                kelly_fraction *= self.config['signals']['kelly_fraction']  # Use fraction of Kelly
                base_position_pct *= (1 + kelly_fraction)
        
        # Apply confidence multiplier
        base_position_pct *= confidence
        
        # Cap at max position size
        max_size = self.config['signals']['max_position_size']
        position_pct = min(base_position_pct, max_size)
        
        return position_pct
    
    def _generate_reasoning(self,
                           indicators: TechnicalIndicators,
                           trend: MarketTrend,
                           signal_type: SignalType) -> str:
        """Generoi perustelut signaalille"""
        reasons = []
        
        if trend == MarketTrend.BULL:
            reasons.append("Bull market detected")
        elif trend == MarketTrend.BEAR:
            reasons.append("Bear market detected")
        
        if signal_type == SignalType.LONG:
            if indicators.rsi < 70:
                reasons.append(f"RSI at {indicators.rsi:.1f} (not overbought)")
            if indicators.macd > indicators.macd_signal:
                reasons.append("MACD bullish crossover")
            if indicators.momentum > 0:
                reasons.append("Positive momentum")
        elif signal_type == SignalType.SHORT:
            if indicators.rsi > 30:
                reasons.append(f"RSI at {indicators.rsi:.1f} (not oversold)")
            if indicators.macd < indicators.macd_signal:
                reasons.append("MACD bearish crossover")
            if indicators.momentum < 0:
                reasons.append("Negative momentum")
        
        return "; ".join(reasons)
    
    def execute_signal(self, signal: TradingSignal) -> bool:
        """Suorita kauppasignaali"""
        if signal.signal_type in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT]:
            return self._close_position(signal.symbol, signal.entry_price)
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            logger.warning(f"Max positions reached, skipping {signal.symbol}")
            return False
        
        # Check if position already exists
        if signal.symbol in self.positions:
            logger.warning(f"Position already exists for {signal.symbol}")
            return False
        
        # Calculate position details
        position_value = self.current_capital * signal.position_size
        quantity = position_value / signal.entry_price
        
        # Create position
        position = Position(
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            position_size=signal.position_size,
            stop_loss=signal.stop_loss,
            take_profit=signal.target_price,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            opened_at=datetime.now(),
            risk_amount=position_value * self.risk_per_trade
        )
        
        self.positions[signal.symbol] = position
        
        logger.info(f"✅ Opened {signal.signal_type.value} position: {signal.symbol} @ ${signal.entry_price:,.2f}")
        
        return True
    
    def _close_position(self, symbol: str, exit_price: float) -> bool:
        """Sulje positio"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # Calculate P&L
        if position.signal_type == SignalType.LONG:
            pnl = (exit_price - position.entry_price) / position.entry_price
        else:  # SHORT
            pnl = (position.entry_price - exit_price) / position.entry_price
        
        pnl_amount = self.current_capital * position.position_size * pnl
        
        # Update capital
        self.current_capital += pnl_amount
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'signal_type': position.signal_type.value,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'pnl': pnl_amount,
            'pnl_percent': pnl * 100,
            'opened_at': position.opened_at,
            'closed_at': datetime.now(),
            'duration': (datetime.now() - position.opened_at).total_seconds() / 3600
        }
        
        self.trade_history.append(trade_record)
        
        # Update performance
        self._update_performance(trade_record)
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"🔒 Closed {position.signal_type.value} position: {symbol} @ ${exit_price:,.2f} | P&L: ${pnl_amount:+,.2f} ({pnl*100:+.2f}%)")
        
        return True
    
    def update_positions(self, prices: Dict[str, float]):
        """Päivitä avoimet positiot ja tarkista stop loss/take profit"""
        for symbol, position in list(self.positions.items()):
            if symbol not in prices:
                continue
            
            current_price = prices[symbol]
            position.current_price = current_price
            
            # Calculate unrealized P&L
            if position.signal_type == SignalType.LONG:
                pnl = (current_price - position.entry_price) / position.entry_price
            else:  # SHORT
                pnl = (position.entry_price - current_price) / position.entry_price
            
            position.unrealized_pnl = self.current_capital * position.position_size * pnl
            position.unrealized_pnl_percent = pnl * 100
            
            # Check stop loss
            if position.signal_type == SignalType.LONG and current_price <= position.stop_loss:
                self._close_position(symbol, position.stop_loss)
                logger.warning(f"🛑 Stop loss hit: {symbol}")
            elif position.signal_type == SignalType.SHORT and current_price >= position.stop_loss:
                self._close_position(symbol, position.stop_loss)
                logger.warning(f"🛑 Stop loss hit: {symbol}")
            
            # Check take profit
            elif position.signal_type == SignalType.LONG and current_price >= position.take_profit:
                self._close_position(symbol, position.take_profit)
                logger.info(f"🎯 Take profit hit: {symbol}")
            elif position.signal_type == SignalType.SHORT and current_price <= position.take_profit:
                self._close_position(symbol, position.take_profit)
                logger.info(f"🎯 Take profit hit: {symbol}")
    
    def _update_performance(self, trade_record: Dict):
        """Päivitä suorituskykytilastot"""
        self.performance.total_trades += 1
        
        if trade_record['pnl'] > 0:
            self.performance.winning_trades += 1
            self.performance.total_profit += trade_record['pnl']
            if trade_record['pnl'] > self.performance.best_trade:
                self.performance.best_trade = trade_record['pnl']
        else:
            self.performance.losing_trades += 1
            self.performance.total_loss += abs(trade_record['pnl'])
            if trade_record['pnl'] < self.performance.worst_trade:
                self.performance.worst_trade = trade_record['pnl']
        
        self.performance.net_profit = self.current_capital - self.initial_capital
        self.performance.win_rate = (self.performance.winning_trades / 
                                    self.performance.total_trades * 100) if self.performance.total_trades > 0 else 0
        
        if self.performance.losing_trades > 0:
            self.performance.profit_factor = self.performance.total_profit / self.performance.total_loss
        else:
            self.performance.profit_factor = float('inf') if self.performance.total_profit > 0 else 0
        
        if self.performance.winning_trades > 0:
            self.performance.avg_win = self.performance.total_profit / self.performance.winning_trades
        if self.performance.losing_trades > 0:
            self.performance.avg_loss = self.performance.total_loss / self.performance.losing_trades
    
    def get_performance_summary(self) -> str:
        """Hae suorituskykytilastot tekstinä"""
        return f"""
📊 TRADING PERFORMANCE SUMMARY

💰 Capital: ${self.current_capital:,.2f} (Started: ${self.initial_capital:,.2f})
📈 Net Profit: ${self.performance.net_profit:+,.2f} ({self.performance.net_profit/self.initial_capital*100:+.2f}%)

📊 Statistics:
• Total Trades: {self.performance.total_trades}
• Win Rate: {self.performance.win_rate:.1f}%
• Winning Trades: {self.performance.winning_trades}
• Losing Trades: {self.performance.losing_trades}
• Profit Factor: {self.performance.profit_factor:.2f}

💵 P&L:
• Total Profit: ${self.performance.total_profit:+,.2f}
• Total Loss: ${self.performance.total_loss:+,.2f}
• Avg Win: ${self.performance.avg_win:+,.2f}
• Avg Loss: ${self.performance.avg_loss:+,.2f}
• Best Trade: ${self.performance.best_trade:+,.2f}
• Worst Trade: ${self.performance.worst_trade:+,.2f}

📊 Open Positions: {len(self.positions)}
        """

