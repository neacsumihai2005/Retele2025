#!/usr/bin/env python3
import socket
import time
import json
import requests
import matplotlib.pyplot as plt
import folium
from datetime import datetime
import os
import sys
from typing import List, Dict, Tuple, Optional

class Traceroute:
    def __init__(self, max_hops: int = 30, timeout: float = 3.0):
        self.max_hops = max_hops
        self.timeout = timeout
        self.udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.icmp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.icmp_recv_socket.settimeout(timeout)
        
    def get_geolocation(self, ip: str) -> Dict:
        """Get geolocation information for an IP address using ip-api.com"""
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'ip': ip,
                        'country': data.get('country', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon')
                    }
        except Exception as e:
            print(f"Error getting geolocation for {ip}: {e}")
        return {'ip': ip, 'country': 'Unknown', 'region': 'Unknown', 'city': 'Unknown'}

    def trace(self, target: str, port: int = 33434) -> List[Dict]:
        """Perform traceroute to target and return list of hops with geolocation info"""
        try:
            target_ip = socket.gethostbyname(target)
        except socket.gaierror:
            print(f"Could not resolve hostname: {target}")
            return []

        print(f"\nTracing route to {target} [{target_ip}]")
        print("over a maximum of {self.max_hops} hops:\n")
        
        hops = []
        
        for ttl in range(1, self.max_hops + 1):
            self.udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            
            start_time = time.time()
            self.udp_send_sock.sendto(b'', (target_ip, port))
            
            try:
                data, addr = self.icmp_recv_socket.recvfrom(1024)
                hop_time = (time.time() - start_time) * 1000
                
                hop_ip = addr[0]
                geo_info = self.get_geolocation(hop_ip)
                geo_info['hop'] = ttl
                geo_info['time'] = round(hop_time, 2)
                hops.append(geo_info)
                
                print(f"{ttl:2d}  {hop_time:6.2f} ms  {hop_ip:15s}  {geo_info['city']}, {geo_info['region']}, {geo_info['country']}")
                
                if hop_ip == target_ip:
                    break
                    
            except socket.timeout:
                print(f"{ttl:2d}  *")
                continue
            except Exception as e:
                print(f"Error at hop {ttl}: {e}")
                continue
                
        return hops

    def save_results(self, hops: List[Dict], target: str, location: str):
        """Save traceroute results to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"traceroute_{target.replace('.', '_')}_{location}_{timestamp}.json"
        
        results = {
            'target': target,
            'location': location,
            'timestamp': timestamp,
            'hops': hops
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {filename}")
        return filename

    def visualize_route(self, hops: List[Dict], target: str, output_file: str):
        """Create a map visualization of the route"""
        # Create a map centered on the first hop
        if not hops or not hops[0].get('lat') or not hops[0].get('lon'):
            print("No valid coordinates for visualization")
            return
            
        m = folium.Map(location=[hops[0]['lat'], hops[0]['lon']], zoom_start=4)
        
        # Add markers for each hop
        for i, hop in enumerate(hops):
            if hop.get('lat') and hop.get('lon'):
                popup_text = f"Hop {hop['hop']}: {hop['ip']}<br>{hop['city']}, {hop['region']}, {hop['country']}"
                folium.Marker(
                    [hop['lat'], hop['lon']],
                    popup=popup_text,
                    tooltip=f"Hop {hop['hop']}"
                ).add_to(m)
        
        # Draw lines between hops
        coordinates = [(hop['lat'], hop['lon']) for hop in hops if hop.get('lat') and hop.get('lon')]
        folium.PolyLine(
            coordinates,
            weight=2,
            color='red',
            opacity=0.8
        ).add_to(m)
        
        # Save the map
        m.save(output_file)
        print(f"Map saved to {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 traceroute.py <target> [location]")
        sys.exit(1)
        
    target = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    
    tracer = Traceroute()
    hops = tracer.trace(target)
    
    if hops:
        # Save results
        json_file = tracer.save_results(hops, target, location)
        
        # Create visualization
        map_file = json_file.replace('.json', '.html')
        tracer.visualize_route(hops, target, map_file)

if __name__ == "__main__":
    main()

'''
 Exercitiu hackney carriage (optional)!
    e posibil ca ipinfo sa raspunda cu status code 429 Too Many Requests
    cititi despre campul X-Forwarded-For din antetul HTTP
        https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/
    si setati-l o valoare in asa fel incat
    sa puteti trece peste sistemul care limiteaza numarul de cereri/zi

    Alternativ, puteti folosi ip-api (documentatie: https://ip-api.com/docs/api:json).
    Acesta permite trimiterea a 45 de query-uri de geolocare pe minut.
'''

# exemplu de request la IP info pentru a
# obtine informatii despre localizarea unui IP
fake_HTTP_header = {
                    'referer': 'https://ipinfo.io/',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
                   }
# informatiile despre ip-ul 193.226.51.6 pe ipinfo.io
# https://ipinfo.io/193.226.51.6 e echivalent cu
raspuns = requests.get('https://ipinfo.io/widget/193.226.51.6', headers=fake_HTTP_header)
print (raspuns.json())

# pentru un IP rezervat retelei locale da bogon=True
raspuns = requests.get('https://ipinfo.io/widget/10.0.0.1', headers=fake_HTTP_header)
print (raspuns.json())

