#!/usr/bin/env python3
"""
Weekly Retraining Script
=========================

Full model retrain with 500+ new matches.
Cross-validation and performance metrics.
Model versioning and rollback capability.

This is part of Layer 5: Continuous Learning.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.xgboost_trainer import XGBoostTrainer
from src.ml.lightgbm_trainer import LightGBMTrainer
from src.ml.data_collector import MatchResultsDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run weekly retraining"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Weekly Model Retraining')
    parser.add_argument('--limit', type=int, help='Limit training samples')
    parser.add_argument('--xgboost-only', action='store_true', help='Only retrain XGBoost')
    parser.add_argument('--lightgbm-only', action='store_true', help='Only retrain LightGBM')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("🚀 WEEKLY MODEL RETRAINING")
    logger.info("=" * 80)
    logger.info(f"📅 Date: {datetime.now().isoformat()}")
    
    # Check database
    db = MatchResultsDB()
    total_matches = db.count_matches()
    total_results = db.count_results()
    
    logger.info(f"📊 Database Status:")
    logger.info(f"   Total Matches: {total_matches}")
    logger.info(f"   Total Results: {total_results}")
    logger.info(f"   Coverage: {total_results / max(total_matches, 1):.1%}")
    
    if total_results < 50:
        logger.warning(f"⚠️ Insufficient training data: {total_results} results (need at least 50)")
        logger.info("💡 Collect more match results before retraining")
        return
    
    results = {}
    
    # Retrain XGBoost
    if not args.lightgbm_only:
        logger.info("\n" + "=" * 80)
        logger.info("🤖 RETRAINING XGBOOST MODEL")
        logger.info("=" * 80)
        
        xgboost_trainer = XGBoostTrainer()
        xgboost_result = xgboost_trainer.train(limit=args.limit)
        
        if xgboost_result.get('success'):
            xgboost_trainer.save_model()
            results['xgboost'] = xgboost_result
            logger.info("✅ XGBoost model retrained and saved")
        else:
            logger.error(f"❌ XGBoost training failed: {xgboost_result.get('error')}")
            results['xgboost'] = {'success': False, 'error': xgboost_result.get('error')}
    
    # Retrain LightGBM
    if not args.xgboost_only:
        logger.info("\n" + "=" * 80)
        logger.info("⚡ RETRAINING LIGHTGBM MODEL")
        logger.info("=" * 80)
        
        lightgbm_trainer = LightGBMTrainer()
        lightgbm_result = lightgbm_trainer.train(limit=args.limit)
        
        if lightgbm_result.get('success'):
            lightgbm_trainer.save_model()
            results['lightgbm'] = lightgbm_result
            logger.info("✅ LightGBM model retrained and saved")
        else:
            logger.error(f"❌ LightGBM training failed: {lightgbm_result.get('error')}")
            results['lightgbm'] = {'success': False, 'error': lightgbm_result.get('error')}
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ WEEKLY RETRAINING COMPLETED")
    logger.info("=" * 80)
    
    for model_name, result in results.items():
        if result.get('success'):
            logger.info(f"✅ {model_name.upper()}:")
            logger.info(f"   Test Accuracy: {result.get('test_accuracy', 0):.3f}")
            logger.info(f"   Test AUC: {result.get('test_auc', 0):.3f}")
        else:
            logger.error(f"❌ {model_name.upper()}: {result.get('error')}")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

