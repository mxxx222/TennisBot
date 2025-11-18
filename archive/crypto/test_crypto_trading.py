#!/usr/bin/env python3
"""
Test Crypto Trading Engine
==========================

Testaa crypto-trading-järjestelmän toimivuutta.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crypto.crypto_profit_optimizer import CryptoProfitOptimizer
from src.crypto.crypto_trading_engine import SignalType, MarketTrend

async def test_trading_engine():
    """Testaa trading engine"""
    print("🧪 Testing Crypto Trading Engine...\n")
    
    # Alusta optimizer
    optimizer = CryptoProfitOptimizer(
        initial_capital=10000,
        risk_per_trade=0.02,
        max_positions=3
    )
    
    print("✅ Optimizer initialized")
    print(f"   Initial Capital: ${optimizer.trading_engine.initial_capital:,.2f}")
    print(f"   Risk Per Trade: {optimizer.trading_engine.risk_per_trade*100:.1f}%")
    print(f"   Max Positions: {optimizer.trading_engine.max_positions}\n")
    
    # Testaa hintahistoria
    print("📊 Testing price history...")
    test_prices = [50000 + i * 100 for i in range(250)]  # Simuloi hintahistoria
    optimizer.trading_engine.price_history['BTC'] = test_prices
    
    # Laske indikaattorit
    indicators = optimizer.trading_engine.calculate_technical_indicators(test_prices)
    
    if indicators:
        print(f"✅ Technical indicators calculated:")
        print(f"   RSI: {indicators.rsi:.2f}")
        print(f"   MACD: {indicators.macd:.4f}")
        print(f"   SMA 20: ${indicators.sma_20:,.2f}")
        print(f"   SMA 50: ${indicators.sma_50:,.2f}")
        print(f"   SMA 200: ${indicators.sma_200:,.2f}")
        print(f"   Trend Strength: {indicators.trend_strength*100:.1f}%")
        print(f"   Momentum: {indicators.momentum*100:+.2f}%\n")
        
        # Tunnista trendi
        current_price = test_prices[-1]
        trend = optimizer.trading_engine.detect_market_trend(indicators, current_price)
        print(f"📈 Market Trend: {trend.value.upper()}\n")
        
        # Generoi signaali
        signal = optimizer.trading_engine.generate_trading_signal(
            symbol='BTC',
            current_price=current_price,
            indicators=indicators
        )
        
        if signal:
            print(f"🎯 Trading Signal Generated:")
            print(f"   Symbol: {signal.symbol}")
            print(f"   Type: {signal.signal_type.value.upper()}")
            print(f"   Entry: ${signal.entry_price:,.2f}")
            print(f"   Target: ${signal.target_price:,.2f}")
            print(f"   Stop Loss: ${signal.stop_loss:,.2f}")
            print(f"   Confidence: {signal.confidence*100:.1f}%")
            print(f"   Expected Profit: {signal.expected_profit:+.2f}%")
            print(f"   Risk/Reward: 1:{signal.risk_reward_ratio:.2f}")
            print(f"   Position Size: {signal.position_size*100:.2f}%")
            print(f"   Reasoning: {signal.reasoning}\n")
        else:
            print("⚠️ No signal generated (may not meet criteria)\n")
    
    # Testaa portfolio status
    print("📊 Portfolio Status:")
    status = optimizer.get_portfolio_status()
    print(f"   Capital: ${status['capital']:,.2f}")
    print(f"   Return: {status['total_return']:+.2f}%")
    print(f"   Open Positions: {status['open_positions']}")
    print(f"   Total Trades: {status['performance']['total_trades']}\n")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_trading_engine())

