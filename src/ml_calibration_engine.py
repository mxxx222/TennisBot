#!/usr/bin/env python3
"""
📊 ML CALIBRATION ENGINE
========================
Analyzes prediction accuracy vs confidence levels to identify calibration issues
and generate statistics for ML model improvement.

Author: TennisBot Calibration System
Version: 1.0.0
"""

import logging
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

class CalibrationEngine:
    """Analyzes calibration data and generates improvement metrics"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize calibration engine
        
        Args:
            db_path: Path to virtual bets database
        """
        if db_path is None:
            data_dir = Path(__file__).parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / 'virtual_bets.db')
        
        self.db_path = db_path
        logger.info("✅ CalibrationEngine initialized")
    
    def analyze_calibration(
        self,
        min_samples: int = 10,
        confidence_buckets: List[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Analyze calibration data and generate statistics
        
        Args:
            min_samples: Minimum samples per bucket for analysis
            confidence_buckets: Custom confidence buckets [(min, max), ...]
            
        Returns:
            Dictionary with calibration analysis results
        """
        try:
            # Get calibration data
            calibration_data = self._get_calibration_data()
            
            if len(calibration_data) < min_samples:
                logger.warning(f"⚠️ Insufficient calibration data: {len(calibration_data)} < {min_samples}")
                return {
                    'status': 'insufficient_data',
                    'total_samples': len(calibration_data),
                    'min_required': min_samples
                }
            
            # Default confidence buckets if not provided
            if confidence_buckets is None:
                confidence_buckets = [
                    (0.50, 0.60),
                    (0.60, 0.65),
                    (0.65, 0.70),
                    (0.70, 0.75),
                    (0.75, 0.80),
                    (0.80, 0.85),
                    (0.85, 0.90),
                    (0.90, 1.00)
                ]
            
            # Analyze by confidence bucket
            bucket_analysis = self._analyze_confidence_buckets(
                calibration_data,
                confidence_buckets,
                min_samples
            )
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(calibration_data)
            
            # Calculate Brier score
            brier_score = self._calculate_brier_score(calibration_data)
            
            # Identify calibration issues
            calibration_issues = self._identify_calibration_issues(bucket_analysis)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                bucket_analysis,
                overall_metrics,
                calibration_issues
            )
            
            return {
                'status': 'success',
                'total_samples': len(calibration_data),
                'analysis_date': datetime.now().isoformat(),
                'confidence_buckets': bucket_analysis,
                'overall_metrics': overall_metrics,
                'brier_score': brier_score,
                'calibration_issues': calibration_issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing calibration: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_calibration_data(self) -> List[Dict[str, Any]]:
        """Get calibration data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        predicted_confidence,
                        actual_outcome,
                        predicted_outcome,
                        accuracy,
                        calibration_error,
                        confidence_bucket,
                        surface
                    FROM calibration_data
                    ORDER BY created_at DESC
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error getting calibration data: {e}")
            return []
    
    def _analyze_confidence_buckets(
        self,
        data: List[Dict[str, Any]],
        buckets: List[Tuple[float, float]],
        min_samples: int
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze calibration by confidence buckets"""
        bucket_results = {}
        
        for min_conf, max_conf in buckets:
            bucket_key = f"{min_conf:.2f}-{max_conf:.2f}"
            
            # Filter data for this bucket
            bucket_data = [
                d for d in data
                if min_conf <= d['predicted_confidence'] < max_conf
            ]
            
            if len(bucket_data) < min_samples:
                bucket_results[bucket_key] = {
                    'samples': len(bucket_data),
                    'status': 'insufficient_data'
                }
                continue
            
            # Calculate metrics
            accuracies = [d['accuracy'] for d in bucket_data]
            confidences = [d['predicted_confidence'] for d in bucket_data]
            errors = [d['calibration_error'] for d in bucket_data]
            
            actual_win_rate = np.mean(accuracies)
            avg_confidence = np.mean(confidences)
            calibration_error = np.mean(errors)
            
            # Expected vs actual
            expected_win_rate = avg_confidence
            calibration_gap = abs(expected_win_rate - actual_win_rate)
            
            bucket_results[bucket_key] = {
                'samples': len(bucket_data),
                'avg_confidence': round(avg_confidence, 4),
                'actual_win_rate': round(actual_win_rate, 4),
                'expected_win_rate': round(expected_win_rate, 4),
                'calibration_error': round(calibration_error, 4),
                'calibration_gap': round(calibration_gap, 4),
                'is_calibrated': calibration_gap < 0.05,  # Within 5%
                'status': 'analyzed'
            }
        
        return bucket_results
    
    def _calculate_overall_metrics(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate overall calibration metrics"""
        if not data:
            return {}
        
        accuracies = [d['accuracy'] for d in data]
        confidences = [d['predicted_confidence'] for d in data]
        errors = [d['calibration_error'] for d in data]
        
        overall_accuracy = np.mean(accuracies)
        avg_confidence = np.mean(confidences)
        avg_calibration_error = np.mean(errors)
        
        # Expected accuracy (average confidence)
        expected_accuracy = avg_confidence
        
        # Calibration gap
        calibration_gap = abs(expected_accuracy - overall_accuracy)
        
        # Reliability (how well calibrated)
        reliability = 1.0 - min(calibration_gap, 1.0)
        
        return {
            'overall_accuracy': round(overall_accuracy, 4),
            'avg_confidence': round(avg_confidence, 4),
            'expected_accuracy': round(expected_accuracy, 4),
            'calibration_gap': round(calibration_gap, 4),
            'avg_calibration_error': round(avg_calibration_error, 4),
            'reliability': round(reliability, 4),
            'total_samples': len(data)
        }
    
    def _calculate_brier_score(
        self,
        data: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate Brier score (lower is better, 0 = perfect)
        Brier = mean((predicted_prob - actual_outcome)^2)
        """
        if not data:
            return 1.0
        
        brier_scores = []
        for d in data:
            predicted_prob = d['predicted_confidence']
            actual_outcome = d['accuracy']  # 1 if correct, 0 if wrong
            brier = (predicted_prob - actual_outcome) ** 2
            brier_scores.append(brier)
        
        return round(np.mean(brier_scores), 4)
    
    def _identify_calibration_issues(
        self,
        bucket_analysis: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify specific calibration issues"""
        issues = []
        
        for bucket_key, bucket_data in bucket_analysis.items():
            if bucket_data.get('status') != 'analyzed':
                continue
            
            gap = bucket_data.get('calibration_gap', 0)
            is_calibrated = bucket_data.get('is_calibrated', True)
            
            if not is_calibrated:
                issue_type = 'overconfident' if bucket_data['avg_confidence'] > bucket_data['actual_win_rate'] else 'underconfident'
                
                issues.append({
                    'confidence_bucket': bucket_key,
                    'issue_type': issue_type,
                    'calibration_gap': gap,
                    'avg_confidence': bucket_data['avg_confidence'],
                    'actual_win_rate': bucket_data['actual_win_rate'],
                    'severity': 'high' if gap > 0.10 else 'medium' if gap > 0.05 else 'low'
                })
        
        return issues
    
    def _generate_recommendations(
        self,
        bucket_analysis: Dict[str, Dict[str, Any]],
        overall_metrics: Dict[str, float],
        calibration_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for model improvement"""
        recommendations = []
        
        # Overall calibration gap
        overall_gap = overall_metrics.get('calibration_gap', 0)
        if overall_gap > 0.10:
            recommendations.append(
                f"High overall calibration gap ({overall_gap:.2%}). "
                "Consider retraining models with calibration-aware loss functions."
            )
        elif overall_gap > 0.05:
            recommendations.append(
                f"Moderate calibration gap ({overall_gap:.2%}). "
                "Consider adjusting confidence thresholds or model weights."
            )
        
        # Bucket-specific issues
        high_severity_issues = [i for i in calibration_issues if i['severity'] == 'high']
        if high_severity_issues:
            recommendations.append(
                f"Found {len(high_severity_issues)} high-severity calibration issues. "
                "Focus model improvements on these confidence ranges."
            )
        
        # Overconfident predictions
        overconfident = [i for i in calibration_issues if i['issue_type'] == 'overconfident']
        if overconfident:
            recommendations.append(
                f"Model is overconfident in {len(overconfident)} confidence buckets. "
                "Consider reducing confidence scores or using temperature scaling."
            )
        
        # Underconfident predictions
        underconfident = [i for i in calibration_issues if i['issue_type'] == 'underconfident']
        if underconfident:
            recommendations.append(
                f"Model is underconfident in {len(underconfident)} confidence buckets. "
                "Consider increasing confidence scores or adjusting model calibration."
            )
        
        # Brier score
        brier = overall_metrics.get('brier_score', 1.0)
        if brier > 0.25:
            recommendations.append(
                f"High Brier score ({brier:.4f}). Model predictions need significant improvement."
            )
        elif brier > 0.20:
            recommendations.append(
                f"Moderate Brier score ({brier:.4f}). Model could benefit from calibration improvements."
            )
        
        if not recommendations:
            recommendations.append(
                "Model is well-calibrated. Continue monitoring for drift."
            )
        
        return recommendations
    
    def get_calibration_by_surface(self) -> Dict[str, Dict[str, Any]]:
        """Analyze calibration by court surface"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        surface,
                        COUNT(*) as samples,
                        AVG(predicted_confidence) as avg_confidence,
                        AVG(accuracy) as actual_win_rate,
                        AVG(calibration_error) as avg_error
                    FROM calibration_data
                    WHERE surface IS NOT NULL
                    GROUP BY surface
                ''')
                
                results = {}
                for row in cursor.fetchall():
                    surface = row['surface'] or 'unknown'
                    results[surface] = {
                        'samples': row['samples'],
                        'avg_confidence': round(row['avg_confidence'], 4),
                        'actual_win_rate': round(row['actual_win_rate'], 4),
                        'calibration_gap': round(
                            abs(row['avg_confidence'] - row['actual_win_rate']), 4
                        ),
                        'avg_error': round(row['avg_error'], 4)
                    }
                
                return results
        except Exception as e:
            logger.error(f"❌ Error analyzing by surface: {e}")
            return {}
    
    def export_calibration_report(
        self,
        output_path: str = None
    ) -> str:
        """Export comprehensive calibration report"""
        if output_path is None:
            data_dir = Path(__file__).parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(data_dir / f'calibration_report_{timestamp}.json')
        
        analysis = self.analyze_calibration()
        surface_analysis = self.get_calibration_by_surface()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'calibration_analysis': analysis,
            'surface_analysis': surface_analysis
        }
        
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Calibration report exported to {output_path}")
        return output_path

