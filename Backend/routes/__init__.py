# Backend/__init__.py
import os
import secrets
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import time

# Create Flask application
app = Flask(__name__,
    template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates",
    static_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\static"
)

# Configure application
SECRET_KEY = secrets.token_hex(32)
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"

# Network share for storage
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Basic file constraints
ALLOWED_EXTENSIONS = {"png", 'jpg', "jpeg", "gif", 'pdf', "txt", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Helper function
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Progress tracking
progress_thread = None
thread_lock = threading.Lock()

def background_progress_tracking():
    """Example background function to track file progress."""
    while True:
        time.sleep(10)  # Simulate periodic updates
        socketio.emit("progress_update", {"message": "Tracking progress..."})

def start_progress_tracking():
    global progress_thread
    if not progress_thread or not progress_thread.is_alive():
        print("Starting progress tracking thread...")  # Debugging
        progress_thread = threading.Thread(target=background_progress_tracking)
        progress_thread.daemon = True  # Allow thread to exit when main program exits
        progress_thread.start()
    else:
        print("Progress tracking thread is already running.")  # Debugging