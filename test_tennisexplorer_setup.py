#!/usr/bin/env python3
"""
Quick validation test for TennisExplorer implementation
Run this after setup to verify everything works
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all module imports"""
    print("🧪 Testing imports...")
    
    tests = [
        ("Scraper", "src.scrapers.tennisexplorer_scraper", "TennisExplorerScraper"),
        ("Pipeline", "src.pipelines.tennisexplorer_pipeline", "TennisExplorerPipeline"),
        ("ELO Enricher", "src.enrichment.elo_enricher", "ELOEnricher"),
        ("Stats Enricher", "src.enrichment.stats_enricher", "StatsEnricher"),
        ("Weather Enricher", "src.enrichment.weather_enricher", "WeatherEnricher"),
        ("Momentum Detector", "src.roi_detection.momentum_detector", "MomentumDetector"),
        ("Kelly Calculator", "src.roi_detection.kelly_calculator", "KellyCalculator"),
        ("Alert Manager", "src.alerts.roi_alert_manager", "ROIAlertManager"),
        ("Scheduler", "src.schedulers.tennisexplorer_scheduler", "TennisExplorerScheduler"),
        ("Monitor", "src.monitoring.tennisexplorer_monitor", "TennisExplorerMonitor"),
        ("Notion Updater", "src.notion.tennisexplorer_notion_updater", "TennisExplorerNotionUpdater"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module_path, class_name in tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def test_file_structure():
    """Test file structure"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "src/scrapers/tennisexplorer_scraper.py",
        "src/pipelines/tennisexplorer_pipeline.py",
        "src/database/tennisexplorer_schema.sql",
        "src/enrichment/elo_enricher.py",
        "src/enrichment/stats_enricher.py",
        "src/enrichment/weather_enricher.py",
        "src/enrichment/tiebreak_enricher.py",
        "src/enrichment/recovery_enricher.py",
        "src/roi_detection/momentum_detector.py",
        "src/roi_detection/fatigue_detector.py",
        "src/roi_detection/h2h_detector.py",
        "src/roi_detection/kelly_calculator.py",
        "src/notion/tennisexplorer_notion_updater.py",
        "src/alerts/roi_alert_manager.py",
        "src/schedulers/tennisexplorer_scheduler.py",
        "src/monitoring/tennisexplorer_monitor.py",
        "config/tennisexplorer_config.yaml",
        "scripts/setup_tennisexplorer_scraper.sh",
        "scripts/setup_tennisexplorer_cron.sh",
        "scripts/deploy_tennisexplorer.sh",
    ]
    
    passed = 0
    failed = 0
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
            passed += 1
        else:
            print(f"  ❌ {file_path} (missing)")
            failed += 1
    
    print(f"\n📊 Results: {passed} found, {failed} missing")
    return failed == 0

def test_basic_functionality():
    """Test basic functionality"""
    print("\n⚙️  Testing basic functionality...")
    
    try:
        from src.scrapers.tennisexplorer_scraper import TennisExplorerScraper
        scraper = TennisExplorerScraper({'request_delay': 2.0}, use_selenium=False)
        print("  ✅ Scraper initialization")
        
        from src.roi_detection.kelly_calculator import KellyCalculator
        kelly = KellyCalculator()
        result = kelly.calculate_stake(2.0, 0.55)
        if result['safe_kelly_pct'] > 0:
            print("  ✅ Kelly calculator")
        else:
            print("  ⚠️  Kelly calculator (edge too small)")
        
        from src.monitoring.tennisexplorer_monitor import TennisExplorerMonitor
        monitor = TennisExplorerMonitor()
        monitor.record_match_scraped()
        summary = monitor.get_metrics_summary()
        if summary['matches_scraped'] == 1:
            print("  ✅ Monitor")
        
        return True
    except Exception as e:
        print(f"  ❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TennisExplorer Implementation Validation")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("File Structure", test_file_structure()))
    results.append(("Basic Functionality", test_basic_functionality()))
    
    print("\n" + "=" * 60)
    print("📊 Final Results")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Ready for deployment.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    print("=" * 60)

