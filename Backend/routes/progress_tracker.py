import threading
import time
from flask_socketio import socketio

progress_thread = None
thread_lock = threading.Lock()

def start_progress_tracking():
    global progress_thread
    if not progress_thread or not progress_thread.is_alive():
        print("Starting progress tracking thread...")  # Debugging
        progress_thread = threading.Thread(target=background_progress_tracking)
        progress_thread.daemon = True  # Allow thread to exit when main program exits
        progress_thread.start()
    else:
        print("Progress tracking thread is already running.")  # Debugging

def background_progress_tracking():
    """Example background function to track file progress."""
    while True:
        time.sleep(10)  # Simulate periodic updates
        socketio.emit("progress_update", {"message": "Tracking progress..."})