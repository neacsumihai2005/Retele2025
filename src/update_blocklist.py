import requests
import logging
from typing import Set
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sources for ad domain lists
BLOCKLIST_SOURCES = [
    'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',
    'https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhosts.txt',
    'https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.2o7Net/hosts',
    'https://raw.githubusercontent.com/crazy-max/WindowsSpyBlocker/master/data/hosts/spy.txt',
    'https://hostfiles.frogeye.fr/firstparty-trackers-hosts.txt'
]

def download_blocklist(url: str) -> Set[str]:
    """Download and parse a blocklist from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        domains = set()
        for line in response.text.splitlines():
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            # Parse hosts file format
            parts = line.strip().split()
            if len(parts) >= 2:
                domain = parts[1].strip()
                if domain and not domain.startswith('#'):
                    domains.add(domain)
        
        logger.info(f"Downloaded {len(domains)} domains from {url}")
        return domains
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return set()

def main():
    """Download and combine blocklists."""
    all_domains = set()
    
    for url in BLOCKLIST_SOURCES:
        domains = download_blocklist(url)
        all_domains.update(domains)
    
    # Remove duplicates and sort
    all_domains = sorted(all_domains)
    
    # Save to file
    with open('blocked_domains.txt', 'w') as f:
        for domain in all_domains:
            f.write(f"{domain}\n")
    
    logger.info(f"Saved {len(all_domains)} unique domains to blocked_domains.txt")

if __name__ == '__main__':
    main() 