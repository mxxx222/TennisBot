#!/usr/bin/env python3
"""
💰 PROFIT SHARING TRACKER
=========================
50/50 tuottojaon seurantajärjestelmä läpinäkyvään voittojen jakamiseen.

Ominaisuudet:
- Automaattinen tuottojen seuranta
- Kuukausittainen jako (50/50)
- Läpinäkyvä raportointi
- Historiallinen data
- Verojen huomiointi
- Kustannusten jako

Tavoite: Reilu ja läpinäkyvä tuottojen jako kumppaneiden välillä
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import calendar
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Yksittäinen transaktio"""
    transaction_id: str
    date: datetime
    type: str  # 'bet', 'win', 'loss', 'expense', 'deposit', 'withdrawal'
    description: str
    amount: float
    
    # Bet-specific
    match_id: Optional[str] = None
    sport: Optional[str] = None
    odds: Optional[float] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MonthlyStatement:
    """Kuukausittainen tiliote"""
    year: int
    month: int
    
    # Alkutilanne
    starting_balance: float = 0.0
    
    # Transaktiot
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    total_bets_placed: float = 0.0
    total_winnings: float = 0.0
    total_losses: float = 0.0
    total_expenses: float = 0.0
    
    # Lopputilanne
    ending_balance: float = 0.0
    gross_profit: float = 0.0
    net_profit: float = 0.0
    
    # Jako
    partner_share: float = 0.0
    my_share: float = 0.0
    
    # Tilastot
    total_bets: int = 0
    winning_bets: int = 0
    win_rate: float = 0.0
    roi: float = 0.0
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProfitSharingConfig:
    """Tuottojaon konfiguraatio"""
    partner_percentage: float = 50.0  # 50%
    my_percentage: float = 50.0       # 50%
    
    # Kustannusten jako
    shared_expenses: bool = True
    expense_split_ratio: float = 50.0  # 50/50 myös kuluissa
    
    # Vähimmäistuotto jakoa varten
    minimum_profit_for_split: float = 100.0  # €100
    
    # Maksuasetukset
    payment_day: int = 1  # Kuukauden ensimmäinen päivä
    currency: str = "EUR"
    
    # Verotus (informatiivinen)
    tax_rate: float = 30.0  # 30% vero voitoista


class ProfitSharingTracker:
    """
    Profit Sharing Tracker - seuraa ja jakaa voitot 50/50
    """
    
    def __init__(self, config: ProfitSharingConfig = None, data_file: str = None):
        """
        Initialize Profit Sharing Tracker
        
        Args:
            config: Tuottojaon konfiguraatio
            data_file: Datatiedoston polku
        """
        logger.info("💰 Initializing Profit Sharing Tracker...")
        
        self.config = config or ProfitSharingConfig()
        self.data_file = data_file or "profit_sharing_data.json"
        
        # Data
        self.transactions: List[Transaction] = []
        self.monthly_statements: List[MonthlyStatement] = []
        self.current_balance = 0.0
        
        # Load existing data
        self._load_data()
        
        logger.info("✅ Profit Sharing Tracker initialized")
    
    def _load_data(self):
        """Lataa olemassa oleva data"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Load transactions
                for t_data in data.get('transactions', []):
                    t_data['date'] = datetime.fromisoformat(t_data['date'])
                    t_data['created_at'] = datetime.fromisoformat(t_data['created_at'])
                    transaction = Transaction(**t_data)
                    self.transactions.append(transaction)
                
                # Load monthly statements
                for s_data in data.get('monthly_statements', []):
                    s_data['generated_at'] = datetime.fromisoformat(s_data['generated_at'])
                    statement = MonthlyStatement(**s_data)
                    self.monthly_statements.append(statement)
                
                # Load balance
                self.current_balance = data.get('current_balance', 0.0)
                
                logger.info(f"📊 Loaded {len(self.transactions)} transactions and {len(self.monthly_statements)} statements")
        
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing data: {e}")
    
    def _save_data(self):
        """Tallenna data"""
        try:
            data = {
                'transactions': [asdict(t) for t in self.transactions],
                'monthly_statements': [asdict(s) for s in self.monthly_statements],
                'current_balance': self.current_balance,
                'config': asdict(self.config),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"💾 Data saved to {self.data_file}")
        
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def add_deposit(self, amount: float, description: str = "Bankroll deposit") -> str:
        """
        Lisää talletus
        
        Args:
            amount: Summa
            description: Kuvaus
            
        Returns:
            Transaction ID
        """
        transaction_id = f"dep_{len(self.transactions)+1:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction = Transaction(
            transaction_id=transaction_id,
            date=datetime.now(),
            type='deposit',
            description=description,
            amount=amount
        )
        
        self.transactions.append(transaction)
        self.current_balance += amount
        
        self._save_data()
        
        logger.info(f"💰 Deposit added: €{amount:.2f} - {description}")
        return transaction_id
    
    def add_bet(self, amount: float, match_id: str, sport: str, odds: float, description: str) -> str:
        """
        Lisää veto
        
        Args:
            amount: Panoksen määrä
            match_id: Ottelun ID
            sport: Laji
            odds: Kertoimet
            description: Kuvaus
            
        Returns:
            Transaction ID
        """
        transaction_id = f"bet_{len(self.transactions)+1:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction = Transaction(
            transaction_id=transaction_id,
            date=datetime.now(),
            type='bet',
            description=description,
            amount=-amount,  # Negative because it's money going out
            match_id=match_id,
            sport=sport,
            odds=odds
        )
        
        self.transactions.append(transaction)
        self.current_balance -= amount
        
        self._save_data()
        
        logger.info(f"🎲 Bet placed: €{amount:.2f} - {description}")
        return transaction_id
    
    def add_win(self, amount: float, match_id: str, description: str) -> str:
        """
        Lisää voitto
        
        Args:
            amount: Voittosumma
            match_id: Ottelun ID
            description: Kuvaus
            
        Returns:
            Transaction ID
        """
        transaction_id = f"win_{len(self.transactions)+1:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction = Transaction(
            transaction_id=transaction_id,
            date=datetime.now(),
            type='win',
            description=description,
            amount=amount,
            match_id=match_id
        )
        
        self.transactions.append(transaction)
        self.current_balance += amount
        
        self._save_data()
        
        logger.info(f"✅ Win recorded: €{amount:.2f} - {description}")
        return transaction_id
    
    def add_loss(self, match_id: str, description: str) -> str:
        """
        Lisää tappio (ei muuta saldoa, koska panos on jo vähennetty)
        
        Args:
            match_id: Ottelun ID
            description: Kuvaus
            
        Returns:
            Transaction ID
        """
        transaction_id = f"loss_{len(self.transactions)+1:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction = Transaction(
            transaction_id=transaction_id,
            date=datetime.now(),
            type='loss',
            description=description,
            amount=0.0,  # No balance change, stake already deducted
            match_id=match_id
        )
        
        self.transactions.append(transaction)
        
        self._save_data()
        
        logger.info(f"❌ Loss recorded: {description}")
        return transaction_id
    
    def add_expense(self, amount: float, description: str, shared: bool = True) -> str:
        """
        Lisää kulu
        
        Args:
            amount: Summa
            description: Kuvaus
            shared: Jaetaanko kulu (50/50)
            
        Returns:
            Transaction ID
        """
        transaction_id = f"exp_{len(self.transactions)+1:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction = Transaction(
            transaction_id=transaction_id,
            date=datetime.now(),
            type='expense',
            description=f"{'[SHARED] ' if shared else '[PERSONAL] '}{description}",
            amount=-amount
        )
        
        self.transactions.append(transaction)
        self.current_balance -= amount
        
        self._save_data()
        
        logger.info(f"💸 Expense added: €{amount:.2f} - {description} ({'shared' if shared else 'personal'})")
        return transaction_id
    
    def generate_monthly_statement(self, year: int, month: int) -> MonthlyStatement:
        """
        Generoi kuukausittainen tiliote
        
        Args:
            year: Vuosi
            month: Kuukausi (1-12)
            
        Returns:
            MonthlyStatement
        """
        logger.info(f"📊 Generating monthly statement for {year}-{month:02d}")
        
        # Filter transactions for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        month_transactions = [
            t for t in self.transactions 
            if start_date <= t.date <= end_date
        ]
        
        # Calculate starting balance (balance at start of month)
        pre_month_transactions = [
            t for t in self.transactions 
            if t.date < start_date
        ]
        starting_balance = sum(t.amount for t in pre_month_transactions)
        
        # Calculate monthly totals
        deposits = sum(t.amount for t in month_transactions if t.type == 'deposit')
        withdrawals = abs(sum(t.amount for t in month_transactions if t.type == 'withdrawal'))
        bets_placed = abs(sum(t.amount for t in month_transactions if t.type == 'bet'))
        winnings = sum(t.amount for t in month_transactions if t.type == 'win')
        expenses = abs(sum(t.amount for t in month_transactions if t.type == 'expense'))
        
        # Calculate ending balance
        ending_balance = starting_balance + sum(t.amount for t in month_transactions)
        
        # Calculate profits
        gross_profit = winnings - bets_placed
        net_profit = gross_profit - expenses
        
        # Calculate profit sharing
        if net_profit >= self.config.minimum_profit_for_split:
            partner_share = net_profit * (self.config.partner_percentage / 100)
            my_share = net_profit * (self.config.my_percentage / 100)
        else:
            partner_share = 0.0
            my_share = 0.0
        
        # Calculate betting statistics
        bet_transactions = [t for t in month_transactions if t.type == 'bet']
        win_transactions = [t for t in month_transactions if t.type == 'win']
        
        total_bets = len(bet_transactions)
        winning_bets = len(win_transactions)
        win_rate = (winning_bets / total_bets) if total_bets > 0 else 0.0
        roi = (gross_profit / bets_placed * 100) if bets_placed > 0 else 0.0
        
        # Create statement
        statement = MonthlyStatement(
            year=year,
            month=month,
            starting_balance=starting_balance,
            total_deposits=deposits,
            total_withdrawals=withdrawals,
            total_bets_placed=bets_placed,
            total_winnings=winnings,
            total_losses=bets_placed - winnings,  # Losses = stakes - winnings
            total_expenses=expenses,
            ending_balance=ending_balance,
            gross_profit=gross_profit,
            net_profit=net_profit,
            partner_share=partner_share,
            my_share=my_share,
            total_bets=total_bets,
            winning_bets=winning_bets,
            win_rate=win_rate,
            roi=roi
        )
        
        # Save statement
        self.monthly_statements.append(statement)
        self._save_data()
        
        logger.info(f"✅ Monthly statement generated - Net profit: €{net_profit:.2f}")
        return statement
    
    def get_current_month_summary(self) -> Dict[str, Any]:
        """Hae kuluvan kuukauden yhteenveto"""
        
        now = datetime.now()
        current_month_transactions = [
            t for t in self.transactions 
            if t.date.year == now.year and t.date.month == now.month
        ]
        
        bets_placed = abs(sum(t.amount for t in current_month_transactions if t.type == 'bet'))
        winnings = sum(t.amount for t in current_month_transactions if t.type == 'win')
        expenses = abs(sum(t.amount for t in current_month_transactions if t.type == 'expense'))
        
        gross_profit = winnings - bets_placed
        net_profit = gross_profit - expenses
        
        bet_count = len([t for t in current_month_transactions if t.type == 'bet'])
        win_count = len([t for t in current_month_transactions if t.type == 'win'])
        
        return {
            'month': f"{now.year}-{now.month:02d}",
            'current_balance': self.current_balance,
            'bets_placed': bets_placed,
            'winnings': winnings,
            'expenses': expenses,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'total_bets': bet_count,
            'winning_bets': win_count,
            'win_rate': (win_count / bet_count) if bet_count > 0 else 0.0,
            'roi': (gross_profit / bets_placed * 100) if bets_placed > 0 else 0.0,
            'projected_partner_share': net_profit * 0.5 if net_profit > 0 else 0.0,
            'projected_my_share': net_profit * 0.5 if net_profit > 0 else 0.0
        }
    
    def print_monthly_statement(self, statement: MonthlyStatement):
        """Tulosta kuukausittainen tiliote"""
        
        month_name = calendar.month_name[statement.month]
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  💰 MONTHLY PROFIT SHARING STATEMENT                        ║
║  ==========================================================  ║
║                                                              ║
║  Period: {month_name} {statement.year}                       ║
║  Generated: {statement.generated_at.strftime('%Y-%m-%d %H:%M')} ║
╚══════════════════════════════════════════════════════════════╝

💰 FINANCIAL SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Starting Balance: €{statement.starting_balance:,.2f}
  Ending Balance: €{statement.ending_balance:,.2f}
  
  Deposits: €{statement.total_deposits:,.2f}
  Withdrawals: €{statement.total_withdrawals:,.2f}
  
  Total Bets Placed: €{statement.total_bets_placed:,.2f}
  Total Winnings: €{statement.total_winnings:,.2f}
  Total Losses: €{statement.total_losses:,.2f}
  Total Expenses: €{statement.total_expenses:,.2f}

📊 PERFORMANCE METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Bets: {statement.total_bets}
  Winning Bets: {statement.winning_bets}
  Win Rate: {statement.win_rate*100:.1f}%
  ROI: {statement.roi:+.1f}%
  
  Gross Profit: €{statement.gross_profit:+,.2f}
  Net Profit: €{statement.net_profit:+,.2f}

💵 PROFIT SHARING (50/50):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Partner Share: €{statement.partner_share:,.2f}
  My Share: €{statement.my_share:,.2f}
  
  {'✅ PROFIT TO DISTRIBUTE' if statement.net_profit > 0 else '❌ NO PROFIT TO DISTRIBUTE'}
  {'Payment due by: ' + str(statement.year) + '-' + str(statement.month+1 if statement.month < 12 else 1).zfill(2) + '-01' if statement.net_profit > 0 else ''}

💡 TAX INFORMATION (Informational):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Estimated Tax ({self.config.tax_rate}%): €{statement.net_profit * (self.config.tax_rate/100):,.2f}
  After-tax Profit: €{statement.net_profit * (1 - self.config.tax_rate/100):,.2f}
        """)
    
    def get_annual_summary(self, year: int) -> Dict[str, Any]:
        """Hae vuosittainen yhteenveto"""
        
        year_statements = [s for s in self.monthly_statements if s.year == year]
        
        if not year_statements:
            return {}
        
        total_net_profit = sum(s.net_profit for s in year_statements)
        total_partner_share = sum(s.partner_share for s in year_statements)
        total_my_share = sum(s.my_share for s in year_statements)
        total_bets = sum(s.total_bets for s in year_statements)
        total_winning_bets = sum(s.winning_bets for s in year_statements)
        
        avg_win_rate = statistics.mean([s.win_rate for s in year_statements if s.total_bets > 0]) if year_statements else 0.0
        avg_roi = statistics.mean([s.roi for s in year_statements if s.total_bets_placed > 0]) if year_statements else 0.0
        
        return {
            'year': year,
            'months_active': len(year_statements),
            'total_net_profit': total_net_profit,
            'total_partner_share': total_partner_share,
            'total_my_share': total_my_share,
            'total_bets': total_bets,
            'total_winning_bets': total_winning_bets,
            'annual_win_rate': avg_win_rate,
            'annual_roi': avg_roi,
            'monthly_statements': year_statements
        }


def main():
    """Test Profit Sharing Tracker"""
    print("💰 PROFIT SHARING TRACKER TEST")
    print("=" * 50)
    
    # Initialize tracker
    config = ProfitSharingConfig(
        partner_percentage=50.0,
        my_percentage=50.0,
        minimum_profit_for_split=100.0
    )
    
    tracker = ProfitSharingTracker(config=config, data_file="test_profit_sharing.json")
    
    # Simulate some activity
    print("\n💰 Simulating betting activity...")
    
    # Initial deposit
    tracker.add_deposit(10000.0, "Initial bankroll")
    
    # Some bets and results
    bet1 = tracker.add_bet(500.0, "match_001", "tennis", 2.1, "Djokovic vs Alcaraz")
    tracker.add_win(1050.0, "match_001", "Djokovic won")
    
    bet2 = tracker.add_bet(300.0, "match_002", "football", 1.8, "Man City vs Arsenal")
    tracker.add_loss("match_002", "Man City lost")
    
    bet3 = tracker.add_bet(400.0, "match_003", "tennis", 2.5, "Swiatek vs Gauff")
    tracker.add_win(1000.0, "match_003", "Swiatek won")
    
    # Add some expenses
    tracker.add_expense(50.0, "Data subscription", shared=True)
    tracker.add_expense(25.0, "VPN service", shared=True)
    
    # Generate monthly statement
    now = datetime.now()
    statement = tracker.generate_monthly_statement(now.year, now.month)
    
    # Print statement
    tracker.print_monthly_statement(statement)
    
    # Current month summary
    print("\n📊 CURRENT MONTH SUMMARY:")
    summary = tracker.get_current_month_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: €{value:,.2f}" if 'rate' not in key and 'roi' not in key else f"  {key}: {value:.1f}%")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
