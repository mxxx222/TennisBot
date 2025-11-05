#!/usr/bin/env python3
"""
FINANCIAL MODELING FRAMEWORK - Educational Portfolio Theory
==========================================================

Educational implementation of portfolio optimization and risk management
techniques using mathematical principles from quantitative finance.

⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY
⚠️  This is a learning framework for portfolio theory, risk management,
    and quantitative finance concepts.

Author: Betfury.io Educational Research System
License: Educational Use Only
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Educational risk categories for learning"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"  
    AGGRESSIVE = "aggressive"


class AssetClass(Enum):
    """Educational asset classes for portfolio theory"""
    EQUITY = "equity"
    BOND = "bond"
    COMMODITY = "commodity"
    CASH = "cash"
    REAL_ESTATE = "real_estate"


@dataclass
class EducationalAsset:
    """Educational asset representation for portfolio learning"""
    symbol: str
    name: str
    asset_class: AssetClass
    expected_return: float  # Annual expected return
    volatility: float       # Annual volatility
    current_price: float    # Current educational price
    dividend_yield: float   # Annual dividend yield


@dataclass
class EducationalPosition:
    """Educational portfolio position"""
    asset: EducationalAsset
    quantity: int
    cost_basis: float
    market_value: float
    unrealized_pnl: float


class KellyCriterion:
    """Educational implementation of Kelly Criterion for bankroll management"""
    
    @staticmethod
    def calculate_kelly_fraction(win_probability: float, 
                               odds: float, 
                               bankroll: float) -> float:
        """
        Calculate optimal Kelly fraction for educational purposes
        
        Args:
            win_probability: Estimated win probability (0-1)
            odds: Decimal odds offered
            bankroll: Current bankroll size
            
        Returns:
            Kelly fraction as percentage of bankroll
            
        Formula: f = (bp - q) / b
        Where:
        - b = odds - 1
        - p = win probability  
        - q = loss probability (1-p)
        """
        if win_probability <= 0 or odds <= 1:
            return 0.0
            
        q = 1 - win_probability
        b = odds - 1
        
        # Kelly fraction calculation
        kelly_fraction = (b * win_probability - q) / b
        
        # Educational safeguard: Use fractional Kelly (25%)
        fractional_kelly = kelly_fraction * 0.25
        
        # Ensure positive and reasonable allocation
        return max(0, min(fractional_kelly, 0.05))  # Max 5% per position
    
    @staticmethod
    def simulate_kelly_path(win_probability: float, 
                          odds: float, 
                          n_simulations: int = 1000) -> Dict[str, float]:
        """Educational simulation of Kelly strategy outcomes"""
        
        results = {
            'mean_return': 0,
            'std_return': 0, 
            'probability_positive': 0,
            'expected_growth_rate': 0
        }
        
        outcomes = []
        
        for _ in range(n_simulations):
            if np.random.random() < win_probability:
                # Win
                outcomes.append(odds - 1)
            else:
                # Loss
                outcomes.append(-1)
        
        results['mean_return'] = np.mean(outcomes)
        results['std_return'] = np.std(outcomes)
        results['probability_positive'] = np.mean(np.array(outcomes) > 0)
        
        # Expected growth rate using Kelly formula
        kelly_fraction = KellyCriterion.calculate_kelly_fraction(
            win_probability, odds, 100
        )
        
        # Educational growth rate approximation
        results['expected_growth_rate'] = kelly_fraction * win_probability
        
        return results


class ExpectedValueCalculator:
    """Educational Expected Value calculations for decision analysis"""
    
    @staticmethod
    def calculate_ev(probabilities: List[float], 
                    outcomes: List[float]) -> Dict[str, float]:
        """
        Calculate Expected Value for educational decision making
        
        Args:
            probabilities: List of outcome probabilities
            outcomes: List of corresponding outcomes
            
        Returns:
            Dictionary with EV, variance, and standard deviation
        """
        if len(probabilities) != len(outcomes):
            raise ValueError("Probabilities and outcomes must be same length")
            
        if abs(sum(probabilities) - 1.0) > 0.001:
            raise ValueError("Probabilities must sum to 1.0")
        
        # Expected Value
        ev = sum(p * o for p, o in zip(probabilities, outcomes))
        
        # Variance
        variance = sum(p * (o - ev)**2 for p, o in zip(probabilities, outcomes))
        
        # Standard Deviation
        std_dev = np.sqrt(variance)
        
        # Coefficient of Variation (risk-adjusted metric)
        cv = std_dev / abs(ev) if ev != 0 else float('inf')
        
        return {
            'expected_value': ev,
            'variance': variance,
            'std_deviation': std_dev,
            'coefficient_variation': cv,
            'risk_level': 'high' if cv > 1.0 else 'moderate' if cv > 0.5 else 'low'
        }


class PortfolioOptimizer:
    """Educational Modern Portfolio Theory implementation"""
    
    def __init__(self, assets: List[EducationalAsset]):
        """Initialize with educational assets"""
        self.assets = assets
        self.n_assets = len(assets)
        
    def generate_efficient_frontier(self, n_portfolios: int = 1000) -> pd.DataFrame:
        """Generate efficient frontier for educational purposes"""
        
        returns_matrix = self._generate_educational_returns()
        
        results = []
        
        for _ in range(n_portfolios):
            # Random portfolio weights
            weights = np.random.random(self.n_assets)
            weights /= weights.sum()  # Normalize to sum to 1
            
            # Calculate portfolio return and volatility
            portfolio_return = np.sum(returns_matrix.mean() * weights) * 252
            portfolio_std = np.sqrt(
                np.dot(weights.T, np.dot(returns_matrix.cov() * 252, weights))
            )
            
            # Sharpe ratio (risk-free rate = 0 for education)
            sharpe_ratio = portfolio_return / portfolio_std if portfolio_std > 0 else 0
            
            results.append({
                'return': portfolio_return,
                'volatility': portfolio_std,
                'sharpe_ratio': sharpe_ratio,
                'weights': weights.tolist()
            })
        
        return pd.DataFrame(results)
    
    def find_optimal_portfolio(self, target_risk: float) -> Dict[str, any]:
        """Find optimal portfolio for given risk tolerance"""
        
        efficient_frontier = self.generate_efficient_frontier()
        
        # Find portfolio closest to target risk
        efficient_frontier['risk_distance'] = abs(
            efficient_frontier['volatility'] - target_risk
        )
        
        optimal_portfolio = efficient_frontier.loc[
            efficient_frontier['risk_distance'].idxmin()
        ]
        
        return {
            'target_risk': target_risk,
            'actual_return': optimal_portfolio['return'],
            'actual_risk': optimal_portfolio['volatility'],
            'sharpe_ratio': optimal_portfolio['sharpe_ratio'],
            'optimal_weights': dict(zip(
                [asset.symbol for asset in self.assets],
                optimal_portfolio['weights']
            ))
        }
    
    def _generate_educational_returns(self) -> pd.DataFrame:
        """Generate realistic educational return data"""
        np.random.seed(42)  # For reproducible results
        
        # Generate 3 years of daily returns
        n_days = 3 * 252
        
        returns_data = {}
        
        for asset in self.assets:
            # Generate returns using asset's characteristics
            daily_return = asset.expected_return / 252
            daily_vol = asset.volatility / np.sqrt(252)
            
            # Random walk with drift
            returns = np.random.normal(daily_return, daily_vol, n_days)
            returns_data[asset.symbol] = returns
        
        return pd.DataFrame(returns_data)


class RiskManager:
    """Educational risk management system"""
    
    def __init__(self, max_portfolio_risk: float = 0.02):
        """
        Initialize risk manager for educational use
        
        Args:
            max_portfolio_risk: Maximum risk per position (default: 2%)
        """
        self.max_position_risk = max_portfolio_risk
        self.risk_events = []
    
    def calculate_position_sizing(self, 
                                asset_return: float,
                                asset_volatility: float,
                                bankroll: float,
                                target_risk: float) -> int:
        """
        Calculate position size based on educational risk management
        
        Args:
            asset_return: Expected annual return
            asset_volatility: Expected annual volatility  
            bankroll: Total portfolio size
            target_risk: Maximum risk per position (e.g., 0.02 for 2%)
            
        Returns:
            Position size (number of shares)
        """
        
        # Value at Risk approach
        var_1_day = asset_volatility / np.sqrt(252)
        var_1_day *= 1.65  # 95% confidence interval
        
        # Maximum position size based on risk budget
        risk_budget = bankroll * target_risk
        max_position_value = risk_budget / var_1_day
        
        # Convert to number of shares (assuming unit price = 1 for education)
        position_size = int(max_position_value)
        
        return max(1, position_size)  # Minimum 1 share
    
    def calculate_portfolio_var(self, 
                              portfolio_weights: List[float],
                              asset_volatility: List[float],
                              correlation_matrix: np.ndarray) -> float:
        """
        Calculate portfolio Value at Risk for educational purposes
        """
        
        # Convert to numpy arrays
        weights = np.array(portfolio_weights)
        volatilities = np.array(asset_volatility)
        
        # Portfolio volatility
        portfolio_vol = np.sqrt(
            weights.T @ (np.diag(volatilities) @ correlation_matrix @ 
                        np.diag(volatilities) @ weights)
        )
        
        # 95% VaR (1.65 standard deviations)
        portfolio_var = 1.65 * portfolio_vol * np.sqrt(252)
        
        return portfolio_var
    
    def log_risk_event(self, event_type: str, details: Dict[str, any]):
        """Log risk events for educational monitoring"""
        self.risk_events.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        })


class EducationalTradingSimulator:
    """Educational trading simulation for learning risk management"""
    
    def __init__(self, initial_bankroll: float = 10000):
        """Initialize simulator with educational bankroll"""
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.positions = {}
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
    
    def simulate_trade(self, 
                      symbol: str,
                      signal: Dict[str, any],
                      price: float = 100.0) -> Dict[str, any]:
        """
        Simulate educational trade execution
        
        Args:
            symbol: Asset symbol
            signal: Trading signal with confidence and odds
            price: Current price for simulation
            
        Returns:
            Trade execution result
        """
        
        # Calculate Kelly-optimal position size
        kelly_fraction = KellyCriterion.calculate_kelly_fraction(
            signal['confidence'], 
            signal['odds'], 
            self.current_bankroll
        )
        
        position_size = int(self.current_bankroll * kelly_fraction / price)
        
        if position_size <= 0:
            return {
                'executed': False,
                'reason': 'Position size too small'
            }
        
        # Execute trade
        trade_cost = position_size * price
        self.current_bankroll -= trade_cost
        
        # Record trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'buy',
            'quantity': position_size,
            'price': price,
            'cost': trade_cost,
            'signal_confidence': signal['confidence'],
            'odds': signal['odds'],
            'expected_value': signal['confidence'] * signal['odds'] - 1
        }
        
        self.trade_history.append(trade_record)
        self.performance_metrics['total_trades'] += 1
        
        return {
            'executed': True,
            'trade_id': len(self.trade_history),
            'position_size': position_size,
            'kelly_fraction': kelly_fraction,
            'trade_record': trade_record
        }
    
    def simulate_outcome(self, trade_id: int, actual_outcome: str) -> Dict[str, any]:
        """
        Simulate trade outcome for educational learning
        
        Args:
            trade_id: ID of the trade
            actual_outcome: 'win' or 'loss'
            
        Returns:
            Trade outcome result
        """
        
        if trade_id > len(self.trade_history):
            return {'error': 'Invalid trade ID'}
        
        trade = self.trade_history[trade_id - 1]
        
        if actual_outcome == 'win':
            # Win scenario
            profit = trade['cost'] * (trade['odds'] - 1)
            self.current_bankroll += trade['cost'] + profit
            
            self.performance_metrics['winning_trades'] += 1
            self.performance_metrics['total_pnl'] += profit
            
        else:
            # Loss scenario  
            loss = trade['cost']
            self.current_bankroll += trade['cost']  # Return remaining bankroll
            
            self.performance_metrics['losing_trades'] += 1
            self.performance_metrics['total_pnl'] -= loss
        
        # Update performance metrics
        win_rate = (self.performance_metrics['winning_trades'] / 
                   self.performance_metrics['total_trades'])
        
        total_return = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll
        
        return {
            'trade_id': trade_id,
            'actual_outcome': actual_outcome,
            'profit_loss': profit if actual_outcome == 'win' else -loss,
            'current_bankroll': self.current_bankroll,
            'total_return': total_return,
            'win_rate': win_rate,
            'trade_count': self.performance_metrics['total_trades']
        }
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get comprehensive educational performance summary"""
        
        total_return = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll
        
        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_return_pct': total_return * 100,
            'total_trades': self.performance_metrics['total_trades'],
            'winning_trades': self.performance_metrics['winning_trades'],
            'losing_trades': self.performance_metrics['losing_trades'],
            'win_rate': (self.performance_metrics['winning_trades'] / 
                        max(1, self.performance_metrics['total_trades'])) * 100,
            'total_pnl': self.performance_metrics['total_pnl'],
            'average_trade_value': self.current_bankroll / max(1, self.performance_metrics['total_trades'])
        }


def create_educational_portfolio() -> List[EducationalAsset]:
    """Create educational portfolio for learning purposes"""
    
    return [
        EducationalAsset("EDU_SP500", "Educational S&P 500 ETF", AssetClass.EQUITY, 
                        0.10, 0.15, 100.0, 0.02),
        EducationalAsset("EDU_BONDS", "Educational Bond Fund", AssetClass.BOND,
                        0.04, 0.05, 100.0, 0.03),
        EducationalAsset("EDU_GOLD", "Educational Gold ETF", AssetClass.COMMODITY,
                        0.06, 0.18, 100.0, 0.0),
        EducationalAsset("EDU_REIT", "Educational REIT", AssetClass.REAL_ESTATE,
                        0.08, 0.12, 100.0, 0.04),
        EducationalAsset("EDU_CASH", "Educational Cash", AssetClass.CASH,
                        0.02, 0.01, 100.0, 0.0)
    ]


def demonstrate_kelly_criterion():
    """Educational demonstration of Kelly Criterion"""
    
    print("🎓 KELLY CRITERION EDUCATIONAL DEMONSTRATION")
    print("=" * 50)
    
    # Scenario: Sports betting example (educational)
    win_probability = 0.60
    odds = 2.0
    bankroll = 1000
    
    kelly_fraction = KellyCriterion.calculate_kelly_fraction(
        win_probability, odds, bankroll
    )
    
    print(f"Scenario: Educational Sports Betting")
    print(f"Win Probability: {win_probability*100:.1f}%")
    print(f"Odds: {odds:.2f}")
    print(f"Bankroll: ${bankroll}")
    print(f"Kelly Fraction: {kelly_fraction*100:.2f}%")
    print(f"Optimal Stake: ${kelly_fraction * bankroll:.2f}")
    print(f"Expected Value: {(win_probability * odds - 1)*100:.1f}%")
    
    # Simulation
    simulation = KellyCriterion.simulate_kelly_path(win_probability, odds)
    print(f"\nEducational Simulation Results:")
    print(f"Mean Return: {simulation['mean_return']*100:.2f}%")
    print(f"Std Deviation: {simulation['std_return']*100:.2f}%")
    print(f"Probability of Profit: {simulation['probability_positive']*100:.1f}%")


def demonstrate_expected_value():
    """Educational demonstration of Expected Value calculation"""
    
    print("\n📊 EXPECTED VALUE EDUCATIONAL DEMONSTRATION")  
    print("=" * 50)
    
    # Scenario: Investment decision with 3 possible outcomes
    probabilities = [0.3, 0.5, 0.2]  # Must sum to 1.0
    outcomes = [100, 0, -50]  # Profits/losses
    
    ev_result = ExpectedValueCalculator.calculate_ev(probabilities, outcomes)
    
    print(f"Investment Decision Example:")
    print(f"Outcome 1: 30% chance, +$100 profit")
    print(f"Outcome 2: 50% chance, $0 (break-even)")
    print(f"Outcome 3: 20% chance, -$50 loss")
    print(f"\nExpected Value: ${ev_result['expected_value']:.2f}")
    print(f"Standard Deviation: ${ev_result['std_deviation']:.2f}")
    print(f"Risk Level: {ev_result['risk_level']}")
    print(f"Coefficient of Variation: {ev_result['coefficient_variation']:.2f}")
    
    # Educational interpretation
    if ev_result['expected_value'] > 0:
        print("✅ Positive EV - Educationally worthwhile investment")
    else:
        print("❌ Negative EV - Educationally not recommended")


def demonstrate_portfolio_optimization():
    """Educational demonstration of Modern Portfolio Theory"""
    
    print("\n💼 PORTFOLIO OPTIMIZATION EDUCATIONAL DEMONSTRATION")
    print("=" * 60)
    
    assets = create_educational_portfolio()
    optimizer = PortfolioOptimizer(assets)
    
    # Generate efficient frontier
    efficient_frontier = optimizer.generate_efficient_frontier(1000)
    
    print(f"Generated {len(efficient_frontier)} educational portfolios")
    print(f"Return range: {efficient_frontier['return'].min()*100:.2f}% - {efficient_frontier['return'].max()*100:.2f}%")
    print(f"Risk range: {efficient_frontier['volatility'].min()*100:.2f}% - {efficient_frontier['volatility'].max()*100:.2f}%")
    
    # Find optimal portfolio for conservative investor
    conservative_target = 0.08  # 8% risk tolerance
    optimal = optimizer.find_optimal_portfolio(conservative_target)
    
    print(f"\nOptimal Portfolio for {conservative_target*100:.1f}% Risk:")
    print(f"Expected Return: {optimal['actual_return']*100:.2f}%")
    print(f"Actual Risk: {optimal['actual_risk']*100:.2f}%")
    print(f"Sharpe Ratio: {optimal['sharpe_ratio']:.3f}")
    
    print(f"\nOptimal Weights:")
    for symbol, weight in optimal['optimal_weights'].items():
        print(f"  {symbol}: {weight*100:.1f}%")


def demonstrate_risk_management():
    """Educational demonstration of risk management techniques"""
    
    print("\n🛡️ RISK MANAGEMENT EDUCATIONAL DEMONSTRATION")
    print("=" * 50)
    
    risk_manager = RiskManager(max_portfolio_risk=0.02)  # 2% max risk
    
    # Calculate position sizing for educational asset
    asset_return = 0.10
    asset_volatility = 0.15
    bankroll = 10000
    target_risk = 0.02
    
    position_size = risk_manager.calculate_position_sizing(
        asset_return, asset_volatility, bankroll, target_risk
    )
    
    print(f"Position Sizing Example:")
    print(f"Asset Return: {asset_return*100:.1f}%")
    print(f"Asset Volatility: {asset_volatility*100:.1f}%")
    print(f"Bankroll: ${bankroll}")
    print(f"Target Risk: {target_risk*100:.1f}%")
    print(f"Optimal Position Size: {position_size} shares")
    
    # Portfolio VaR calculation
    portfolio_weights = [0.6, 0.3, 0.1]  # 60% equity, 30% bonds, 10% gold
    volatilities = [0.15, 0.05, 0.18]   # Annual volatilities
    
    # Simple correlation matrix (educational)
    correlation_matrix = np.array([
        [1.0, 0.2, 0.0],    # Equity correlations
        [0.2, 1.0, 0.1],    # Bond correlations  
        [0.0, 0.1, 1.0]     # Gold correlations
    ])
    
    portfolio_var = risk_manager.calculate_portfolio_var(
        portfolio_weights, volatilities, correlation_matrix
    )
    
    print(f"\nPortfolio VaR (95% confidence):")
    print(f"Annual Portfolio VaR: {portfolio_var*100:.2f}%")
    print(f"VaR at 99% confidence: {portfolio_var*2.33*100:.2f}%")


def demonstrate_trading_simulation():
    """Educational trading simulation demonstration"""
    
    print("\n🎮 EDUCATIONAL TRADING SIMULATION")
    print("=" * 40)
    
    simulator = EducationalTradingSimulator(initial_bankroll=10000)
    
    # Simulate several educational trades
    educational_signals = [
        {'confidence': 0.65, 'odds': 1.80, 'description': 'Strong momentum signal'},
        {'confidence': 0.55, 'odds': 2.20, 'description': 'Value opportunity'},
        {'confidence': 0.75, 'odds': 1.50, 'description': 'High confidence trade'}
    ]
    
    print(f"Initial Bankroll: ${simulator.initial_bankroll}")
    
    executed_trades = []
    
    for i, signal in enumerate(educational_signals, 1):
        result = simulator.simulate_trade(
            f"EDU_ASSET_{i}", signal, price=100.0
        )
        
        if result['executed']:
            executed_trades.append((i, result))
            print(f"\nTrade {i}: {signal['description']}")
            print(f"  Confidence: {signal['confidence']*100:.0f}%")
            print(f"  Odds: {signal['odds']:.2f}")
            print(f"  Position Size: {result['position_size']} shares")
            print(f"  Kelly Fraction: {result['kelly_fraction']*100:.2f}%")
            
            # Simulate outcomes
            outcomes = ['win', 'loss', 'win']
            outcome_sim = simulator.simulate_outcome(i, outcomes[i-1])
            print(f"  Outcome: {outcomes[i-1].upper()}")
            print(f"  P&L: ${outcome_sim['profit_loss']:.2f}")
    
    # Final performance summary
    summary = simulator.get_performance_summary()
    
    print(f"\n📈 SIMULATION SUMMARY")
    print(f"Final Bankroll: ${summary['current_bankroll']:.2f}")
    print(f"Total Return: {summary['total_return_pct']:.2f}%")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']:.1f}%")
    print(f"Total P&L: ${summary['total_pnl']:.2f}")


if __name__ == "__main__":
    """Educational demonstration of financial modeling concepts"""
    
    print("🎓 BETFURY.IO EDUCATIONAL FINANCIAL MODELING FRAMEWORK")
    print("=" * 60)
    print("⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY")
    print("⚠️  This framework demonstrates quantitative finance concepts")
    print("⚠️  for educational and learning purposes only")
    print()
    
    # Run educational demonstrations
    demonstrate_kelly_criterion()
    demonstrate_expected_value()
    demonstrate_portfolio_optimization()
    demonstrate_risk_management()
    demonstrate_trading_simulation()
    
    print("\n" + "="*60)
    print("✅ EDUCATIONAL FINANCIAL MODELING DEMONSTRATION COMPLETE")
    print("🔍 These concepts are fundamental to:")
    print("   • Portfolio Theory (Markowitz)")
    print("   • Risk Management")
    print("   • Quantitative Trading")
    print("   • Investment Analysis")
    print("   • Financial Engineering")
    print("=" * 60)