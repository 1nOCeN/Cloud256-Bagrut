import socket
import threading
import json
from Notify import notification_manager

class ProgressSocketServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.clients = []  # List of tuples (client_socket, username)
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.running = True
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()

    def run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            print(f"[ProgressSocket] Server running on {self.host}:{self.port}")
            while self.running:
                try:
                    client, addr = server.accept()
                    print(f"[ProgressSocket] Connection from {addr}")
                    # Set a small timeout for handshake to prevent hanging
                    client.settimeout(5)
                    try:
                        data = client.recv(1024).decode()
                        user_info = json.loads(data)
                        username = user_info.get("username")
                        if username:
                            with self.lock:
                                self.clients.append((client, username))
                            print(f"[ProgressSocket] New client connected: {username}")
                            # Remove timeout after handshake
                            client.settimeout(None)
                        else:
                            print("[ProgressSocket] No username received, closing connection.")
                            client.close()
                    except Exception as e:
                        print(f"[ProgressSocket] Error during handshake: {e}")
                        client.close()
                except Exception as e:
                    print(f"[ProgressSocket] Error accepting connection: {e}")

    def notify_upload_complete(self, username, filename):
        message = json.dumps({
            "event": "upload_complete",
            "filename": filename
        })
        print(f"Notification added for {username}: {filename}")
        notification_manager.add_notification(username, filename)

        disconnected = []
        with self.lock:
            for client, user in self.clients:
                if user == username:
                    try:
                        client.sendall(message.encode())
                        print(f"[ProgressSocket] Sent upload_complete to {username}")
                    except Exception as e:
                        print(f"[ProgressSocket] Error sending to {username}: {e}")
                        disconnected.append((client, user))
            # Remove disconnected clients
            for dc in disconnected:
                self.clients.remove(dc)

    def stop(self):
        self.running = False
        with self.lock:
            for client, _ in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        print("[ProgressSocket] Server stopped")
