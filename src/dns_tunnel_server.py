import socket
import struct
import logging
import os
import json
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dns_tunnel_server.log"),
        logging.StreamHandler()
    ]
)

class DNSTunnelServer:
    def __init__(self, host='0.0.0.0', port=53):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.chunk_size = 100  # Maximum size of each chunk in bytes
        self.transfer_state = {}  # Track transfer state for each client
        self.base_dir = Path("files")  # Directory to store files
        self.base_dir.mkdir(exist_ok=True)
        logging.info(f"DNS Tunnel Server listening on {self.host}:{self.port}")

    def parse_dns_query(self, data):
        try:
            # Extract the query name from the DNS packet
            offset = 12
            name = []
            while True:
                length = data[offset]
                if length == 0:
                    break
                offset += 1
                name.append(data[offset:offset + length].decode('utf-8'))
                offset += length
            query_name = '.'.join(name)
            
            # Extract sequence number if present
            seq_num = None
            if query_name.startswith('seq-'):
                try:
                    seq_num = int(query_name.split('-')[1])
                    query_name = '-'.join(query_name.split('-')[2:])
                except (IndexError, ValueError):
                    pass
                    
            return query_name, seq_num
        except Exception as e:
            logging.error(f"Error parsing DNS query: {e}")
            return None, None

    def create_dns_response(self, query_name, data, seq_num=None, is_ack=False):
        try:
            # DNS header (12 bytes)
            header = struct.pack('!HHHHHH', 0x8180, 1, 1, 0, 0, 0)
            
            # Query section
            query_parts = query_name.split('.')
            query = b''
            for part in query_parts:
                query += struct.pack('!B', len(part)) + part.encode('utf-8')
            query += b'\x00'
            query += struct.pack('!HH', 16, 1)  # Type TXT, Class IN
            
            # Answer section
            answer = struct.pack('!H', 0xC000 | 12)  # Name pointer
            answer += struct.pack('!HHIH', 16, 1, 300, len(data) + 1)
            
            # Add sequence number and ACK flag if present
            if seq_num is not None:
                data = struct.pack('!B', 1 if is_ack else 0) + struct.pack('!I', seq_num) + data
            
            answer += struct.pack('!B', len(data)) + data
            response = header + query + answer
            logging.info(f"Created DNS response with TXT data length: {len(data)}")
            return response
        except Exception as e:
            logging.error(f"Error creating DNS response: {e}")
            return None

    def get_file_chunk(self, filename, chunk_num, client_id):
        try:
            file_path = self.base_dir / filename
            if not file_path.exists():
                logging.error(f"File not found: {filename}")
                return None
                
            with open(file_path, 'rb') as f:
                f.seek((chunk_num - 1) * self.chunk_size)
                chunk = f.read(self.chunk_size)
                
            if not chunk:
                return None
                
            # Update transfer state
            if client_id not in self.transfer_state:
                self.transfer_state[client_id] = {
                    'filename': filename,
                    'last_chunk': chunk_num,
                    'total_chunks': (os.path.getsize(file_path) + self.chunk_size - 1) // self.chunk_size
                }
            else:
                self.transfer_state[client_id]['last_chunk'] = chunk_num
                
            return chunk
        except Exception as e:
            logging.error(f"Error reading file chunk: {e}")
            return None

    def handle_file_request(self, query_name, seq_num, client_addr):
        try:
            parts = query_name.split('.')
            if len(parts) < 3:
                logging.error(f"Invalid query format: {query_name}")
                return None, None
                
            # Handle ACK requests
            if query_name.startswith('ack-'):
                client_id = f"{client_addr[0]}:{client_addr[1]}"
                if client_id in self.transfer_state:
                    return b'ACK', True
                return None, None
                
            # Handle normal file requests
            chunk_info = parts[0].split('-')
            if len(chunk_info) != 3 or chunk_info[0] != 'chunk':
                logging.error(f"Invalid chunk format: {parts[0]}")
                return None, None
                
            chunk_num = int(chunk_info[1])
            filename = chunk_info[2]
            client_id = f"{client_addr[0]}:{client_addr[1]}"
            
            chunk_data = self.get_file_chunk(filename, chunk_num, client_id)
            if chunk_data:
                logging.info(f"Preparing TXT data for chunk {chunk_num} of {filename}")
                return chunk_data, False
            return None, None
        except Exception as e:
            logging.error(f"Error handling file request: {e}")
            return None, None

    def start(self):
        logging.info("DNS Tunnel Server started and waiting for queries...")
        while True:
            try:
                data, addr = self.sock.recvfrom(512)
                logging.info(f"Received UDP packet from {addr}")
                query_name, seq_num = self.parse_dns_query(data)
                
                if query_name:
                    logging.info(f"Received query for: {query_name}")
                    response_data, is_ack = self.handle_file_request(query_name, seq_num, addr)
                    
                    if response_data:
                        response = self.create_dns_response(query_name, response_data, seq_num, is_ack)
                        if response:
                            logging.debug(f"DNS response hex: {response.hex()}")
                            self.sock.sendto(response, addr)
                            logging.info(f"Sent response for: {query_name}")
            except Exception as e:
                logging.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    server = DNSTunnelServer()
    server.start() 