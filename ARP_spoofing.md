# ARP Spoofing Implementation

## Overview
This implementation demonstrates an ARP spoofing attack in a controlled environment using Docker containers. The attack is designed for educational purposes to understand network security vulnerabilities and how to protect against them.

## Architecture
```
            MIDDLE------------\
        subnet2: 198.7.0.3     \
        MAC: 02:42:c6:0a:00:02  \
               forwarding        \ 
              /                   \
             /                     \
Poison ARP 198.7.0.1 is-at         Poison ARP 198.7.0.2 is-at 
           02:42:c6:0a:00:02         |         02:42:c6:0a:00:02
           /                         |
          /                          |
         /                           |
        /                            |
    SERVER <---------------------> ROUTER <---------------------> CLIENT
net2: 198.7.0.2                      |                           net1: 172.7.0.2
MAC: 02:42:c6:0a:00:03               |                            MAC eth0: 02:42:ac:0a:00:02
                           subnet1:  172.7.0.1
                           MAC eth0: 02:42:ac:0a:00:01
                           subnet2:  198.7.0.1
                           MAC eth1: 02:42:c6:0a:00:01
                           subnet1 <------> subnet2
                                 forwarding
```

## Prerequisites
- Docker and Docker Compose
- Python 3.x
- Scapy library (`pip install scapy`)
- Root/Administrator privileges for network operations

## Setup Instructions

1. **Build and Start Containers**
```bash
docker compose up -d
```

2. **Clear ARP Cache**
Before starting the attack, clear the ARP cache on both router and server:
```bash
# On server container
docker exec -it retele-am-team-server-1 ip -s -s neigh flush all

# On router container
docker exec -it retele-am-team-router-1 ip -s -s neigh flush all
```

3. **Install Dependencies**
```bash
pip install scapy
```

## Implementation Details

### ARP Spoofing Script (`src/arp_spoof.py`)

The script implements the following key features:

1. **ARP Spoofer Class**
   - Handles ARP packet creation and sending
   - Manages MAC address retrieval
   - Implements error handling and logging

2. **Attack Mechanism**
   - Uses threading for simultaneous attacks
   - Implements continuous ARP cache poisoning
   - Includes proper sleep intervals to avoid flooding

3. **Network Configuration**
   - Proper IP forwarding setup
   - NAT configuration with MASQUERADE
   - Interface management

### Key Components

1. **Packet Creation**
```python
arp_packet = ARP(
    op=2,  # ARP Reply
    pdst=target_ip,
    hwdst="ff:ff:ff:ff:ff:ff",
    psrc=gateway_ip,
    hwsrc=attacker_mac
)
```

2. **Threading Implementation**
```python
server_thread = threading.Thread(target=poison_server)
router_thread = threading.Thread(target=poison_router)
```

3. **Error Handling**
```python
try:
    send(arp_packet, verbose=0)
except Exception as e:
    logging.error(f"Error sending ARP packet: {e}")
```

## Usage

1. **Start the Attack**
```bash
python3 src/arp_spoof.py
```

2. **Monitor Traffic**
```bash
tcpdump -SntvXX -i any
```

3. **Test the Attack**
```bash
# In server container
wget http://old.fmi.unibuc.ro
```

## Security Considerations

1. **Educational Purpose Only**
   - This implementation is for educational purposes
   - Do not use for malicious purposes
   - Use only in controlled environments

2. **Protection Measures**
   - Static ARP entries
   - ARP monitoring tools
   - Network segmentation
   - VLAN implementation

## Troubleshooting

1. **Permission Issues**
   - Ensure root/administrator privileges
   - Check network interface permissions
   - Verify Docker container capabilities

2. **Network Issues**
   - Verify container networking
   - Check IP forwarding status
   - Confirm ARP cache clearing

3. **Script Issues**
   - Verify Scapy installation
   - Check Python version compatibility
   - Ensure proper file permissions

## References

1. [ARP Spoofing Explanation](https://samsclass.info/124/proj11/P13xN-arpspoof.html)
2. [Black Hat Python ARP Cache Poisoning](https://medium.com/@ismailakkila/black-hat-python-arp-cache-poisoning-with-scapy-7cb1d8b9d242)
3. [ARP Spoofing Video Tutorial](https://www.youtube.com/watch?v=hI9J_tnNDCc)

## License
This implementation is provided for educational purposes only. Use responsibly and ethically. 