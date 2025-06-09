import socket
import struct
import logging
import time
import hashlib
import os
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DNSTunnelClient:
    def __init__(self, server_ip, server_port=53, timeout=2, max_retries=3):
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout
        self.max_retries = max_retries
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.transfer_state = {}
        self.base_dir = Path("downloads")
        self.base_dir.mkdir(exist_ok=True)

    def create_dns_query(self, query_name, seq_num=None):
        try:
            # DNS header (12 bytes)
            header = struct.pack('!HHHHHH', 0x0001, 1, 0, 0, 0, 0)
            
            # Add sequence number if present
            if seq_num is not None:
                query_name = f"seq-{seq_num}-{query_name}"
            
            # Query section
            query_parts = query_name.split('.')
            query = b''
            for part in query_parts:
                query += struct.pack('!B', len(part)) + part.encode('utf-8')
            query += b'\x00'
            query += struct.pack('!HH', 16, 1)  # Type TXT, Class IN
            return header + query
        except Exception as e:
            logging.error(f"Error creating DNS query: {e}")
            return None

    def parse_dns_response(self, data):
        try:
            # Skip the DNS header (12 bytes)
            offset = 12
            # Skip the query section
            while data[offset] != 0:
                offset += data[offset] + 1
            offset += 1  # null terminator
            offset += 4  # type (2) + class (2)
            
            # Now at the answer section
            offset += 2  # name pointer
            offset += 2  # type
            offset += 2  # class
            offset += 4  # TTL
            rdlength = struct.unpack('!H', data[offset:offset+2])[0]
            offset += 2
            
            # Check if this is an ACK response
            if rdlength >= 5:  # ACK flag (1) + seq_num (4)
                is_ack = bool(data[offset])
                seq_num = struct.unpack('!I', data[offset+1:offset+5])[0]
                offset += 5
                if is_ack:
                    return None, seq_num, True
            
            # TXT record: 1 byte length, then the data
            txt_length = data[offset]
            offset += 1
            txt_data = data[offset:offset + txt_length]
            
            # Extract sequence number if present
            seq_num = None
            if txt_length >= 5:  # ACK flag (1) + seq_num (4)
                is_ack = bool(txt_data[0])
                seq_num = struct.unpack('!I', txt_data[1:5])[0]
                txt_data = txt_data[5:]
            
            logging.info(f"Received TXT data length: {len(txt_data)}")
            return txt_data, seq_num, False
        except Exception as e:
            logging.error(f"Error parsing DNS response: {e}")
            return None, None, False

    def request_file_chunk(self, chunk_num, filename, domain, seq_num=None):
        query_name = f"chunk-{chunk_num}-{filename}.{domain}"
        query = self.create_dns_query(query_name, seq_num)
        if not query:
            return None, None
        
        for retry in range(self.max_retries):
            try:
                self.sock.sendto(query, (self.server_ip, self.server_port))
                data, _ = self.sock.recvfrom(512)
                logging.debug(f"Received DNS response hex: {data.hex()}")
                chunk_data, resp_seq_num, is_ack = self.parse_dns_response(data)
                
                if is_ack:
                    # Send ACK acknowledgment
                    ack_query = self.create_dns_query(f"ack-{resp_seq_num}.{domain}")
                    self.sock.sendto(ack_query, (self.server_ip, self.server_port))
                    return None, resp_seq_num
                
                return chunk_data, resp_seq_num
            except socket.timeout:
                logging.warning(f"Timeout requesting chunk {chunk_num} (attempt {retry + 1}/{self.max_retries})")
                if retry == self.max_retries - 1:
                    return None, None
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                logging.error(f"Error requesting chunk {chunk_num}: {e}")
                return None, None

    def save_transfer_state(self, filename):
        state_file = self.base_dir / f"{filename}.state"
        with open(state_file, 'w') as f:
            json.dump(self.transfer_state, f)

    def load_transfer_state(self, filename):
        state_file = self.base_dir / f"{filename}.state"
        if state_file.exists():
            with open(state_file, 'r') as f:
                self.transfer_state = json.load(f)
            return True
        return False

    def download_file(self, filename, domain, num_chunks=None, resume=True):
        if resume and self.load_transfer_state(filename):
            logging.info(f"Resuming download of {filename} from chunk {self.transfer_state.get('last_chunk', 1)}")
            start_chunk = self.transfer_state.get('last_chunk', 1)
        else:
            start_chunk = 1
            self.transfer_state = {'last_chunk': 0, 'total_chunks': num_chunks}
        
        output_file = self.base_dir / filename
        mode = 'ab' if start_chunk > 1 else 'wb'
        
        with open(output_file, mode) as f:
            chunk_num = start_chunk
            while num_chunks is None or chunk_num <= num_chunks:
                chunk_data, seq_num = self.request_file_chunk(chunk_num, filename, domain)
                
                if chunk_data is None:
                    if seq_num is not None:
                        # This was an ACK response, continue with next chunk
                        chunk_num += 1
                        self.transfer_state['last_chunk'] = chunk_num
                        self.save_transfer_state(filename)
                        continue
                    else:
                        logging.error(f"Failed to receive chunk {chunk_num}")
                        return False
                
                f.write(chunk_data)
                logging.info(f"Received chunk {chunk_num}/{num_chunks if num_chunks else '?'}")
                
                # Update transfer state
                self.transfer_state['last_chunk'] = chunk_num
                self.save_transfer_state(filename)
                
                # If we received an empty chunk, we're done
                if len(chunk_data) == 0:
                    break
                
                chunk_num += 1
        
        # Clean up state file after successful download
        if os.path.exists(self.base_dir / f"{filename}.state"):
            os.remove(self.base_dir / f"{filename}.state")
        
        return True

    def compute_md5(self, filename):
        file_path = self.base_dir / filename
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

if __name__ == "__main__":
    client = DNSTunnelClient(server_ip='127.0.0.1')
    filename = 'example.txt'
    domain = 'tunnel-domain.live'
    num_chunks = 5
    
    if client.download_file(filename, domain, num_chunks, resume=True):
        md5 = client.compute_md5(filename)
        logging.info(f"File downloaded successfully. MD5: {md5}")
    else:
        logging.error("File download failed.") 