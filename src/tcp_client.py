#!/usr/bin/env python3
import socket
import random
import time
import string
import sys

def generate_random_message():
    """Generează un mesaj aleatoriu"""
    length = random.randint(10, 50)
    return f"[CLIENT] {''.join(random.choices(string.ascii_letters + string.digits, k=length))}"

def start_client():
    """Pornește clientul TCP"""
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Conectare la server
            client.connect(('198.7.0.2', 8081))
            print("Conectat la server", flush=True)
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
                    print("Serverul s-a deconectat", flush=True)
                    sys.stdout.flush()
                    break
                print(f"Am primit: {data.decode()}", flush=True)
                sys.stdout.flush()
                
                time.sleep(2)  # Așteaptă 2 secunde între mesaje
                
        except ConnectionRefusedError:
            print("Nu s-a putut conecta la server. Reîncercare în 5 secunde...", flush=True)
            sys.stdout.flush()
            time.sleep(5)
        except ConnectionResetError:
            print("Conexiunea a fost resetată de server", flush=True)
            sys.stdout.flush()
            time.sleep(2)
        except Exception as e:
            print(f"Eroare: {e}", flush=True)
            sys.stdout.flush()
            time.sleep(2)
        finally:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    start_client()
