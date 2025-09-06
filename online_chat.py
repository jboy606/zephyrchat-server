import os
import socket
import threading
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# ================= Configuration =================
MODE = os.getenv("CHAT_MODE", "server")  # "server" or "client"
PASSWORD = os.getenv("CHAT_PASSWORD", "1234")
USERNAME = os.getenv("CHAT_USERNAME", "Guest")
HOST = os.getenv("CHAT_HOST", "127.0.0.1")  # Server IP for client
PORT = int(os.getenv("CHAT_PORT", 54321))
# ================================================

# AES Encryption helpers
def pad(s):
    return s + (16 - len(s) % 16) * " "

def encrypt(msg, key):
    cipher = AES.new(key, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(msg).encode())).decode()

def decrypt(msg, key):
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(base64.b64decode(msg)).decode().rstrip()

key = pad(PASSWORD)[:16].encode()  # 16-byte AES key

# ================= Server =================
def run_server():
    clients = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)
    print(f"✅ Server running on 0.0.0.0:{PORT}")

    def handle_client(conn, addr):
        try:
            name = decrypt(conn.recv(1024).decode(), key)
            welcome = f"{name} joined the chat."
            broadcast(welcome, conn)
            while True:
                msg = conn.recv(4096).decode()
                if not msg:
                    break
                broadcast(decrypt(msg, key), conn)
        except:
            pass
        finally:
            conn.close()
            clients.remove(conn)

    def broadcast(message, sender=None):
        for c in clients:
            if c != sender:
                try:
                    c.send(encrypt(message, key).encode())
                except:
                    pass

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ================= Client =================
def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    client.send(encrypt(USERNAME, key).encode())

    def receive():
        while True:
            try:
                msg = decrypt(client.recv(4096).decode(), key)
                print(msg)
            except:
                break

    threading.Thread(target=receive, daemon=True).start()

    while True:
        msg = input()  # Only used for local clients
        if msg.lower() == "exit":
            break
        client.send(encrypt(msg, key).encode())

# ================= Main =================
if __name__ == "__main__":
    if MODE.lower() == "server":
        run_server()
    elif MODE.lower() == "client":
        run_client()
    else:
        print("Invalid MODE! Set CHAT_MODE=server or client.")
