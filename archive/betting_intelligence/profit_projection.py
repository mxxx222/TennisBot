#!/usr/bin/env python3
"""
💰 SMART VALUE DETECTOR - PROFIT PROJECTION
==========================================

Realistinen tuottoennuste laillisella järjestelmällä.

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

from typing import List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MonthlyProjection:
    """Kuukausittainen ennuste"""
    month: int
    starting_balance: float
    monthly_profit: float
    ending_balance: float
    cumulative_profit: float
    roi_percentage: float
    trades_count: int


class ProfitProjection:
    """
    Realistinen tuottoennuste laillisella järjestelmällä
    """
    
    @staticmethod
    def project_12_months(initial_bankroll: float = 1000.0,
                          monthly_roi: float = 0.15,
                          conservative: bool = True) -> List[MonthlyProjection]:
        """
        Konservatiivinen ennuste:
        - 15% keskimääräinen kuukausi ROI
        - Kelly Criterion hedge (25%)
        - 5 tradea/päivä
        
        Args:
            initial_bankroll: Alkupankkisaldo
            monthly_roi: Kuukausittainen ROI (default 15%)
            conservative: Käytä konservatiivista mallia
        """
        
        months = []
        bankroll = initial_bankroll
        
        # Adjust ROI if conservative
        if conservative:
            monthly_roi = monthly_roi * 0.85  # 85% of target
        
        for month in range(1, 13):
            # Monthly return
            monthly_return = bankroll * monthly_roi
            bankroll_end = bankroll + monthly_return
            
            # Skaalausta kuukausi 4 jälkeen (compound growth)
            if month % 3 == 0 and month > 3:
                # Slight boost every 3 months
                bankroll_end *= 1.05
            
            # Estimate trades (5 per day, ~150 per month)
            trades_count = 150
            
            months.append(MonthlyProjection(
                month=month,
                starting_balance=bankroll,
                monthly_profit=monthly_return,
                ending_balance=bankroll_end,
                cumulative_profit=bankroll_end - initial_bankroll,
                roi_percentage=monthly_roi * 100,
                trades_count=trades_count
            ))
            
            bankroll = bankroll_end
        
        return months
    
    @staticmethod
    def project_aggressive(initial_bankroll: float = 1000.0) -> List[MonthlyProjection]:
        """
        Aggressiivinen ennuste (20-25% kuukausi ROI)
        """
        return ProfitProjection.project_12_months(
            initial_bankroll=initial_bankroll,
            monthly_roi=0.20,
            conservative=False
        )
    
    @staticmethod
    def project_conservative(initial_bankroll: float = 1000.0) -> List[MonthlyProjection]:
        """
        Konservatiivinen ennuste (12-15% kuukausi ROI)
        """
        return ProfitProjection.project_12_months(
            initial_bankroll=initial_bankroll,
            monthly_roi=0.12,
            conservative=True
        )
    
    @staticmethod
    def print_projection(projections: List[MonthlyProjection], 
                        title: str = "SMART VALUE DETECTOR - 12 KUUKAUDEN ENNUSTE"):
        """Print projection table"""
        print(f"""
╔════════════════════════════════════════════════════════════════╗
║     💰 {title}
║     ({projections[0].roi_percentage:.0f}% kuukausi ROI - {'KONSERVATIIVINEN' if projections[0].roi_percentage < 18 else 'AGGRESSIIVINEN'})
╠════════════════════════════════════════════════════════════════╣
""")
        
        for m in projections:
            print(f"║ KK {m.month:2d} | Start: €{m.starting_balance:8,.0f} | "
                  f"Voitto: €{m.monthly_profit:8,.0f} | "
                  f"End: €{m.ending_balance:8,.0f} |")
        
        final = projections[-1].ending_balance
        profit = final - projections[0].starting_balance
        initial = projections[0].starting_balance
        
        print(f"""╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  🎉 VUODEN LOPUSSA:                                            ║
║  ├─ Alkupankkisaldo: €{initial:,.0f}                                   ║
║  ├─ Loppupankkisaldo: €{final:,.0f}                            ║
║  ├─ Kokonaisvoitto: €{profit:,.0f}                              ║
║  └─ ROI: {(profit/initial)*100:.0f}% vuodessa ✅              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
        """)
    
    @staticmethod
    def compare_scenarios(initial_bankroll: float = 1000.0):
        """Compare different scenarios"""
        conservative = ProfitProjection.project_conservative(initial_bankroll)
        moderate = ProfitProjection.project_12_months(initial_bankroll, 0.15, True)
        aggressive = ProfitProjection.project_aggressive(initial_bankroll)
        
        print("""
╔════════════════════════════════════════════════════════════════╗
║     📊 SKENAARIO-VERTAILU
╠════════════════════════════════════════════════════════════════╣
""")
        
        scenarios = [
            ("Konservatiivinen (12%)", conservative),
            ("Keskitaso (15%)", moderate),
            ("Aggressiivinen (20%)", aggressive)
        ]
        
        for name, proj in scenarios:
            final = proj[-1].ending_balance
            profit = final - initial_bankroll
            roi = (profit / initial_bankroll) * 100
            
            print(f"║ {name:30s} │ Loppu: €{final:8,.0f} │ ROI: {roi:5.0f}% │")
        
        print("╚════════════════════════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    print("💰 Profit Projection - Test")
    print("=" * 50)
    
    # Conservative projection
    print("\n📊 KONSERVATIIVINEN ENNUSTE:")
    conservative = ProfitProjection.project_conservative(1000)
    ProfitProjection.print_projection(conservative, "KONSERVATIIVINEN ENNUSTE")
    
    # Moderate projection
    print("\n📊 KESKITASO ENNUSTE:")
    moderate = ProfitProjection.project_12_months(1000, 0.15, True)
    ProfitProjection.print_projection(moderate, "KESKITASO ENNUSTE")
    
    # Compare scenarios
    ProfitProjection.compare_scenarios(1000)

