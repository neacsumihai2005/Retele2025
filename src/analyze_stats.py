import json
import logging
from collections import Counter
from typing import Dict, List
import socket
import whois
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Companies to track
COMPANIES = {
    'google': ['google', 'gstatic', 'gmail', 'youtube', 'doubleclick'],
    'facebook': ['facebook', 'fbcdn', 'instagram', 'whatsapp'],
    'amazon': ['amazon', 'aws', 'cloudfront'],
    'microsoft': ['microsoft', 'msft', 'windows', 'bing', 'live'],
    'apple': ['apple', 'icloud', 'itunes'],
    'twitter': ['twitter', 'twimg'],
    'adobe': ['adobe', 'adobecqms'],
    'cloudflare': ['cloudflare'],
    'akamai': ['akamai'],
    'fastly': ['fastly'],
}

def get_company_from_domain(domain: str) -> str:
    """Determine which company a domain belongs to."""
    domain_lower = domain.lower()
    
    for company, keywords in COMPANIES.items():
        if any(keyword in domain_lower for keyword in keywords):
            return company
    
    return 'other'

def analyze_blocked_requests():
    """Analyze the blocked requests and generate statistics."""
    try:
        with open('blocked_requests.json', 'r') as f:
            blocked_requests = json.load(f)
    except FileNotFoundError:
        logger.error("No blocked requests file found")
        return
    
    # Basic statistics
    total_requests = len(blocked_requests)
    unique_domains = len(set(req['domain'] for req in blocked_requests))
    
    # Company statistics
    company_counter = Counter()
    for req in blocked_requests:
        company = get_company_from_domain(req['domain'])
        company_counter[company] += 1
    
    # Time-based statistics
    requests_by_hour = Counter()
    for req in blocked_requests:
        timestamp = datetime.fromisoformat(req['timestamp'])
        hour = timestamp.strftime('%Y-%m-%d %H:00')
        requests_by_hour[hour] += 1
    
    # Print statistics
    print("\n=== DNS Ad Blocker Statistics ===")
    print(f"Total blocked requests: {total_requests}")
    print(f"Unique blocked domains: {unique_domains}")
    
    print("\nTop blocked companies:")
    for company, count in company_counter.most_common():
        percentage = (count / total_requests) * 100
        print(f"{company}: {count} requests ({percentage:.1f}%)")
    
    print("\nRequests by hour:")
    for hour, count in sorted(requests_by_hour.items()):
        print(f"{hour}: {count} requests")
    
    # Save detailed statistics to file
    stats = {
        'total_requests': total_requests,
        'unique_domains': unique_domains,
        'company_stats': dict(company_counter),
        'hourly_stats': dict(requests_by_hour)
    }
    
    with open('blocker_statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info("Statistics saved to blocker_statistics.json")

if __name__ == '__main__':
    analyze_blocked_requests() 