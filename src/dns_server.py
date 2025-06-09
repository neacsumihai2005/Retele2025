import socket
import struct
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import json
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DNSServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 53):
        self.host = host
        self.port = port
        self.blocked_domains = set()
        self.blocked_requests = []
        self.load_blocked_domains()
        
    def load_blocked_domains(self):
        """Load the list of blocked domains from a file."""
        try:
            with open('blocked_domains.txt', 'r') as f:
                self.blocked_domains = set(line.strip() for line in f)
            logger.info(f"Loaded {len(self.blocked_domains)} blocked domains")
        except FileNotFoundError:
            logger.warning("No blocked domains file found. Creating empty list.")
            self.blocked_domains = set()

    def save_blocked_request(self, domain: str):
        """Save information about a blocked request."""
        timestamp = datetime.now().isoformat()
        self.blocked_requests.append({
            'timestamp': timestamp,
            'domain': domain
        })
        
        # Save to file periodically
        if len(self.blocked_requests) % 10 == 0:
            self.write_blocked_requests()

    def write_blocked_requests(self):
        """Write blocked requests to a file."""
        with open('blocked_requests.json', 'w') as f:
            json.dump(self.blocked_requests, f, indent=2)

    def parse_domain(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Parse a domain name from DNS packet."""
        domain = []
        while True:
            length = data[offset]
            if length == 0:
                break
            if length & 0xC0 == 0xC0:  # Handle DNS compression
                pointer = struct.unpack('!H', data[offset:offset+2])[0] & 0x3FFF
                domain.append(self.parse_domain(data, pointer)[0])
                offset += 2
                break
            offset += 1
            domain.append(data[offset:offset+length].decode())
            offset += length
        return '.'.join(domain), offset + 1

    def create_response(self, query_id: int, domain: str, is_blocked: bool) -> bytes:
        """Create a DNS response packet."""
        # DNS header
        response = struct.pack('!HHHHHH', 
            query_id,  # ID
            0x8180,    # Flags (Standard query response, No error)
            1,         # Questions
            1 if is_blocked else 0,  # Answer RRs
            0,         # Authority RRs
            0          # Additional RRs
        )

        # Original question
        for part in domain.split('.'):
            response += struct.pack('!B', len(part))
            response += part.encode()
        response += b'\x00'
        response += struct.pack('!HH', 1, 1)  # Type A, Class IN

        # Answer section (if blocked)
        if is_blocked:
            # Name pointer to question
            response += struct.pack('!H', 0xC000 | 12)
            # Type A, Class IN, TTL, RDLength, RData (0.0.0.0)
            response += struct.pack('!HHIH', 1, 1, 300, 4)
            response += socket.inet_aton('0.0.0.0')

        return response

    def handle_query(self, data: bytes, addr: Tuple[str, int]) -> bytes:
        """Handle an incoming DNS query."""
        try:
            query_id = struct.unpack('!H', data[0:2])[0]
            domain, _ = self.parse_domain(data, 12)
            
            is_blocked = domain in self.blocked_domains
            if is_blocked:
                logger.info(f"Blocked request for domain: {domain}")
                self.save_blocked_request(domain)
            
            return self.create_response(query_id, domain, is_blocked)
        except Exception as e:
            logger.error(f"Error handling query: {str(e)}")
            logger.error(traceback.format_exc())
            return b''

    def start(self):
        """Start the DNS server."""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server.bind((self.host, self.port))
            logger.info(f"DNS server started on {self.host}:{self.port}")

            while True:
                try:
                    data, addr = server.recvfrom(512)
                    response = self.handle_query(data, addr)
                    if response:
                        server.sendto(response, addr)
                except Exception as e:
                    logger.error(f"Error processing request: {str(e)}")
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Failed to start DNS server: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        finally:
            server.close()

if __name__ == '__main__':
    try:
        server = DNSServer()
        server.start()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        raise 