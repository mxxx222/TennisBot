"""
Mojo Performance Monitoring Module
Tracks and reports performance improvements from Mojo acceleration
"""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    from src.mojo_bindings import get_performance_stats
    MOJO_BINDINGS_AVAILABLE = True
except ImportError:
    MOJO_BINDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MojoPerformanceMonitor:
    """Monitor and report Mojo performance improvements"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "data/mojo_performance.log"
        self.stats = defaultdict(lambda: {
            'mojo_calls': 0,
            'python_calls': 0,
            'mojo_total_time': 0.0,
            'python_total_time': 0.0,
            'errors': []
        })
        self.operation_history = []
        
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_operation(
        self,
        operation: str,
        use_mojo: bool,
        elapsed_time: float,
        input_size: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log a single operation"""
        self.stats[operation]['mojo_calls' if use_mojo else 'python_calls'] += 1
        if use_mojo:
            self.stats[operation]['mojo_total_time'] += elapsed_time
        else:
            self.stats[operation]['python_total_time'] += elapsed_time
        
        if error:
            self.stats[operation]['errors'].append(error)
        
        self.operation_history.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'use_mojo': use_mojo,
            'elapsed_time': elapsed_time,
            'input_size': input_size,
            'error': error
        })
        
        # Keep only last 1000 operations in memory
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for a specific operation"""
        stats = self.stats[operation]
        
        result = {
            'operation': operation,
            'mojo_calls': stats['mojo_calls'],
            'python_calls': stats['python_calls'],
            'total_calls': stats['mojo_calls'] + stats['python_calls'],
            'errors': len(stats['errors'])
        }
        
        if stats['mojo_calls'] > 0:
            result['avg_mojo_time_ms'] = (stats['mojo_total_time'] / stats['mojo_calls']) * 1000
        if stats['python_calls'] > 0:
            result['avg_python_time_ms'] = (stats['python_total_time'] / stats['python_calls']) * 1000
        
        if stats['mojo_calls'] > 0 and stats['python_calls'] > 0:
            mojo_avg = result.get('avg_mojo_time_ms', 0)
            python_avg = result.get('avg_python_time_ms', 0)
            if mojo_avg > 0:
                result['speedup'] = python_avg / mojo_avg
                result['time_saved_percent'] = ((python_avg - mojo_avg) / python_avg) * 100
        
        return result
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        all_operations = {}
        
        for operation in self.stats.keys():
            all_operations[operation] = self.get_operation_stats(operation)
        
        # Get bindings stats if available
        bindings_stats = {}
        if MOJO_BINDINGS_AVAILABLE:
            try:
                bindings_stats = get_performance_stats()
            except Exception as e:
                logger.warning(f"Failed to get bindings stats: {e}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'operations': all_operations,
            'bindings_stats': bindings_stats,
            'total_operations': len(self.operation_history),
            'summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_mojo_calls = sum(s['mojo_calls'] for s in self.stats.values())
        total_python_calls = sum(s['python_calls'] for s in self.stats.values())
        total_mojo_time = sum(s['mojo_total_time'] for s in self.stats.values())
        total_python_time = sum(s['python_total_time'] for s in self.stats.values())
        
        summary = {
            'total_mojo_calls': total_mojo_calls,
            'total_python_calls': total_python_calls,
            'total_calls': total_mojo_calls + total_python_calls,
            'mojo_usage_percent': (total_mojo_calls / (total_mojo_calls + total_python_calls) * 100) if (total_mojo_calls + total_python_calls) > 0 else 0
        }
        
        if total_mojo_calls > 0 and total_python_calls > 0:
            avg_mojo_time = (total_mojo_time / total_mojo_calls) * 1000
            avg_python_time = (total_python_time / total_python_calls) * 1000
            if avg_mojo_time > 0:
                summary['overall_speedup'] = avg_python_time / avg_mojo_time
                summary['time_saved_percent'] = ((avg_python_time - avg_mojo_time) / avg_python_time) * 100
        
        return summary
    
    def save_report(self, filepath: Optional[str] = None) -> str:
        """Save performance report to file"""
        filepath = filepath or f"data/mojo_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_all_stats()
        
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {filepath}")
        return filepath
    
    def print_summary(self):
        """Print performance summary to console"""
        stats = self.get_all_stats()
        summary = stats['summary']
        
        print("\n" + "="*60)
        print("MOJO PERFORMANCE MONITOR SUMMARY")
        print("="*60)
        print(f"Total Operations: {stats['total_operations']}")
        print(f"Mojo Calls: {summary['total_mojo_calls']}")
        print(f"Python Calls: {summary['total_python_calls']}")
        print(f"Mojo Usage: {summary['mojo_usage_percent']:.1f}%")
        
        if 'overall_speedup' in summary:
            print(f"Overall Speedup: {summary['overall_speedup']:.2f}x")
            print(f"Time Saved: {summary['time_saved_percent']:.1f}%")
        
        print("\nOperation Details:")
        print("-" * 60)
        
        for op_name, op_stats in stats['operations'].items():
            print(f"\n{op_name}:")
            print(f"  Total Calls: {op_stats['total_calls']}")
            print(f"  Mojo: {op_stats['mojo_calls']}, Python: {op_stats['python_calls']}")
            
            if 'speedup' in op_stats:
                print(f"  Speedup: {op_stats['speedup']:.2f}x")
                print(f"  Avg Mojo: {op_stats.get('avg_mojo_time_ms', 0):.2f}ms")
                print(f"  Avg Python: {op_stats.get('avg_python_time_ms', 0):.2f}ms")
        
        print("="*60 + "\n")


# Global monitor instance
_global_monitor: Optional[MojoPerformanceMonitor] = None


def get_monitor() -> MojoPerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = MojoPerformanceMonitor()
    return _global_monitor


def log_operation(operation: str, use_mojo: bool, elapsed_time: float, **kwargs):
    """Log operation to global monitor"""
    monitor = get_monitor()
    monitor.log_operation(operation, use_mojo, elapsed_time, **kwargs)

