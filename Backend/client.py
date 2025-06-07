import socket

HOST = '127.0.0.1'
PORT = 5555

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"Connected to chat server at {HOST}:{PORT}")

        while True:
            msg = input("You: ")
            if msg.lower() == 'exit':
                break
            client.sendall(msg.encode())

            data = client.recv(1024)
            if not data:
                break
            print(f"Received: {data.decode()}")

if __name__ == "__main__":
    start_client()
