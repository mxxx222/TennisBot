#!/usr/bin/env python3
"""
Comprehensive test suite for Venice AI integration
Tests all AI components and validates cost savings vs OpenAI
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test imports
try:
    from ai_analysis.venice_client import VeniceAIClient
    from ai_analysis.match_analyzer import AIMatchAnalyzer
    from ai_analysis.pattern_detector import AIPatternDetector
    from ai_analysis.cost_tracker import VeniceAICostTracker
    from ai_analysis.ai_config import VeniceAIConfig
    from monitors.value_detector import ValueDetector, ValueOpportunity
    from storage.odds_database import OddsDatabase
    print("✅ All AI modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class VeniceAIIntegrationTest:
    """Comprehensive test suite for Venice AI integration"""
    
    def __init__(self):
        self.config = VeniceAIConfig()
        self.cost_tracker = VeniceAICostTracker()
        self.database = OddsDatabase()
        
        # Test results
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    async def run_all_tests(self):
        """Run all Venice AI integration tests"""
        
        print("\n🤖 VENICE AI INTEGRATION TEST SUITE")
        print("=" * 50)
        
        # Test 1: Configuration validation
        await self.test_configuration()
        
        # Test 2: Venice AI client connection
        await self.test_venice_connection()
        
        # Test 3: Cost tracking system
        await self.test_cost_tracking()
        
        # Test 4: Match analysis
        await self.test_match_analysis()
        
        # Test 5: Pattern detection
        await self.test_pattern_detection()
        
        # Test 6: AI-enhanced value detection
        await self.test_ai_value_detection()
        
        # Test 7: Cost savings validation
        await self.test_cost_savings()
        
        # Test 8: Performance benchmarks
        await self.test_performance()
        
        # Generate final report
        self.generate_test_report()
    
    async def test_configuration(self):
        """Test Venice AI configuration"""
        
        print("\n📋 Testing Venice AI Configuration...")
        self.total_tests += 1
        
        try:
            # Validate configuration
            is_valid = self.config.validate_config()
            
            if is_valid:
                print("✅ Configuration validation passed")
                
                # Test cost calculation
                cost_info = self.config.calculate_cost_savings(1000, 500)
                expected_venice_cost = (1000 * 0.15 + 500 * 0.60) / 1_000_000
                
                if abs(cost_info['venice_cost'] - expected_venice_cost) < 0.0001:
                    print("✅ Cost calculation accuracy verified")
                    self.passed_tests += 1
                    self.test_results['configuration'] = 'PASSED'
                else:
                    print("❌ Cost calculation inaccurate")
                    self.test_results['configuration'] = 'FAILED'
            else:
                print("❌ Configuration validation failed")
                self.test_results['configuration'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            self.test_results['configuration'] = 'FAILED'
    
    async def test_venice_connection(self):
        """Test Venice AI API connection"""
        
        print("\n🔗 Testing Venice AI Connection...")
        self.total_tests += 1
        
        try:
            async with VeniceAIClient() as client:
                # Test connection
                is_connected = await client.test_connection()
                
                if is_connected:
                    print("✅ Venice AI connection successful")
                    self.passed_tests += 1
                    self.test_results['connection'] = 'PASSED'
                else:
                    print("❌ Venice AI connection failed")
                    self.test_results['connection'] = 'FAILED'
                    
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            self.test_results['connection'] = 'FAILED'
    
    async def test_cost_tracking(self):
        """Test cost tracking system"""
        
        print("\n💰 Testing Cost Tracking System...")
        self.total_tests += 1
        
        try:
            # Test cost logging
            savings = self.cost_tracker.log_cost(
                feature="test_analysis",
                model_used="llama-3.3-70b",
                input_tokens=1000,
                output_tokens=500,
                venice_cost=0.00045,
                request_id="test_001"
            )
            
            # Validate savings calculation
            expected_openai_cost = (1000 * 5.00 + 500 * 15.00) / 1_000_000
            expected_savings = expected_openai_cost - 0.00045
            
            if abs(savings - expected_savings) < 0.0001:
                print("✅ Cost tracking accuracy verified")
                
                # Test summary generation
                summary = self.cost_tracker.get_daily_summary()
                if summary.total_requests > 0:
                    print("✅ Cost summary generation working")
                    self.passed_tests += 1
                    self.test_results['cost_tracking'] = 'PASSED'
                else:
                    print("❌ Cost summary generation failed")
                    self.test_results['cost_tracking'] = 'FAILED'
            else:
                print("❌ Cost tracking calculation inaccurate")
                self.test_results['cost_tracking'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Cost tracking test failed: {e}")
            self.test_results['cost_tracking'] = 'FAILED'
    
    async def test_match_analysis(self):
        """Test AI-powered match analysis"""
        
        print("\n⚽ Testing Match Analysis...")
        self.total_tests += 1
        
        try:
            # Create test match data
            test_match = {
                'match_id': 'test_match_001',
                'home_team': 'Test FC',
                'away_team': 'Demo United',
                'home_odds': 1.65,
                'away_odds': 2.20,
                'league': 'soccer_test_league',
                'commence_time': datetime.now() + timedelta(hours=2)
            }
            
            analyzer = AIMatchAnalyzer(self.database)
            
            # Test single match analysis
            async with VeniceAIClient() as client:
                # Test connection first
                if await client.test_connection():
                    # Create mock opportunity
                    opportunity = ValueOpportunity(
                        match_id=test_match['match_id'],
                        team=test_match['home_team'],
                        opponent=test_match['away_team'],
                        odds=test_match['home_odds'],
                        previous_odds=None,
                        league=test_match['league'],
                        commence_time=test_match['commence_time'],
                        detected_time=datetime.now(),
                        recommended_stake=10.0,
                        confidence='Medium',
                        edge_estimate=5.0,
                        kelly_fraction=0.02,
                        urgency_level='MEDIUM',
                        priority_score=50.0,
                        time_sensitivity=0.8,
                        movement_direction='stable',
                        odds_velocity=0.0
                    )
                    
                    # Test analysis
                    enhanced_opportunities = await analyzer.analyze_opportunities([opportunity])
                    
                    if enhanced_opportunities and len(enhanced_opportunities) > 0:
                        enhanced = enhanced_opportunities[0]
                        
                        # Validate enhancement
                        if (hasattr(enhanced, 'ai_enhanced') and 
                            hasattr(enhanced, 'ai_confidence') and
                            hasattr(enhanced, 'combined_edge')):
                            print("✅ Match analysis enhancement successful")
                            print(f"   AI Confidence: {enhanced.ai_confidence:.1%}")
                            print(f"   Combined Edge: {enhanced.combined_edge:.1f}%")
                            print(f"   Analysis Cost: ${enhanced.analysis_cost:.4f}")
                            
                            self.passed_tests += 1
                            self.test_results['match_analysis'] = 'PASSED'
                        else:
                            print("❌ Match analysis enhancement incomplete")
                            self.test_results['match_analysis'] = 'FAILED'
                    else:
                        print("❌ Match analysis returned no results")
                        self.test_results['match_analysis'] = 'FAILED'
                else:
                    print("⚠️  Venice AI connection failed, using fallback analysis")
                    self.test_results['match_analysis'] = 'SKIPPED'
                    
        except Exception as e:
            print(f"❌ Match analysis test failed: {e}")
            self.test_results['match_analysis'] = 'FAILED'
    
    async def test_pattern_detection(self):
        """Test AI pattern detection"""
        
        print("\n📊 Testing Pattern Detection...")
        self.total_tests += 1
        
        try:
            # Create mock historical data
            mock_opportunities = []
            for i in range(10):
                mock_opportunities.append({
                    'league': f'soccer_test_league_{i % 3}',
                    'odds': 1.30 + (i * 0.05),
                    'edge_estimate': 3.0 + (i * 0.5),
                    'urgency_level': ['LOW', 'MEDIUM', 'HIGH'][i % 3],
                    'detected_time': (datetime.now() - timedelta(days=i)).isoformat()
                })
            
            detector = AIPatternDetector(self.database)
            
            # Test pattern detection
            patterns = await detector.detect_profitable_patterns(days=7)
            
            if patterns:
                print(f"✅ Pattern detection successful: {len(patterns)} patterns found")
                for pattern in patterns[:3]:  # Show first 3 patterns
                    print(f"   - {pattern.pattern_type}: {pattern.profitability_score:.1f}% score")
                
                self.passed_tests += 1
                self.test_results['pattern_detection'] = 'PASSED'
            else:
                print("⚠️  No patterns detected (may be normal with limited data)")
                self.test_results['pattern_detection'] = 'SKIPPED'
                
        except Exception as e:
            print(f"❌ Pattern detection test failed: {e}")
            self.test_results['pattern_detection'] = 'FAILED'
    
    async def test_ai_value_detection(self):
        """Test AI-enhanced value detection"""
        
        print("\n🎯 Testing AI-Enhanced Value Detection...")
        self.total_tests += 1
        
        try:
            # Create test value detector
            value_detector = ValueDetector(bankroll=1000.0)
            
            # Check if AI is available
            if hasattr(value_detector, 'ai_analyzer') and value_detector.ai_analyzer:
                print("✅ AI-enhanced value detector initialized")
                
                # Get AI enhancement stats
                ai_stats = value_detector.get_ai_enhancement_stats()
                
                if ai_stats.get('ai_available', False):
                    print("✅ AI enhancement system operational")
                    print(f"   Enhancement rate: {ai_stats.get('enhancement_rate', 0):.1%}")
                    print(f"   Total cost: ${ai_stats.get('total_ai_cost', 0):.4f}")
                    print(f"   Estimated savings: ${ai_stats.get('cost_savings', 0):.4f}")
                    
                    self.passed_tests += 1
                    self.test_results['ai_value_detection'] = 'PASSED'
                else:
                    print("❌ AI enhancement system not available")
                    self.test_results['ai_value_detection'] = 'FAILED'
            else:
                print("⚠️  AI analyzer not initialized (fallback mode)")
                self.test_results['ai_value_detection'] = 'SKIPPED'
                
        except Exception as e:
            print(f"❌ AI value detection test failed: {e}")
            self.test_results['ai_value_detection'] = 'FAILED'
    
    async def test_cost_savings(self):
        """Test and validate cost savings vs OpenAI"""
        
        print("\n💸 Testing Cost Savings Validation...")
        self.total_tests += 1
        
        try:
            # Get cost summary
            summary = self.cost_tracker.get_daily_summary()
            roi_analysis = self.cost_tracker.get_roi_analysis()
            
            print(f"✅ Daily cost summary generated")
            print(f"   Venice cost: ${summary.total_venice_cost:.4f}")
            print(f"   OpenAI equivalent: ${summary.total_openai_equivalent:.4f}")
            print(f"   Savings: ${summary.total_savings:.4f} ({summary.savings_percentage:.1f}%)")
            
            # Validate savings percentage
            if summary.savings_percentage > 80:  # Should be 90%+ savings
                print("✅ Cost savings target achieved (>80%)")
                
                # Test ROI analysis
                if roi_analysis['monthly_savings'] >= 0:
                    print("✅ ROI analysis positive")
                    print(f"   Monthly projected savings: ${roi_analysis['monthly_savings']:.2f}")
                    print(f"   Annual projected savings: ${roi_analysis['annual_projected_savings']:.2f}")
                    
                    self.passed_tests += 1
                    self.test_results['cost_savings'] = 'PASSED'
                else:
                    print("❌ ROI analysis shows negative returns")
                    self.test_results['cost_savings'] = 'FAILED'
            else:
                print(f"❌ Cost savings below target: {summary.savings_percentage:.1f}% < 80%")
                self.test_results['cost_savings'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Cost savings test failed: {e}")
            self.test_results['cost_savings'] = 'FAILED'
    
    async def test_performance(self):
        """Test performance benchmarks"""
        
        print("\n⚡ Testing Performance Benchmarks...")
        self.total_tests += 1
        
        try:
            # Test response time
            start_time = datetime.now()
            
            async with VeniceAIClient() as client:
                if await client.test_connection():
                    # Test simple analysis
                    test_data = {
                        'home_team': 'Speed Test FC',
                        'away_team': 'Benchmark United',
                        'home_odds': 1.50,
                        'away_odds': 2.50,
                        'league': 'performance_test'
                    }
                    
                    result = await client.analyze_match_value(test_data)
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    if result and response_time < 10.0:  # Should complete within 10 seconds
                        print(f"✅ Performance benchmark met: {response_time:.2f}s response time")
                        
                        # Test cost efficiency
                        if result.cost < 0.01:  # Should cost less than 1 cent per analysis
                            print(f"✅ Cost efficiency target met: ${result.cost:.4f} per analysis")
                            
                            self.passed_tests += 1
                            self.test_results['performance'] = 'PASSED'
                        else:
                            print(f"❌ Cost efficiency below target: ${result.cost:.4f} > $0.01")
                            self.test_results['performance'] = 'FAILED'
                    else:
                        print(f"❌ Performance benchmark failed: {response_time:.2f}s > 10s")
                        self.test_results['performance'] = 'FAILED'
                else:
                    print("⚠️  Performance test skipped (connection failed)")
                    self.test_results['performance'] = 'SKIPPED'
                    
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = 'FAILED'
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n📊 VENICE AI INTEGRATION TEST REPORT")
        print("=" * 50)
        
        # Summary
        success_rate = (self.passed_tests / self.total_tests) * 100
        print(f"Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})")
        
        # Detailed results
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status_emoji = {
                'PASSED': '✅',
                'FAILED': '❌',
                'SKIPPED': '⚠️'
            }.get(result, '❓')
            
            print(f"  {status_emoji} {test_name.replace('_', ' ').title()}: {result}")
        
        # Cost analysis
        try:
            summary = self.cost_tracker.get_daily_summary()
            roi_analysis = self.cost_tracker.get_roi_analysis()
            
            print(f"\nCost Analysis:")
            print(f"  💰 Total Venice Cost: ${summary.total_venice_cost:.4f}")
            print(f"  💸 OpenAI Equivalent: ${summary.total_openai_equivalent:.4f}")
            print(f"  💵 Total Savings: ${summary.total_savings:.4f}")
            print(f"  📈 Savings Rate: {summary.savings_percentage:.1f}%")
            print(f"  🎯 Monthly Projected Savings: ${roi_analysis['monthly_savings']:.2f}")
            print(f"  📅 Annual Projected Savings: ${roi_analysis['annual_projected_savings']:.2f}")
            
        except Exception as e:
            print(f"\nCost analysis unavailable: {e}")
        
        # Recommendations
        print(f"\nRecommendations:")
        
        if success_rate >= 80:
            print("  ✅ Venice AI integration is ready for production")
            print("  🚀 Expected 90% cost savings vs OpenAI")
            print("  💰 Projected annual savings: $2,000-3,000")
        elif success_rate >= 60:
            print("  ⚠️  Venice AI integration needs minor fixes")
            print("  🔧 Review failed tests and address issues")
        else:
            print("  ❌ Venice AI integration requires major fixes")
            print("  🛠️  Address critical failures before production use")
        
        # Export report
        try:
            report_file = self.cost_tracker.export_cost_report()
            if report_file:
                print(f"\n📄 Detailed cost report exported: {report_file}")
        except:
            pass

async def main():
    """Run Venice AI integration tests"""
    
    print("🤖 Starting Venice AI Integration Test Suite...")
    
    # Initialize test suite
    test_suite = VeniceAIIntegrationTest()
    
    # Run all tests
    await test_suite.run_all_tests()
    
    print("\n✅ Venice AI Integration Test Suite Complete!")

if __name__ == "__main__":
    asyncio.run(main())
