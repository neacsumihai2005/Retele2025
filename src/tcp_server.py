#!/usr/bin/env python3
import socket
import random
import time
import string
import sys

def generate_random_message():
    """Generează un mesaj aleatoriu"""
    length = random.randint(10, 50)
    return f"[SERVER] {''.join(random.choices(string.ascii_letters + string.digits, k=length))}"

def start_server():
    """Pornește serverul TCP"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8081))
    server.listen(1)
    print("Serverul așteaptă conexiuni...", flush=True)
    sys.stdout.flush()
    
    while True:
        try:
            client, addr = server.accept()
            print(f"Conexiune acceptată de la {addr}", flush=True)
            sys.stdout.flush()
            
            while True:
                # Trimite mesaj aleatoriu
                message = generate_random_message()
                print(f"Trimit: {message}", flush=True)
                sys.stdout.flush()
                client.send(message.encode())
                
                # Primește mesaj
                data = client.recv(1024)
                if not data:
                    print("Clientul s-a deconectat", flush=True)
                    sys.stdout.flush()
                    break
                print(f"Am primit: {data.decode()}", flush=True)
                sys.stdout.flush()
                
                time.sleep(2)  # Așteaptă 2 secunde între mesaje
                
        except ConnectionResetError:
            print("Conexiunea a fost resetată de client", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"Eroare: {e}", flush=True)
            sys.stdout.flush()
        finally:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    start_server()
