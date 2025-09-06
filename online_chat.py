import socket
import threading
import sys
from getpass import getpass

# ====================== CONFIG ======================
PORT = 54321  # Chat server port
PASSWORD = "1234"  # Change this before sharing

# ====================== SERVER ======================
clients = []
usernames = {}

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message.encode())
            except:
                pass

def handle_client(conn, addr, server_password):
    try:
        # Ask client for password
        conn.send("PASSWORD:".encode())
        pw = conn.recv(1024).decode()
        if pw != server_password:
            conn.send("❌ Wrong password. Disconnecting.".encode())
            conn.close()
            return

        # Ask for username
        conn.send("USERNAME:".encode())
        username = conn.recv(1024).decode()
        usernames[conn] = username
        clients.append(conn)
        broadcast(f"[JOIN] {username} joined the chat")
        broadcast_user_list()

        while True:
            msg = conn.recv(4096).decode()
            if not msg or msg.lower() == "exit":
                break
            broadcast(f"{username}: {msg}", conn)
    except:
        pass
    finally:
        clients.remove(conn)
        broadcast(f"[LEAVE] {usernames.get(conn, 'Unknown')} left the chat")
        broadcast_user_list()
        conn.close()

def broadcast_user_list():
    user_list = ", ".join(usernames.values())
    broadcast(f"[USERS] {user_list}")

def run_server(server_password=PASSWORD):
    host = "0.0.0.0"  # Listen on all interfaces
    print(f"✅ Server running on {host}:{PORT}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, PORT))
    server.listen(5)

    def accept_clients():
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr, server_password), daemon=True).start()

    threading.Thread(target=accept_clients, daemon=True).start()

    # Server input loop
    while True:
        cmd = input()
        if cmd.lower() == "exit":
            print("Shutting down server...")
            for c in clients:
                try:
                    c.send("Server is shutting down.".encode())
                    c.close()
                except:
                    pass
            server.close()
            break
        else:
            broadcast(f"[SERVER]: {cmd}")

# ====================== CLIENT ======================
def run_client():
    host = input("Enter server IP / domain: ")
    username = input("Enter your username: ")
    password = getpass("Enter server password: ")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, PORT))
    except:
        print("❌ Could not connect to server.")
        return

    # Receive password prompt
    prompt = client.recv(1024).decode()
    if "PASSWORD" in prompt:
        client.send(password.encode())
    # Receive username prompt
    prompt = client.recv(1024).decode()
    if "USERNAME" in prompt:
        client.send(username.encode())

    print("✅ Connected to server! Type 'exit' to leave.\n")

    def receive_messages():
        while True:
            try:
                msg = client.recv(4096).decode()
                if not msg:
                    break
                print(msg)
            except:
                break

    threading.Thread(target=receive_messages, daemon=True).start()

    while True:
        msg = input()
        if msg.lower() == "exit":
            client.send("exit".encode())
            client.close()
            break
        client.send(msg.encode())

# ====================== MAIN ======================
def main():
    print("=== Online Chat ===")
    print("1. Start Server")
    print("2. Connect as Client")
    choice = input("Choose an option: ")
    if choice == "1":
        new_password = getpass("Set server password (default is 1234): ")
        if new_password.strip() != "":
            run_server(new_password)
        else:
            run_server()
    elif choice == "2":
        run_client()
    else:
        print("Invalid choice")

# ====================== ENTRY ======================
if __name__ == "__main__":
    main()
