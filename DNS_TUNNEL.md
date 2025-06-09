# DNS_TUNNEL

A simple DNS tunnel implementation in Python for educational purposes. This project demonstrates how to transfer data (such as files) over DNS queries and responses using TXT records, inspired by real-world DNS tunneling tools.

---

## Features
- Custom DNS server that responds to TXT queries with file chunks
- Client that requests file chunks and reconstructs the file
- Logging for both server and client
- Designed for local testing and learning about DNS tunneling

---

## 1. Prerequisites
- **Python 3**
- **Root/Administrator access** (to bind to port 53)
- (Optional) Linux for easiest port 53 binding

---

## 2. Setup
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. How It Works
- The server listens for DNS queries on UDP port 53.
- The client sends DNS queries for file chunks (e.g., `chunk-1-filename.domain`).
- The server responds with a DNS TXT record containing the requested chunk.
- The client reconstructs the file from the received chunks.

---

## 4. Usage

### Start the DNS Tunnel Server
```bash
sudo python3 src/dns_tunnel_server.py
```
- The server will log queries and responses to `dns_tunnel_server.log`.

### Run the DNS Tunnel Client
```bash
python3 src/dns_tunnel_client.py
```
- By default, the client requests 5 chunks of `example.txt` from the server.
- The received file will be saved as `example.txt` in the current directory.

---

## 5. Testing

### Check File Content
After running the client, check the file:
```bash
cat example.txt
```
You should see:
```
Chunk 1 of exampleChunk 2 of exampleChunk 3 of exampleChunk 4 of exampleChunk 5 of example
```

### Verify MD5 Checksum
```bash
md5sum example.txt
```
- The checksum should match the one printed by the client.

### Logs
- **Server log:** `dns_tunnel_server.log` (shows queries, responses, and hex dumps)
- **Client output:** Shows each chunk received and the final checksum

---

## 6. Customization
- To transfer a real file, update the server's `handle_file_request` method to read and send actual file chunks.
- Adjust the number of chunks and file name in the client as needed.

---

## 7. Troubleshooting
- If you see `OSError: [Errno 98] Address already in use`, make sure no other process is using port 53:
  ```bash
  sudo lsof -i :53
  sudo kill <PID>
  ```
- Run the server with `sudo` to bind to port 53.
- Make sure your firewall allows UDP traffic on port 53 for remote testing.

---

## 8. Security Warning
**Do not use this code for malicious purposes or on networks you do not own or have permission to test. DNS tunneling can be detected and is often blocked by network administrators.**

---

## 9. References
- [DNS Tunneling Explained](https://dnstunnel.de/)
- [Python DNS Packet Structure](https://github.com/senisioi/computer-networks/tree/2023/capitolul6#scapy_dns)
- [Real-world DNS tunnel tools: iodine, dnstt, OzymanDNS] 