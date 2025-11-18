#!/usr/bin/env python3
"""
⚖️ COMPLIANCE AND ETHICAL SCRAPING MANAGER
==========================================

Comprehensive compliance framework with:
- Terms of service monitoring and enforcement
- Rate limiting and respectful scraping
- Robots.txt compliance
- Ethical data usage guidelines
- Legal compliance tracking

Author: TennisBot Advanced Analytics
Version: 1.0.0
"""

import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin
import time
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json
import re
from pathlib import Path
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceManager:
    """Manages compliance and ethical scraping practices"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Compliance settings
        self.respect_robots_txt = self.config.get('respect_robots_txt', True)
        self.max_requests_per_hour = self.config.get('max_requests_per_hour', 100)
        self.min_delay_between_requests = self.config.get('min_delay_between_requests', 1.0)
        self.user_agent = self.config.get('user_agent', 'TennisBot-Educational/1.0')

        # Domain tracking
        self.domain_rules = {}  # domain -> rules
        self.request_history = {}  # domain -> timestamps
        self.violations = {}  # domain -> violation count

        # Legal compliance
        self.allowed_domains = set(self.config.get('allowed_domains', []))
        self.blocked_domains = set(self.config.get('blocked_domains', []))
        self.gdpr_compliant = self.config.get('gdpr_compliant', True)

        # Load existing rules
        self._load_compliance_rules()

    def check_domain_compliance(self, url: str) -> Dict[str, Any]:
        """
        Check if a domain is compliant for scraping

        Returns:
            Dict with compliance status and details
        """
        domain = self._extract_domain(url)

        compliance_info = {
            'domain': domain,
            'compliant': True,
            'reasons': [],
            'warnings': [],
            'block_recommended': False
        }

        # Check blocked domains
        if domain in self.blocked_domains:
            compliance_info['compliant'] = False
            compliance_info['reasons'].append('Domain is in blocked list')
            compliance_info['block_recommended'] = True
            return compliance_info

        # Check allowed domains (if whitelist is active)
        if self.allowed_domains and domain not in self.allowed_domains:
            compliance_info['compliant'] = False
            compliance_info['reasons'].append('Domain not in allowed list')
            return compliance_info

        # Check robots.txt
        if self.respect_robots_txt:
            robots_check = self._check_robots_txt(url)
            if not robots_check['allowed']:
                compliance_info['compliant'] = False
                compliance_info['reasons'].append(f'Robots.txt disallows access: {robots_check["reason"]}')
                compliance_info.update(robots_check)

        # Check rate limits
        rate_check = self._check_rate_limits(domain)
        if not rate_check['within_limits']:
            compliance_info['compliant'] = False
            compliance_info['reasons'].append(f'Rate limit exceeded: {rate_check["reason"]}')
            compliance_info.update(rate_check)

        # Check for known ToS violations
        tos_check = self._check_terms_of_service(domain)
        if tos_check['violates_tos']:
            compliance_info['compliant'] = False
            compliance_info['reasons'].append(f'Terms of service violation: {tos_check["reason"]}')
            compliance_info['block_recommended'] = True
            compliance_info.update(tos_check)

        # Add warnings for edge cases
        if compliance_info['compliant']:
            warnings = self._get_compliance_warnings(domain)
            compliance_info['warnings'].extend(warnings)

        return compliance_info

    def get_request_headers(self, url: str) -> Dict[str, str]:
        """Get appropriate headers for a request to maintain compliance"""
        domain = self._extract_domain(url)

        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Add domain-specific headers if needed
        if domain in self.domain_rules:
            domain_headers = self.domain_rules[domain].get('required_headers', {})
            headers.update(domain_headers)

        return headers

    def enforce_request_delay(self, url: str) -> float:
        """
        Calculate and enforce appropriate delay between requests

        Returns:
            Delay time in seconds
        """
        domain = self._extract_domain(url)

        # Base delay
        delay = self.min_delay_between_requests

        # Domain-specific delays
        if domain in self.domain_rules:
            domain_delay = self.domain_rules[domain].get('min_delay', 0)
            delay = max(delay, domain_delay)

        # Rate-based delays
        if domain in self.request_history:
            recent_requests = self.request_history[domain]
            now = datetime.now()

            # Count requests in last hour
            hour_ago = now - timedelta(hours=1)
            recent_count = sum(1 for req_time in recent_requests if req_time > hour_ago)

            if recent_count >= self.max_requests_per_hour:
                # Calculate delay to stay under limit
                delay = max(delay, 3600 / self.max_requests_per_hour)

        # Apply delay
        time.sleep(delay)

        # Record request
        self._record_request(domain)

        return delay

    def validate_data_usage(self, data: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """
        Validate that data usage complies with regulations

        Args:
            data: The scraped data
            purpose: Intended use ('educational', 'research', 'commercial', etc.)

        Returns:
            Validation result with compliance status
        """
        validation = {
            'compliant': True,
            'issues': [],
            'recommendations': [],
            'gdpr_impact': 'none'
        }

        # Check data types for sensitive information
        sensitive_fields = ['email', 'phone', 'address', 'ssn', 'credit_card']
        found_sensitive = []

        def check_dict_for_sensitive(d):
            for key, value in d.items():
                key_lower = str(key).lower()
                if any(sensitive in key_lower for sensitive in sensitive_fields):
                    found_sensitive.append(key)
                elif isinstance(value, dict):
                    check_dict_for_sensitive(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            check_dict_for_sensitive(item)

        check_dict_for_sensitive(data)

        if found_sensitive:
            validation['compliant'] = False
            validation['issues'].append(f'Found sensitive data fields: {found_sensitive}')
            validation['gdpr_impact'] = 'high'
            validation['recommendations'].append('Remove or anonymize sensitive data fields')

        # Check data volume for commercial use
        if purpose == 'commercial':
            # Commercial use may have additional restrictions
            validation['recommendations'].append('Ensure commercial use complies with source terms')

        # Check for personal data
        personal_indicators = ['name', 'age', 'location', 'contact']
        personal_data_found = []

        def check_personal_data(d):
            for key, value in d.items():
                key_lower = str(key).lower()
                if any(indicator in key_lower for indicator in personal_indicators):
                    if isinstance(value, str) and len(value.strip()) > 0:
                        personal_data_found.append(key)

        check_personal_data(data)

        if personal_data_found and self.gdpr_compliant:
            validation['gdpr_impact'] = 'medium'
            validation['recommendations'].append('Consider GDPR implications for personal data')

        return validation

    def report_violation(self, domain: str, violation_type: str, details: str = ""):
        """Report a compliance violation"""
        if domain not in self.violations:
            self.violations[domain] = []

        violation = {
            'timestamp': datetime.now().isoformat(),
            'type': violation_type,
            'details': details,
            'domain': domain
        }

        self.violations[domain].append(violation)

        logger.warning(f"🚨 Compliance violation reported: {domain} - {violation_type}")

        # Auto-block severely violating domains
        severe_violations = ['tos_violation', 'legal_violation', 'data_breach']
        if violation_type in severe_violations:
            self.blocked_domains.add(domain)
            logger.critical(f"🚫 Auto-blocked domain {domain} due to severe violation")

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_domains_checked': len(set(list(self.request_history.keys()) + list(self.violations.keys()))),
                'blocked_domains': len(self.blocked_domains),
                'domains_with_violations': len(self.violations),
                'total_violations': sum(len(violations) for violations in self.violations.values())
            },
            'violations': self.violations,
            'blocked_domains': list(self.blocked_domains),
            'request_history': {
                domain: len(timestamps) for domain, timestamps in self.request_history.items()
            }
        }

        return report

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _check_robots_txt(self, url: str) -> Dict[str, Any]:
        """Check robots.txt compliance"""
        result = {
            'allowed': True,
            'reason': '',
            'crawl_delay': 0,
            'checked': False
        }

        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            result['allowed'] = rp.can_fetch(self.user_agent, url)
            result['checked'] = True

            if not result['allowed']:
                result['reason'] = 'Robots.txt disallows this user agent/path'

            # Get crawl delay
            delay = rp.crawl_delay(self.user_agent)
            if delay:
                result['crawl_delay'] = delay

        except Exception as e:
            logger.debug(f"Error checking robots.txt for {url}: {e}")
            result['reason'] = f'Could not check robots.txt: {e}'

        return result

    def _check_rate_limits(self, domain: str) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        result = {
            'within_limits': True,
            'reason': '',
            'current_requests': 0,
            'limit': self.max_requests_per_hour
        }

        if domain not in self.request_history:
            return result

        recent_requests = self.request_history[domain]
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Count requests in last hour
        result['current_requests'] = sum(1 for req_time in recent_requests if req_time > hour_ago)

        if result['current_requests'] >= self.max_requests_per_hour:
            result['within_limits'] = False
            result['reason'] = f'{result["current_requests"]} requests in last hour (limit: {self.max_requests_per_hour})'

        return result

    def _check_terms_of_service(self, domain: str) -> Dict[str, Any]:
        """Check terms of service compliance"""
        result = {
            'violates_tos': False,
            'reason': '',
            'tos_url': '',
            'last_checked': None
        }

        # Known ToS restrictions (this would be expanded with actual research)
        tos_restrictions = {
            'oddsportal.com': {
                'commercial_use': False,
                'automated_access': False,
                'reason': 'Commercial use and automated access prohibited'
            },
            'flashscore.com': {
                'commercial_use': False,
                'reason': 'Commercial use prohibited without permission'
            },
            'atptour.com': {
                'automated_access': False,
                'reason': 'Automated access restricted'
            }
        }

        if domain in tos_restrictions:
            restrictions = tos_restrictions[domain]
            result['violates_tos'] = True
            result['reason'] = restrictions['reason']
            result['tos_url'] = f"https://{domain}/terms"

        return result

    def _get_compliance_warnings(self, domain: str) -> List[str]:
        """Get compliance warnings for a domain"""
        warnings = []

        # Check for high-risk domains
        high_risk_domains = ['betting', 'gambling', 'odds']
        if any(risk in domain for risk in high_risk_domains):
            warnings.append('Domain appears to be gambling-related - ensure compliance with local laws')

        # Check for international domains
        if '.com' not in domain:
            warnings.append('Non-.com domain - verify international data protection laws')

        return warnings

    def _record_request(self, domain: str):
        """Record a request for rate limiting"""
        if domain not in self.request_history:
            self.request_history[domain] = []

        self.request_history[domain].append(datetime.now())

        # Keep only recent requests (last 24 hours)
        day_ago = datetime.now() - timedelta(days=1)
        self.request_history[domain] = [
            req_time for req_time in self.request_history[domain]
            if req_time > day_ago
        ]

    def _load_compliance_rules(self):
        """Load domain-specific compliance rules"""
        # This would load from a configuration file
        # For now, using hardcoded rules
        self.domain_rules = {
            'oddsportal.com': {
                'min_delay': 5.0,
                'max_requests_per_hour': 50,
                'required_headers': {
                    'Referer': 'https://www.oddsportal.com/'
                }
            },
            'flashscore.com': {
                'min_delay': 3.0,
                'max_requests_per_hour': 100,
                'required_headers': {
                    'Referer': 'https://www.flashscore.com/'
                }
            },
            'atptour.com': {
                'min_delay': 2.0,
                'max_requests_per_hour': 200
            }
        }

    def export_compliance_report(self, filename: str = None) -> str:
        """Export compliance report to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"compliance_report_{timestamp}.json"

        report = self.get_compliance_report()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📋 Exported compliance report to {filename}")
        return filename

class EthicalScrapingFramework:
    """Framework for ethical web scraping practices"""

    def __init__(self, compliance_manager: ComplianceManager):
        self.compliance = compliance_manager
        self.ethical_guidelines = self._load_ethical_guidelines()

    def assess_scraping_ethics(self, target: str, purpose: str, data_types: List[str]) -> Dict[str, Any]:
        """
        Assess the ethical implications of a scraping operation

        Args:
            target: Target website/domain
            purpose: Scraping purpose
            data_types: Types of data being collected

        Returns:
            Ethical assessment
        """
        assessment = {
            'ethical_score': 100,  # Start with perfect score
            'concerns': [],
            'recommendations': [],
            'approved': True
        }

        # Check purpose ethics
        if purpose == 'commercial':
            assessment['ethical_score'] -= 20
            assessment['concerns'].append('Commercial use may compete with data source revenue')

        # Check data sensitivity
        sensitive_data = ['personal', 'financial', 'medical', 'contact']
        for data_type in data_types:
            if any(sensitive in data_type.lower() for sensitive in sensitive_data):
                assessment['ethical_score'] -= 30
                assessment['concerns'].append(f'Sensitive data type: {data_type}')
                assessment['approved'] = False

        # Check target reputation
        reputable_sources = ['wikipedia.org', 'gov.uk', 'edu']
        if not any(reputable in target for reputable in reputable_sources):
            assessment['ethical_score'] -= 10
            assessment['concerns'].append('Target source may have data usage restrictions')

        # Generate recommendations
        if assessment['ethical_score'] < 70:
            assessment['recommendations'].append('Consider obtaining explicit permission from data source')
            assessment['recommendations'].append('Implement data minimization practices')

        if assessment['ethical_score'] < 50:
            assessment['approved'] = False
            assessment['recommendations'].append('Reconsider scraping operation - may violate ethical guidelines')

        return assessment

    def _load_ethical_guidelines(self) -> Dict[str, Any]:
        """Load ethical scraping guidelines"""
        return {
            'data_minimization': 'Only collect data necessary for your purpose',
            'transparency': 'Be transparent about data collection',
            'consent': 'Obtain consent when collecting personal data',
            'fair_use': 'Respect copyright and terms of service',
            'no_harm': 'Do not cause harm to data sources or individuals',
            'attribution': 'Properly attribute data sources when appropriate'
        }

# Convenience functions
def check_scraping_compliance(url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to check scraping compliance"""
    manager = ComplianceManager(config)
    return manager.check_domain_compliance(url)

def validate_data_compliance(data: Dict[str, Any], purpose: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to validate data usage compliance"""
    manager = ComplianceManager(config)
    return manager.validate_data_usage(data, purpose)

if __name__ == "__main__":
    # Test the compliance manager
    print("⚖️ COMPLIANCE AND ETHICAL SCRAPING MANAGER TEST")
    print("=" * 60)

    # Test configuration
    config = {
        'respect_robots_txt': True,
        'max_requests_per_hour': 100,
        'min_delay_between_requests': 1.0,
        'user_agent': 'TennisBot-Educational/1.0',
        'gdpr_compliant': True
    }

    try:
        # Initialize compliance manager
        compliance = ComplianceManager(config)

        # Test domains
        test_domains = [
            'https://www.oddsportal.com/tennis/',
            'https://www.flashscore.com/tennis/',
            'https://www.atptour.com/en/scores/current'
        ]

        print("🧪 Testing domain compliance checks...")

        for url in test_domains:
            print(f"\n🔍 Checking {url}...")
            result = compliance.check_domain_compliance(url)

            print(f"   Compliant: {result['compliant']}")
            if result['reasons']:
                print(f"   Reasons: {', '.join(result['reasons'])}")
            if result['warnings']:
                print(f"   Warnings: {', '.join(result['warnings'])}")

        # Test data validation
        print("\n🧪 Testing data usage validation...")

        test_data = {
            'match': 'Player A vs Player B',
            'odds': {'home': 2.10, 'away': 1.85},
            'personal_info': {'email': 'test@example.com'}  # Sensitive data
        }

        validation = compliance.validate_data_usage(test_data, 'educational')
        print(f"   Data compliant: {validation['compliant']}")
        if validation['issues']:
            print(f"   Issues: {', '.join(validation['issues'])}")

        # Export compliance report
        report_file = compliance.export_compliance_report()
        print(f"\n📋 Compliance report exported to: {report_file}")

        print("\n✅ Compliance manager test completed successfully")

    except Exception as e:
        print(f"❌ Compliance manager test failed: {e}")
        import traceback
        traceback.print_exc()