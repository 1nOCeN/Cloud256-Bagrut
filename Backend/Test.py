import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if "progress" in data:
        print(f"Upload Progress: {data['progress']}%")
    if "filename" in data:
        print(f"Upload Complete: {data['filename']}")

ws = websocket.WebSocketApp("ws://127.0.0.1:5000/socket.io/?EIO=4&transport=websocket",
                             on_message=on_message)

ws.run_forever()
