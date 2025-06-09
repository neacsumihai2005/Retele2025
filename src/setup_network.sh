#!/bin/bash

# Stop systemd-resolved
echo "Stopping systemd-resolved..."
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved

# Configure iptables
echo "Configuring iptables..."
sudo iptables -I INPUT 6 -p udp -m udp --dport 53 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save

# Create necessary directories
echo "Creating directories..."
mkdir -p files downloads

# Set up test file
echo "Creating test file..."
echo "This is a test file for DNS tunneling.
It contains multiple lines to test chunking.
Each line will be sent as a separate chunk.
This helps verify the reliability of the transfer.
The file should be transferred completely and correctly." > files/example.txt

echo "Network setup complete!"
echo "You can now start the DNS tunnel server with: sudo python3 src/dns_tunnel_server.py"
echo "And the client with: python3 src/dns_tunnel_client.py" 