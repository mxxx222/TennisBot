#!/usr/bin/env python3
"""
Data validation helpers for all scrapers.
"""

from typing import Dict, List, Any
from datetime import datetime


def validate_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate match data before writing to production.

    Returns:
        {
            "is_valid": bool,
            "errors": List[Dict] with check_type, field, expected, actual, severity
        }
    """
    errors = []

    # Required fields
    required_fields = [
        "player_a",
        "player_b",
        "tournament",
        "surface",
        "match_date"
    ]

    for field in required_fields:
        if not match.get(field):
            errors.append({
                "check_type": "Missing Field",
                "field": field,
                "expected": "non-empty",
                "actual": "empty or missing",
                "severity": "Critical"
            })

    # Validate odds range
    if match.get("odds_a"):
        if not (1.01 <= match["odds_a"] <= 50.0):
            errors.append({
                "check_type": "Invalid Odds",
                "field": "odds_a",
                "expected": "1.01-50.0",
                "actual": str(match["odds_a"]),
                "severity": "Warning"
            })

    # Validate surface
    valid_surfaces = ["Hard", "Clay", "Grass", "Indoor Hard", "Carpet"]
    if match.get("surface") and match["surface"] not in valid_surfaces:
        errors.append({
            "check_type": "Surface Mismatch",
            "field": "surface",
            "expected": f"One of {valid_surfaces}",
            "actual": match["surface"],
            "severity": "Warning"
        })

    # Check for critical errors
    critical_errors = [e for e in errors if e["severity"] == "Critical"]

    return {
        "is_valid": len(critical_errors) == 0,
        "errors": errors
    }

