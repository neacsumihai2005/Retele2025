# DNS Ad Blocker Setup Guide

This document explains how to set up and use the DNS Ad Blocker on your system using Docker Compose.

---

## 1. Prerequisites
- **Docker** and **Docker Compose** installed
- **Python 3** (for updating the blocklist and analyzing stats)
- Root/Administrator access (to bind to port 53)

---

## 2. Clone the Repository
```
git clone <your-repo-url>
cd <your-repo-directory>
```

---

## 3. Update the Blocklist
Download and combine the latest ad/tracker domain lists:
```
python3 src/update_blocklist.py
```
This will create or update `blocked_domains.txt`.

---

## 4. Build and Start the DNS Server
Build and run the DNS ad blocker using Docker Compose:
```
sudo docker-compose build dns-server
sudo docker-compose up -d
```

---

## 5. Set Your System DNS to 127.0.0.1
### Linux
Edit `/etc/resolv.conf` and set:
```
nameserver 127.0.0.1
```
Or use your network manager to set the DNS server to `127.0.0.1`.

### Windows
- Go to Network Connections
- Right-click your active connection > Properties
- Select "Internet Protocol Version 4 (TCP/IPv4)" > Properties
- Set Preferred DNS server to `127.0.0.1`

### macOS
- System Preferences > Network > Advanced > DNS
- Add `127.0.0.1` to the DNS servers list

---

## 6. Test the Ad Blocker
Run:
```
dig doubleclick.net @127.0.0.1
```
You should see:
```
doubleclick.net. ... IN A 0.0.0.0
```
This means the ad domain is blocked.

---

## 7. Check Blocked Requests
Blocked domains are logged in `blocked_requests.json` in your project directory.

---

## 8. Analyze Blocked Domains
To generate statistics about blocked domains and companies:
```
python3 src/analyze_stats.py
```
This will create `blocker_statistics.json` and print a summary.

---

## 9. Troubleshooting
- Make sure no other service (like `systemd-resolved`) is using port 53.
- If Docker Compose fails with port errors, stop other DNS containers or services.
- If you change the blocklist or code, rebuild the container:
  ```
  sudo docker-compose build dns-server
  sudo docker-compose up -d
  ```

---

## 10. Stopping the DNS Ad Blocker
To stop the DNS ad blocker:
```
sudo docker-compose down
```

---

## 11. Updating the Blocklist
To update the blocklist in the future:
```
python3 src/update_blocklist.py
sudo docker-compose restart dns-server
```

---

## 12. Notes
- You can edit `blocked_domains.txt` to add/remove domains manually.
- The DNS server only blocks domains in the list; all others are not resolved unless you add forwarding logic.
- For best results, keep your blocklist updated.

---

**Enjoy a cleaner, ad-free browsing experience!** 