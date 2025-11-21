#!/usr/bin/env python3
"""
Unified Scraper Monitoring Library

Tracks execution, errors, and data quality across all scrapers.
"""

import os
import traceback
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()


class ScraperMonitor:
    """Unified monitoring for all scrapers"""

    def __init__(self, scraper_name: str, environment: str = "Production"):
        self.scraper_name = scraper_name
        self.environment = environment
        self.notion = Client(auth=os.getenv("NOTION_TOKEN"))

        # Database IDs from environment
        self.runs_db = os.getenv("SCRAPER_RUNS_DB_ID")
        self.errors_db = os.getenv("SCRAPER_ERRORS_DB_ID")
        self.quality_db = os.getenv("DATA_QUALITY_DB_ID")

    def start_run(self) -> str:
        """Start a new scraper run, returns run_id"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = f"{timestamp}_{self.scraper_name.replace(' ', '_')}"

        try:
            self.notion.pages.create(
                parent={"database_id": self.runs_db},
                properties={
                    "Run ID": {"title": [{"text": {"content": run_id}}]},
                    "Scraper Name": {"select": {"name": self.scraper_name}},
                    "Status": {"status": {"name": "Running"}},
                    "Environment": {"select": {"name": self.environment}},
                    "Start Time": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
                }
            )
            print(f"✅ Started monitoring run: {run_id}")
        except Exception as e:
            print(f"⚠️  Failed to log run start: {e}")

        return run_id

    def complete_run(
        self,
        run_id: str,
        status: str = "Success",
        matches_found: int = 0,
        matches_written: int = 0,
        duplicates_skipped: int = 0,
        errors_count: int = 0,
        data_quality_score: float = 100.0,
        notes: str = ""
    ):
        """Complete a scraper run with final metrics"""
        try:
            # Find the page by run_id
            results = self.notion.databases.query(
                database_id=self.runs_db,
                filter={
                    "property": "Run ID",
                    "title": {"equals": run_id}
                }
            )

            if not results["results"]:
                print(f"⚠️  Run {run_id} not found in database")
                return

            page_id = results["results"][0]["id"]

            # Calculate duration
            start_time_str = results["results"][0]["properties"]["Start Time"]["date"]["start"]
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            duration = int((datetime.now(timezone.utc) - start_time).total_seconds())

            # Update page
            self.notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"status": {"name": status}},
                    "End Time": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
                    "Duration (s)": {"number": duration},
                    "Matches Found": {"number": matches_found},
                    "Matches Written": {"number": matches_written},
                    "Duplicates Skipped": {"number": duplicates_skipped},
                    "Errors": {"number": errors_count},
                    "Data Quality Score": {"number": round(data_quality_score, 1)},
                    "Notes": {"rich_text": [{"text": {"content": notes[:2000]}}]} if notes else {"rich_text": []}
                }
            )

            print(f"✅ Completed run: {run_id} ({status})")
        except Exception as e:
            print(f"⚠️  Failed to complete run: {e}")

    def log_error(
        self,
        run_id: str,
        exception: Exception,
        severity: str = "High",
        impact: str = "Partial Failure",
        context: str = ""
    ):
        """Log an error to Scraper Errors database"""
        try:
            error_type = type(exception).__name__
            error_message = str(exception)
            stack_trace = traceback.format_exc()

            self.notion.pages.create(
                parent={"database_id": self.errors_db},
                properties={
                    "Error ID": {"title": [{"text": {"content": f"{run_id}_{error_type}"}}]},
                    "Run ID": {"rich_text": [{"text": {"content": run_id}}]},
                    "Scraper Name": {"select": {"name": self.scraper_name}},
                    "Error Type": {"select": {"name": error_type}},
                    "Error Message": {"rich_text": [{"text": {"content": error_message[:2000]}}]},
                    "Stack Trace": {"rich_text": [{"text": {"content": stack_trace[:2000]}}]},
                    "Severity": {"select": {"name": severity}},
                    "Impact": {"select": {"name": impact}},
                    "Resolution Status": {"status": {"name": "Unresolved"}},
                    "First Seen": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
                }
            )

            print(f"⚠️  Logged error: {error_type}")
        except Exception as e:
            print(f"❌ Failed to log error: {e}")

    def log_quality_issue(
        self,
        run_id: str,
        match_ref: str,
        check_type: str,
        field_name: str,
        expected: str,
        actual: str,
        severity: str = "Warning",
        action: str = "Quarantined"
    ):
        """Log a data quality issue"""
        try:
            self.notion.pages.create(
                parent={"database_id": self.quality_db},
                properties={
                    "Validation ID": {"title": [{"text": {"content": f"{run_id}_{match_ref}_{field_name}"}}]},
                    "Run ID": {"rich_text": [{"text": {"content": run_id}}]},
                    "Scraper Name": {"select": {"name": self.scraper_name}},
                    "Match Reference": {"rich_text": [{"text": {"content": match_ref}}]},
                    "Check Type": {"select": {"name": check_type}},
                    "Field Name": {"rich_text": [{"text": {"content": field_name}}]},

                    "Expected Value": {"rich_text": [{"text": {"content": str(expected)[:2000]}}]},
                    "Actual Value": {"rich_text": [{"text": {"content": str(actual)[:2000]}}]},
                    "Severity": {"select": {"name": severity}},
                    "Action Taken": {"select": {"name": action}},
                    "Review Status": {"status": {"name": "Pending"}},
                    "Detected At": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
                }
            )
        except Exception as e:
            print(f"⚠️  Failed to log quality issue: {e}")


# Convenience function for quick validation
def validate_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """Quick match validation wrapper"""
    from shared.validators import validate_match as _validate
    return _validate(match)

