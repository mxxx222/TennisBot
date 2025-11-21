#!/usr/bin/env python3
"""
ML Dashboard CLI
================

Command-line interface for performance dashboard.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.performance_dashboard import PerformanceDashboard

if __name__ == "__main__":
    dashboard = PerformanceDashboard()
    dashboard.print_dashboard()

