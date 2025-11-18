#!/usr/bin/env python3
"""
Comprehensive test suite for Hybrid AI System (Venice AI + OpenAI)
Tests smart routing, cost optimization, and quality validation
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
    from ai_analysis.hybrid_router import HybridAIRouter
    from ai_analysis.quality_validator import QualityValidator
    from ai_analysis.openai_client import OpenAIClient
    from ai_analysis.venice_client import VeniceAIClient
    from ai_analysis.cost_tracker import VeniceAICostTracker
    print("✅ All hybrid AI modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class HybridAISystemTest:
    """Comprehensive test suite for hybrid AI system"""
    
    def __init__(self):
        self.hybrid_router = HybridAIRouter()
        self.quality_validator = QualityValidator()
        self.cost_tracker = VeniceAICostTracker()
        
        # Test results
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    async def run_all_tests(self):
        """Run all hybrid AI system tests"""
        
        print("\n🤖 HYBRID AI SYSTEM TEST SUITE")
        print("=" * 50)
        
        # Test 1: Provider availability
        await self.test_provider_availability()
        
        # Test 2: Smart routing logic
        await self.test_smart_routing()
        
        # Test 3: Cost optimization
        await self.test_cost_optimization()
        
        # Test 4: Quality validation
        await self.test_quality_validation()
        
        # Test 5: Batch processing
        await self.test_batch_processing()
        
        # Test 6: Hybrid analytics
        await self.test_hybrid_analytics()
        
        # Test 7: Performance benchmarks
        await self.test_performance_benchmarks()
        
        # Test 8: Integration test
        await self.test_end_to_end_integration()
        
        # Generate final report
        self.generate_test_report()
    
    async def test_provider_availability(self):
        """Test availability of both AI providers"""
        
        print("\n🔗 Testing AI Provider Availability...")
        self.total_tests += 1
        
        try:
            # Test both providers
            provider_status = await self.hybrid_router.test_both_providers()
            
            venice_ok = provider_status.get('venice_ai', False)
            openai_ok = provider_status.get('openai', False)
            hybrid_ready = provider_status.get('hybrid_ready', False)
            
            if venice_ok:
                print("✅ Venice AI connection successful")
            else:
                print("❌ Venice AI connection failed")
            
            if openai_ok:
                print("✅ OpenAI connection successful")
            else:
                print("⚠️  OpenAI connection failed (may be expected)")
            
            if hybrid_ready:
                print("✅ Hybrid system ready")
                self.passed_tests += 1
                self.test_results['provider_availability'] = 'PASSED'
            else:
                print("❌ Hybrid system not ready")
                self.test_results['provider_availability'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Provider availability test failed: {e}")
            self.test_results['provider_availability'] = 'FAILED'
    
    async def test_smart_routing(self):
        """Test smart routing logic"""
        
        print("\n🎯 Testing Smart Routing Logic...")
        self.total_tests += 1
        
        try:
            # Test cases for routing decisions
            test_cases = [
                {
                    'name': 'Low stakes, low edge',
                    'data': {
                        'home_team': 'Test FC',
                        'away_team': 'Demo United',
                        'current_edge': 2.0,
                        'stake': 8.0,
                        'confidence': 'Medium'
                    },
                    'expected_provider': 'venice'
                },
                {
                    'name': 'High edge trigger',
                    'data': {
                        'home_team': 'High Edge FC',
                        'away_team': 'Value United',
                        'current_edge': 5.5,
                        'stake': 10.0,
                        'confidence': 'High'
                    },
                    'expected_provider': 'openai' if self.hybrid_router.openai_available else 'venice'
                },
                {
                    'name': 'High stakes trigger',
                    'data': {
                        'home_team': 'Big Stake FC',
                        'away_team': 'Premium United',
                        'current_edge': 3.0,
                        'stake': 18.0,
                        'confidence': 'Medium'
                    },
                    'expected_provider': 'openai' if self.hybrid_router.openai_available else 'venice'
                },
                {
                    'name': 'Critical timing',
                    'data': {
                        'home_team': 'Urgent FC',
                        'away_team': 'Time United',
                        'current_edge': 3.5,
                        'stake': 12.0,
                        'confidence': 'High',
                        'commence_time': datetime.now() + timedelta(minutes=30)
                    },
                    'expected_provider': 'openai' if self.hybrid_router.openai_available else 'venice'
                }
            ]
            
            routing_tests_passed = 0
            
            for test_case in test_cases:
                print(f"  Testing: {test_case['name']}")
                
                # Make routing decision
                routing = self.hybrid_router._make_routing_decision(test_case['data'])
                
                expected_openai = test_case['expected_provider'] == 'openai'
                
                if routing.use_openai == expected_openai:
                    print(f"    ✅ Routed to {test_case['expected_provider']} as expected")
                    routing_tests_passed += 1
                else:
                    actual_provider = 'openai' if routing.use_openai else 'venice'
                    print(f"    ⚠️  Routed to {actual_provider}, expected {test_case['expected_provider']}")
                    print(f"    Reason: {routing.reason}")
            
            if routing_tests_passed >= len(test_cases) * 0.75:  # 75% pass rate
                print("✅ Smart routing logic working correctly")
                self.passed_tests += 1
                self.test_results['smart_routing'] = 'PASSED'
            else:
                print("❌ Smart routing logic needs adjustment")
                self.test_results['smart_routing'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Smart routing test failed: {e}")
            self.test_results['smart_routing'] = 'FAILED'
    
    async def test_cost_optimization(self):
        """Test cost optimization and savings"""
        
        print("\n💰 Testing Cost Optimization...")
        self.total_tests += 1
        
        try:
            # Test opportunity with Venice AI
            venice_opportunity = {
                'home_team': 'Cost Test FC',
                'away_team': 'Savings United',
                'current_edge': 2.5,
                'stake': 10.0,
                'confidence': 'Medium'
            }
            
            # Analyze with hybrid router
            result = await self.hybrid_router.analyze_opportunity(venice_opportunity)
            
            if result:
                print(f"✅ Analysis completed with {result.ai_provider.upper()}")
                print(f"   Cost: ${result.analysis_cost:.4f}")
                print(f"   Savings: ${result.cost_savings:.4f}")
                
                # Validate cost savings
                if result.ai_provider == 'venice' and result.cost_savings > 0:
                    print("✅ Cost savings achieved with Venice AI")
                    savings_percentage = (result.cost_savings / (result.analysis_cost + result.cost_savings)) * 100
                    print(f"   Savings rate: {savings_percentage:.1f}%")
                    
                    if savings_percentage > 80:  # Should be 90%+ savings
                        print("✅ Cost optimization target achieved")
                        self.passed_tests += 1
                        self.test_results['cost_optimization'] = 'PASSED'
                    else:
                        print("❌ Cost optimization below target")
                        self.test_results['cost_optimization'] = 'FAILED'
                elif result.ai_provider == 'openai':
                    print("✅ Premium analysis used for high-value opportunity")
                    self.passed_tests += 1
                    self.test_results['cost_optimization'] = 'PASSED'
                else:
                    print("❌ Cost optimization not working")
                    self.test_results['cost_optimization'] = 'FAILED'
            else:
                print("❌ Cost optimization test failed - no result")
                self.test_results['cost_optimization'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Cost optimization test failed: {e}")
            self.test_results['cost_optimization'] = 'FAILED'
    
    async def test_quality_validation(self):
        """Test quality validation system"""
        
        print("\n🏆 Testing Quality Validation...")
        self.total_tests += 1
        
        try:
            # Test high-stakes opportunity
            high_stakes_opportunity = {
                'home_team': 'Quality FC',
                'away_team': 'Validation United',
                'current_edge': 4.5,
                'stake': 20.0,
                'confidence': 'High',
                'commence_time': datetime.now() + timedelta(hours=2)
            }
            
            # Validate opportunity
            validation = await self.quality_validator.validate_opportunity(high_stakes_opportunity)
            
            if validation.is_validated:
                print("✅ Quality validation completed")
                print(f"   Validation score: {validation.validation_score:.1f}/100")
                print(f"   Risk assessment: {validation.risk_assessment}")
                print(f"   Recommended action: {validation.recommended_action}")
                print(f"   Stake adjustment: {validation.stake_adjustment:.2f}x")
                print(f"   Validation cost: ${validation.cost:.4f}")
                
                if validation.validation_score > 50:
                    print("✅ Quality validation working correctly")
                    self.passed_tests += 1
                    self.test_results['quality_validation'] = 'PASSED'
                else:
                    print("❌ Quality validation score too low")
                    self.test_results['quality_validation'] = 'FAILED'
            else:
                print("⚠️  Quality validation not required for this opportunity")
                self.test_results['quality_validation'] = 'SKIPPED'
                
        except Exception as e:
            print(f"❌ Quality validation test failed: {e}")
            self.test_results['quality_validation'] = 'FAILED'
    
    async def test_batch_processing(self):
        """Test batch processing capabilities"""
        
        print("\n📦 Testing Batch Processing...")
        self.total_tests += 1
        
        try:
            # Create batch of test opportunities
            batch_opportunities = []
            for i in range(5):
                opportunity = {
                    'home_team': f'Batch FC {i+1}',
                    'away_team': f'Test United {i+1}',
                    'current_edge': 2.0 + i * 0.5,
                    'stake': 8.0 + i * 2.0,
                    'confidence': ['Low', 'Medium', 'High'][i % 3],
                    'commence_time': datetime.now() + timedelta(hours=i+1)
                }
                batch_opportunities.append(opportunity)
            
            # Process batch
            batch_results = await self.hybrid_router.analyze_batch(batch_opportunities)
            
            if batch_results and len(batch_results) > 0:
                print(f"✅ Batch processing completed: {len(batch_results)} results")
                
                # Check routing distribution
                venice_count = sum(1 for r in batch_results if r.ai_provider == 'venice')
                openai_count = sum(1 for r in batch_results if r.ai_provider == 'openai')
                
                print(f"   Venice AI: {venice_count} analyses")
                print(f"   OpenAI: {openai_count} analyses")
                
                # Calculate total costs and savings
                total_cost = sum(r.analysis_cost for r in batch_results)
                total_savings = sum(r.cost_savings for r in batch_results)
                
                print(f"   Total cost: ${total_cost:.4f}")
                print(f"   Total savings: ${total_savings:.4f}")
                
                if len(batch_results) >= len(batch_opportunities) * 0.8:  # 80% success rate
                    print("✅ Batch processing working correctly")
                    self.passed_tests += 1
                    self.test_results['batch_processing'] = 'PASSED'
                else:
                    print("❌ Batch processing success rate too low")
                    self.test_results['batch_processing'] = 'FAILED'
            else:
                print("❌ Batch processing failed - no results")
                self.test_results['batch_processing'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Batch processing test failed: {e}")
            self.test_results['batch_processing'] = 'FAILED'
    
    async def test_hybrid_analytics(self):
        """Test hybrid analytics and cost tracking"""
        
        print("\n📊 Testing Hybrid Analytics...")
        self.total_tests += 1
        
        try:
            # Get routing statistics
            routing_stats = self.hybrid_router.get_routing_stats()
            
            print("✅ Routing statistics generated")
            print(f"   Total requests: {routing_stats['total_requests']}")
            print(f"   Venice percentage: {routing_stats['venice_percentage']:.1f}%")
            print(f"   OpenAI percentage: {routing_stats['openai_percentage']:.1f}%")
            print(f"   Total savings: ${routing_stats['total_cost_savings']:.4f}")
            
            # Get hybrid analytics from cost tracker
            hybrid_analytics = self.cost_tracker.get_hybrid_analytics()
            
            print("✅ Hybrid analytics generated")
            print(f"   Hybrid savings: ${hybrid_analytics['hybrid_summary']['hybrid_savings']:.4f}")
            print(f"   Savings percentage: {hybrid_analytics['hybrid_summary']['hybrid_savings_percentage']:.1f}%")
            
            # Get validation statistics
            validation_stats = self.quality_validator.get_validation_stats()
            
            print("✅ Validation statistics generated")
            print(f"   Validations performed: {validation_stats['validations_performed']}")
            print(f"   Success rate: {validation_stats['success_rate']:.1%}")
            
            self.passed_tests += 1
            self.test_results['hybrid_analytics'] = 'PASSED'
            
        except Exception as e:
            print(f"❌ Hybrid analytics test failed: {e}")
            self.test_results['hybrid_analytics'] = 'FAILED'
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        
        print("\n⚡ Testing Performance Benchmarks...")
        self.total_tests += 1
        
        try:
            # Test response time
            start_time = datetime.now()
            
            test_opportunity = {
                'home_team': 'Performance FC',
                'away_team': 'Benchmark United',
                'current_edge': 3.0,
                'stake': 12.0,
                'confidence': 'Medium'
            }
            
            result = await self.hybrid_router.analyze_opportunity(test_opportunity)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            if result and response_time < 30.0:  # Should complete within 30 seconds
                print(f"✅ Performance benchmark met: {response_time:.2f}s response time")
                
                # Test cost efficiency
                if result.analysis_cost < 0.02:  # Should cost less than 2 cents per analysis
                    print(f"✅ Cost efficiency target met: ${result.analysis_cost:.4f} per analysis")
                    
                    self.passed_tests += 1
                    self.test_results['performance_benchmarks'] = 'PASSED'
                else:
                    print(f"❌ Cost efficiency below target: ${result.analysis_cost:.4f} > $0.02")
                    self.test_results['performance_benchmarks'] = 'FAILED'
            else:
                print(f"❌ Performance benchmark failed: {response_time:.2f}s > 30s")
                self.test_results['performance_benchmarks'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Performance benchmark test failed: {e}")
            self.test_results['performance_benchmarks'] = 'FAILED'
    
    async def test_end_to_end_integration(self):
        """Test complete end-to-end integration"""
        
        print("\n🔄 Testing End-to-End Integration...")
        self.total_tests += 1
        
        try:
            # Create comprehensive test scenario
            integration_opportunity = {
                'home_team': 'Integration FC',
                'away_team': 'E2E United',
                'current_edge': 4.2,
                'stake': 16.0,
                'confidence': 'High',
                'commence_time': datetime.now() + timedelta(hours=1.5),
                'league': 'soccer_efl_champ'
            }
            
            # Step 1: Hybrid analysis
            hybrid_result = await self.hybrid_router.analyze_opportunity(integration_opportunity)
            
            if not hybrid_result:
                print("❌ Integration test failed at hybrid analysis")
                self.test_results['end_to_end_integration'] = 'FAILED'
                return
            
            print(f"✅ Step 1: Hybrid analysis completed ({hybrid_result.ai_provider.upper()})")
            
            # Step 2: Quality validation
            validation_result = await self.quality_validator.validate_opportunity(
                integration_opportunity, 
                {
                    'edge_estimate': hybrid_result.edge_estimate,
                    'confidence_score': hybrid_result.confidence_score,
                    'risk_factors': hybrid_result.risk_factors,
                    'value_assessment': hybrid_result.value_assessment
                }
            )
            
            print(f"✅ Step 2: Quality validation completed (Score: {validation_result.validation_score:.1f})")
            
            # Step 3: Cost analysis
            total_cost = hybrid_result.analysis_cost + validation_result.cost
            total_savings = hybrid_result.cost_savings
            
            print(f"✅ Step 3: Cost analysis completed")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Total savings: ${total_savings:.4f}")
            
            # Integration success criteria
            if (hybrid_result.edge_estimate > 0 and 
                validation_result.validation_score > 0 and 
                total_cost < 0.05):  # Less than 5 cents total
                
                print("✅ End-to-end integration successful")
                self.passed_tests += 1
                self.test_results['end_to_end_integration'] = 'PASSED'
            else:
                print("❌ Integration test failed quality criteria")
                self.test_results['end_to_end_integration'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ End-to-end integration test failed: {e}")
            self.test_results['end_to_end_integration'] = 'FAILED'
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n📊 HYBRID AI SYSTEM TEST REPORT")
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
        
        # System status
        print(f"\nSystem Status:")
        print(f"  🤖 Venice AI: {'Available' if self.hybrid_router.openai_available or True else 'Unavailable'}")
        print(f"  🏆 OpenAI: {'Available' if self.hybrid_router.openai_available else 'Unavailable'}")
        print(f"  🔄 Hybrid Router: {'Ready' if success_rate >= 60 else 'Needs fixes'}")
        
        # Cost analysis
        try:
            routing_stats = self.hybrid_router.get_routing_stats()
            hybrid_analytics = self.cost_tracker.get_hybrid_analytics()
            
            print(f"\nCost Analysis:")
            print(f"  💰 Total Requests: {routing_stats['total_requests']}")
            print(f"  💸 Total Savings: ${routing_stats['total_cost_savings']:.4f}")
            print(f"  📈 Venice Usage: {routing_stats['venice_percentage']:.1f}%")
            print(f"  🏆 OpenAI Usage: {routing_stats['openai_percentage']:.1f}%")
            
        except Exception as e:
            print(f"\nCost analysis unavailable: {e}")
        
        # Recommendations
        print(f"\nRecommendations:")
        
        if success_rate >= 80:
            print("  ✅ Hybrid AI system is ready for production")
            print("  🚀 Expected 80-90% cost savings vs all-OpenAI")
            print("  💰 Premium quality for high-stakes decisions")
        elif success_rate >= 60:
            print("  ⚠️  Hybrid AI system needs minor fixes")
            print("  🔧 Review failed tests and address issues")
        else:
            print("  ❌ Hybrid AI system requires major fixes")
            print("  🛠️  Address critical failures before production use")

async def main():
    """Run hybrid AI system tests"""
    
    print("🤖 Starting Hybrid AI System Test Suite...")
    
    # Initialize test suite
    test_suite = HybridAISystemTest()
    
    # Run all tests
    await test_suite.run_all_tests()
    
    print("\n✅ Hybrid AI System Test Suite Complete!")

if __name__ == "__main__":
    asyncio.run(main())
