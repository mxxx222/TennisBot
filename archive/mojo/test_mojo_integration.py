#!/usr/bin/env python3
"""
Tests for Mojo Performance Layer Integration
Compares Mojo vs Python implementations for accuracy and performance
"""

import unittest
import numpy as np
import time
import os
from typing import Dict, Any

# Set environment variable to test both paths
os.environ['USE_MOJO_LAYER'] = 'true'

try:
    from src.mojo_bindings import (
        batch_predict,
        ensemble_aggregate,
        feature_transform,
        normalize_features,
        compute_statistics,
        vectorized_transforms,
        get_performance_stats,
        should_use_mojo
    )
    from src.mojo_performance_monitor import MojoPerformanceMonitor
    MOJO_BINDINGS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Mojo bindings not available: {e}")
    MOJO_BINDINGS_AVAILABLE = False


class TestMojoIntegration(unittest.TestCase):
    """Test Mojo integration and performance"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.monitor = MojoPerformanceMonitor()
        np.random.seed(42)  # For reproducible tests
    
    def test_ensemble_aggregate_accuracy(self):
        """Test that Mojo ensemble aggregation matches Python fallback"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        # Create test data
        batch_size = 100
        num_models = 4
        
        predictions = [
            np.random.rand(batch_size) for _ in range(num_models)
        ]
        weights = np.random.rand(num_models)
        weights = weights / weights.sum()  # Normalize
        
        # Test Mojo implementation
        os.environ['USE_MOJO_LAYER'] = 'true'
        result_mojo = ensemble_aggregate(predictions, weights)
        
        # Test Python fallback
        os.environ['USE_MOJO_LAYER'] = 'false'
        result_python = ensemble_aggregate(predictions, weights)
        
        # Compare results (should be nearly identical)
        np.testing.assert_allclose(result_mojo, result_python, rtol=1e-5, atol=1e-7)
        print(f"✅ Ensemble aggregation accuracy test passed")
        print(f"   Max difference: {np.max(np.abs(result_mojo - result_python)):.2e}")
    
    def test_feature_transform_accuracy(self):
        """Test that Mojo feature transformation matches Python fallback"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        # Create test data
        batch_size = 50
        num_features = 20
        
        features = np.random.randn(batch_size, num_features) * 10 + 5
        mean = np.random.randn(num_features) * 2
        std = np.random.rand(num_features) * 3 + 1
        
        # Test Mojo implementation
        os.environ['USE_MOJO_LAYER'] = 'true'
        result_mojo = feature_transform(features, mean, std)
        
        # Test Python fallback
        os.environ['USE_MOJO_LAYER'] = 'false'
        result_python = feature_transform(features, mean, std)
        
        # Compare results
        np.testing.assert_allclose(result_mojo, result_python, rtol=1e-5, atol=1e-7)
        print(f"✅ Feature transformation accuracy test passed")
        print(f"   Max difference: {np.max(np.abs(result_mojo - result_python)):.2e}")
    
    def test_compute_statistics_accuracy(self):
        """Test that Mojo statistics computation matches Python fallback"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        # Create test data
        data = np.random.randn(1000) * 10 + 5
        
        # Test Mojo implementation
        os.environ['USE_MOJO_LAYER'] = 'true'
        result_mojo = compute_statistics(data)
        
        # Test Python fallback
        os.environ['USE_MOJO_LAYER'] = 'false'
        result_python = compute_statistics(data)
        
        # Compare results
        for key in result_mojo.keys():
            self.assertAlmostEqual(
                result_mojo[key], result_python[key],
                places=6,
                msg=f"Statistics mismatch for {key}"
            )
        
        print(f"✅ Statistics computation accuracy test passed")
    
    def test_batch_predict_performance(self):
        """Test batch prediction performance"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        # Create larger test data
        batch_size = 1000
        num_models = 4
        
        features = np.random.rand(batch_size, 10)
        model_weights = np.random.rand(num_models)
        model_weights = model_weights / model_weights.sum()
        
        predictions_list = [
            np.random.rand(batch_size) for _ in range(num_models)
        ]
        
        # Test Mojo implementation
        os.environ['USE_MOJO_LAYER'] = 'true'
        start = time.time()
        result_mojo = batch_predict(features, model_weights, predictions_list)
        mojo_time = time.time() - start
        
        # Test Python fallback
        os.environ['USE_MOJO_LAYER'] = 'false'
        start = time.time()
        result_python = batch_predict(features, model_weights, predictions_list)
        python_time = time.time() - start
        
        # Compare results
        np.testing.assert_allclose(result_mojo, result_python, rtol=1e-5)
        
        speedup = python_time / mojo_time if mojo_time > 0 else 0
        print(f"✅ Batch prediction performance test passed")
        print(f"   Mojo time: {mojo_time*1000:.2f}ms")
        print(f"   Python time: {python_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.2f}x")
    
    def test_vectorized_transforms_performance(self):
        """Test vectorized transforms performance"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        # Create larger test data
        data = np.random.randn(10000) * 10
        
        # Test Mojo implementation
        os.environ['USE_MOJO_LAYER'] = 'true'
        start = time.time()
        result_mojo = vectorized_transforms(data, "normalize")
        mojo_time = time.time() - start
        
        # Test Python fallback
        os.environ['USE_MOJO_LAYER'] = 'false'
        start = time.time()
        result_python = vectorized_transforms(data, "normalize")
        python_time = time.time() - start
        
        # Compare results
        np.testing.assert_allclose(result_mojo, result_python, rtol=1e-5)
        
        speedup = python_time / mojo_time if mojo_time > 0 else 0
        print(f"✅ Vectorized transforms performance test passed")
        print(f"   Mojo time: {mojo_time*1000:.2f}ms")
        print(f"   Python time: {python_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.2f}x")
    
    def test_fallback_behavior(self):
        """Test that fallback works when Mojo is unavailable"""
        # Temporarily disable Mojo
        original_value = os.environ.get('USE_MOJO_LAYER', 'true')
        os.environ['USE_MOJO_LAYER'] = 'false'
        
        try:
            # Should still work with Python fallback
            data = np.random.randn(100)
            result = compute_statistics(data)
            
            self.assertIn('mean', result)
            self.assertIn('std', result)
            self.assertIn('min', result)
            self.assertIn('max', result)
            
            print(f"✅ Fallback behavior test passed")
        finally:
            os.environ['USE_MOJO_LAYER'] = original_value
    
    def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        monitor = MojoPerformanceMonitor()
        
        # Log some operations
        monitor.log_operation("test_op", True, 0.001)
        monitor.log_operation("test_op", False, 0.005)
        monitor.log_operation("test_op", True, 0.0008)
        
        stats = monitor.get_operation_stats("test_op")
        
        self.assertEqual(stats['mojo_calls'], 2)
        self.assertEqual(stats['python_calls'], 1)
        self.assertIn('speedup', stats)
        
        summary = monitor.get_all_stats()
        self.assertIn('summary', summary)
        self.assertIn('operations', summary)
        
        print(f"✅ Performance monitoring test passed")
        print(f"   Stats: {stats}")
    
    def test_integration_with_real_data(self):
        """Test integration with realistic data shapes"""
        if not MOJO_BINDINGS_AVAILABLE:
            self.skipTest("Mojo bindings not available")
        
        os.environ['USE_MOJO_LAYER'] = 'true'
        
        # Simulate real inference scenario
        batch_size = 100
        num_features = 50
        num_models = 3
        
        features = np.random.randn(batch_size, num_features)
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0) + 1e-6  # Avoid division by zero
        
        predictions = [
            np.random.rand(batch_size) for _ in range(num_models)
        ]
        weights = np.array([0.4, 0.4, 0.2])
        
        # Test full pipeline
        normalized = feature_transform(features, mean, std)
        ensemble = ensemble_aggregate(predictions, weights)
        
        self.assertEqual(normalized.shape, features.shape)
        self.assertEqual(len(ensemble), batch_size)
        
        print(f"✅ Real data integration test passed")


def run_performance_benchmark():
    """Run comprehensive performance benchmark"""
    print("\n" + "="*60)
    print("MOJO PERFORMANCE BENCHMARK")
    print("="*60)
    
    if not MOJO_BINDINGS_AVAILABLE:
        print("⚠️  Mojo bindings not available - running Python-only benchmarks")
        os.environ['USE_MOJO_LAYER'] = 'false'
    
    monitor = MojoPerformanceMonitor()
    
    # Benchmark ensemble aggregation
    print("\n📊 Benchmarking ensemble aggregation...")
    for batch_size in [100, 1000, 10000]:
        predictions = [np.random.rand(batch_size) for _ in range(4)]
        weights = np.random.rand(4)
        weights = weights / weights.sum()
        
        os.environ['USE_MOJO_LAYER'] = 'true'
        start = time.time()
        result_mojo = ensemble_aggregate(predictions, weights)
        mojo_time = time.time() - start
        
        os.environ['USE_MOJO_LAYER'] = 'false'
        start = time.time()
        result_python = ensemble_aggregate(predictions, weights)
        python_time = time.time() - start
        
        speedup = python_time / mojo_time if mojo_time > 0 else 0
        print(f"  Batch size {batch_size}: Mojo={mojo_time*1000:.2f}ms, Python={python_time*1000:.2f}ms, Speedup={speedup:.2f}x")
    
    # Print summary
    monitor.print_summary()
    
    # Save report
    report_path = monitor.save_report()
    print(f"\n📄 Full report saved to: {report_path}")


if __name__ == '__main__':
    # Run tests
    print("Running Mojo integration tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run benchmark
    run_performance_benchmark()

