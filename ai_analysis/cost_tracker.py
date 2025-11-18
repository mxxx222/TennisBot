"""
Cost Tracking System for Venice AI Integration
Monitors and reports cost savings vs OpenAI baseline
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class CostEntry:
    """Individual cost tracking entry"""
    timestamp: datetime
    feature: str  # 'match_analysis', 'pattern_detection', 'optimization'
    model_used: str  # 'llama-3.3-70b', 'llama-3.2-3b'
    input_tokens: int
    output_tokens: int
    venice_cost: float
    openai_equivalent_cost: float
    savings: float
    request_id: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CostEntry':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class CostSummary:
    """Cost summary for a time period"""
    period_start: datetime
    period_end: datetime
    total_requests: int
    total_venice_cost: float
    total_openai_equivalent: float
    total_savings: float
    savings_percentage: float
    feature_breakdown: Dict[str, Dict]
    model_breakdown: Dict[str, Dict]
    daily_costs: List[Dict]

class VeniceAICostTracker:
    """Tracks and analyzes Venice AI costs vs OpenAI baseline"""
    
    def __init__(self, log_file: str = "venice_ai_costs.json"):
        self.log_file = log_file
        self.cost_entries: List[CostEntry] = []
        self.daily_budgets = {
            'match_analysis': 5.00,
            'pattern_detection': 2.00,
            'optimization': 1.00
        }
        self.monthly_budget = 50.00
        
        # Load existing data
        self._load_cost_data()
        
        # Performance tracking
        self.total_requests = 0
        self.total_savings = 0.0
        
    def log_cost(self, feature: str, model_used: str, input_tokens: int, 
                 output_tokens: int, venice_cost: float, request_id: str = "", 
                 is_openai: bool = False) -> float:
        """Log a cost entry and return savings amount"""
        
        # Calculate costs and savings
        if is_openai:
            # This is actual OpenAI cost, so no savings vs itself
            openai_equivalent = venice_cost  # venice_cost is actually OpenAI cost here
            savings = 0.0
        else:
            # This is Venice AI cost, calculate OpenAI equivalent
            # GPT-4o pricing: $5.00 input + $15.00 output per 1M tokens
            openai_input_cost = (input_tokens / 1_000_000) * 5.00
            openai_output_cost = (output_tokens / 1_000_000) * 15.00
            openai_equivalent = openai_input_cost + openai_output_cost
            savings = openai_equivalent - venice_cost
        
        # Create cost entry
        entry = CostEntry(
            timestamp=datetime.now(),
            feature=feature,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            venice_cost=venice_cost,
            openai_equivalent_cost=openai_equivalent,
            savings=savings,
            request_id=request_id
        )
        
        # Add to tracking
        self.cost_entries.append(entry)
        self.total_requests += 1
        self.total_savings += savings
        
        # Save to file
        self._save_cost_data()
        
        # Check budgets
        self._check_budget_alerts()
        
        logger.info(f"Cost logged: {feature} - Venice: ${venice_cost:.4f}, "
                   f"OpenAI equiv: ${openai_equivalent:.4f}, "
                   f"Saved: ${savings:.4f} ({(savings/openai_equivalent)*100:.1f}%)")
        
        return savings
    
    def get_daily_summary(self, date: datetime = None) -> CostSummary:
        """Get cost summary for a specific day"""
        
        if date is None:
            date = datetime.now()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return self._generate_summary(start_date, end_date)
    
    def get_weekly_summary(self) -> CostSummary:
        """Get cost summary for the past week"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        return self._generate_summary(start_date, end_date)
    
    def get_monthly_summary(self) -> CostSummary:
        """Get cost summary for the current month"""
        
        now = datetime.now()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        
        return self._generate_summary(start_date, end_date)
    
    def _generate_summary(self, start_date: datetime, end_date: datetime) -> CostSummary:
        """Generate cost summary for date range"""
        
        # Filter entries for date range
        period_entries = [
            entry for entry in self.cost_entries
            if start_date <= entry.timestamp <= end_date
        ]
        
        if not period_entries:
            return CostSummary(
                period_start=start_date,
                period_end=end_date,
                total_requests=0,
                total_venice_cost=0.0,
                total_openai_equivalent=0.0,
                total_savings=0.0,
                savings_percentage=0.0,
                feature_breakdown={},
                model_breakdown={},
                daily_costs=[]
            )
        
        # Calculate totals
        total_requests = len(period_entries)
        total_venice_cost = sum(entry.venice_cost for entry in period_entries)
        total_openai_equivalent = sum(entry.openai_equivalent_cost for entry in period_entries)
        total_savings = sum(entry.savings for entry in period_entries)
        savings_percentage = (total_savings / total_openai_equivalent * 100) if total_openai_equivalent > 0 else 0
        
        # Feature breakdown
        feature_breakdown = {}
        for entry in period_entries:
            feature = entry.feature
            if feature not in feature_breakdown:
                feature_breakdown[feature] = {
                    'requests': 0,
                    'venice_cost': 0.0,
                    'openai_equivalent': 0.0,
                    'savings': 0.0
                }
            
            feature_breakdown[feature]['requests'] += 1
            feature_breakdown[feature]['venice_cost'] += entry.venice_cost
            feature_breakdown[feature]['openai_equivalent'] += entry.openai_equivalent_cost
            feature_breakdown[feature]['savings'] += entry.savings
        
        # Model breakdown
        model_breakdown = {}
        for entry in period_entries:
            model = entry.model_used
            if model not in model_breakdown:
                model_breakdown[model] = {
                    'requests': 0,
                    'venice_cost': 0.0,
                    'openai_equivalent': 0.0,
                    'savings': 0.0,
                    'avg_input_tokens': 0,
                    'avg_output_tokens': 0
                }
            
            model_breakdown[model]['requests'] += 1
            model_breakdown[model]['venice_cost'] += entry.venice_cost
            model_breakdown[model]['openai_equivalent'] += entry.openai_equivalent_cost
            model_breakdown[model]['savings'] += entry.savings
        
        # Calculate averages for model breakdown
        for model_data in model_breakdown.values():
            model_entries = [e for e in period_entries if e.model_used == model]
            if model_entries:
                model_data['avg_input_tokens'] = sum(e.input_tokens for e in model_entries) / len(model_entries)
                model_data['avg_output_tokens'] = sum(e.output_tokens for e in model_entries) / len(model_entries)
        
        # Daily costs
        daily_costs = []
        current_date = start_date
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            daily_entries = [
                entry for entry in period_entries
                if current_date <= entry.timestamp < next_date
            ]
            
            daily_cost = {
                'date': current_date.strftime('%Y-%m-%d'),
                'requests': len(daily_entries),
                'venice_cost': sum(entry.venice_cost for entry in daily_entries),
                'openai_equivalent': sum(entry.openai_equivalent_cost for entry in daily_entries),
                'savings': sum(entry.savings for entry in daily_entries)
            }
            daily_costs.append(daily_cost)
            current_date = next_date
        
        return CostSummary(
            period_start=start_date,
            period_end=end_date,
            total_requests=total_requests,
            total_venice_cost=total_venice_cost,
            total_openai_equivalent=total_openai_equivalent,
            total_savings=total_savings,
            savings_percentage=savings_percentage,
            feature_breakdown=feature_breakdown,
            model_breakdown=model_breakdown,
            daily_costs=daily_costs
        )
    
    def _check_budget_alerts(self):
        """Check if budgets are being exceeded"""
        
        today = datetime.now().date()
        
        # Check daily budgets by feature
        for feature, budget in self.daily_budgets.items():
            daily_cost = self._get_daily_cost_by_feature(feature, today)
            
            if daily_cost > budget * 0.8:  # 80% threshold
                logger.warning(f"Daily budget alert: {feature} at ${daily_cost:.2f} "
                             f"(80% of ${budget:.2f} budget)")
            
            if daily_cost > budget:
                logger.error(f"Daily budget exceeded: {feature} at ${daily_cost:.2f} "
                           f"(over ${budget:.2f} budget)")
        
        # Check monthly budget
        monthly_summary = self.get_monthly_summary()
        if monthly_summary.total_venice_cost > self.monthly_budget * 0.8:
            logger.warning(f"Monthly budget alert: ${monthly_summary.total_venice_cost:.2f} "
                         f"(80% of ${self.monthly_budget:.2f} budget)")
        
        if monthly_summary.total_venice_cost > self.monthly_budget:
            logger.error(f"Monthly budget exceeded: ${monthly_summary.total_venice_cost:.2f} "
                       f"(over ${self.monthly_budget:.2f} budget)")
    
    def _get_daily_cost_by_feature(self, feature: str, date: datetime.date) -> float:
        """Get daily cost for specific feature"""
        
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        daily_entries = [
            entry for entry in self.cost_entries
            if (entry.feature == feature and 
                start_datetime <= entry.timestamp < end_datetime)
        ]
        
        return sum(entry.venice_cost for entry in daily_entries)
    
    def _save_cost_data(self):
        """Save cost data to JSON file"""
        
        try:
            # Keep only last 10,000 entries to prevent file from growing too large
            if len(self.cost_entries) > 10000:
                self.cost_entries = self.cost_entries[-5000:]
            
            data = {
                'entries': [entry.to_dict() for entry in self.cost_entries],
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_entries': len(self.cost_entries),
                    'total_requests': self.total_requests,
                    'total_savings': self.total_savings
                }
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cost data: {e}")
    
    def _load_cost_data(self):
        """Load cost data from JSON file"""
        
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                
                # Load entries
                self.cost_entries = [
                    CostEntry.from_dict(entry_data) 
                    for entry_data in data.get('entries', [])
                ]
                
                # Load metadata
                metadata = data.get('metadata', {})
                self.total_requests = metadata.get('total_requests', 0)
                self.total_savings = metadata.get('total_savings', 0.0)
                
                logger.info(f"Loaded {len(self.cost_entries)} cost entries from {self.log_file}")
            
        except Exception as e:
            logger.error(f"Failed to load cost data: {e}")
            self.cost_entries = []
    
    def export_cost_report(self, output_file: str = None) -> str:
        """Export detailed cost report"""
        
        if output_file is None:
            output_file = f"venice_ai_cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Generate comprehensive report
            report = {
                'report_generated': datetime.now().isoformat(),
                'summary': {
                    'total_requests': self.total_requests,
                    'total_savings': self.total_savings,
                    'total_entries': len(self.cost_entries)
                },
                'daily_summary': self.get_daily_summary().to_dict() if hasattr(self.get_daily_summary(), 'to_dict') else self._summary_to_dict(self.get_daily_summary()),
                'weekly_summary': self._summary_to_dict(self.get_weekly_summary()),
                'monthly_summary': self._summary_to_dict(self.get_monthly_summary()),
                'budget_status': {
                    'daily_budgets': self.daily_budgets,
                    'monthly_budget': self.monthly_budget,
                    'current_month_usage': self.get_monthly_summary().total_venice_cost
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Cost report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export cost report: {e}")
            return ""
    
    def _summary_to_dict(self, summary: CostSummary) -> Dict:
        """Convert CostSummary to dictionary"""
        return {
            'period_start': summary.period_start.isoformat(),
            'period_end': summary.period_end.isoformat(),
            'total_requests': summary.total_requests,
            'total_venice_cost': summary.total_venice_cost,
            'total_openai_equivalent': summary.total_openai_equivalent,
            'total_savings': summary.total_savings,
            'savings_percentage': summary.savings_percentage,
            'feature_breakdown': summary.feature_breakdown,
            'model_breakdown': summary.model_breakdown,
            'daily_costs': summary.daily_costs
        }
    
    def get_roi_analysis(self) -> Dict:
        """Get ROI analysis of hybrid AI integration"""
        
        monthly_summary = self.get_monthly_summary()
        
        # Calculate monthly ROI
        monthly_savings = monthly_summary.total_savings
        monthly_cost = monthly_summary.total_venice_cost
        
        # Estimate annual projections
        annual_savings = monthly_savings * 12
        annual_cost = monthly_cost * 12
        
        # Calculate payback period (immediate since we're saving money)
        payback_months = 0  # Immediate savings
        
        return {
            'monthly_savings': monthly_savings,
            'monthly_cost': monthly_cost,
            'monthly_roi_percentage': (monthly_savings / monthly_cost * 100) if monthly_cost > 0 else 0,
            'annual_projected_savings': annual_savings,
            'annual_projected_cost': annual_cost,
            'payback_period_months': payback_months,
            'cost_reduction_percentage': monthly_summary.savings_percentage,
            'break_even_analysis': {
                'already_profitable': True,
                'monthly_profit': monthly_savings,
                'annual_profit': annual_savings
            }
        }
    
    def get_hybrid_analytics(self) -> Dict:
        """Get hybrid AI analytics (Venice + OpenAI)"""
        
        # Separate Venice and OpenAI entries
        venice_entries = [e for e in self.cost_entries if not e.model_used.startswith('openai_')]
        openai_entries = [e for e in self.cost_entries if e.model_used.startswith('openai_')]
        
        # Calculate Venice stats
        venice_cost = sum(e.venice_cost for e in venice_entries)
        venice_requests = len(venice_entries)
        venice_savings = sum(e.savings for e in venice_entries)
        
        # Calculate OpenAI stats
        openai_cost = sum(e.venice_cost for e in openai_entries)  # venice_cost field contains actual OpenAI cost
        openai_requests = len(openai_entries)
        
        # Calculate hybrid efficiency
        total_requests = venice_requests + openai_requests
        total_cost = venice_cost + openai_cost
        
        # What would all-OpenAI cost
        all_openai_cost = venice_cost * 25 + openai_cost  # Venice is ~25x cheaper
        hybrid_savings = all_openai_cost - total_cost
        
        return {
            'hybrid_summary': {
                'total_requests': total_requests,
                'total_cost': round(total_cost, 4),
                'all_openai_equivalent': round(all_openai_cost, 4),
                'hybrid_savings': round(hybrid_savings, 4),
                'hybrid_savings_percentage': round((hybrid_savings / all_openai_cost * 100) if all_openai_cost > 0 else 0, 1)
            },
            'venice_ai': {
                'requests': venice_requests,
                'cost': round(venice_cost, 4),
                'percentage_of_requests': round((venice_requests / max(total_requests, 1)) * 100, 1),
                'percentage_of_cost': round((venice_cost / max(total_cost, 1)) * 100, 1),
                'avg_cost_per_request': round(venice_cost / max(venice_requests, 1), 4),
                'savings_vs_openai': round(venice_savings, 4)
            },
            'openai': {
                'requests': openai_requests,
                'cost': round(openai_cost, 4),
                'percentage_of_requests': round((openai_requests / max(total_requests, 1)) * 100, 1),
                'percentage_of_cost': round((openai_cost / max(total_cost, 1)) * 100, 1),
                'avg_cost_per_request': round(openai_cost / max(openai_requests, 1), 4)
            },
            'efficiency_metrics': {
                'cost_per_request_hybrid': round(total_cost / max(total_requests, 1), 4),
                'cost_per_request_all_openai': round(all_openai_cost / max(total_requests, 1), 4),
                'efficiency_improvement': round(((all_openai_cost - total_cost) / max(all_openai_cost, 1)) * 100, 1)
            }
        }
