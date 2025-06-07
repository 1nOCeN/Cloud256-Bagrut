import os
import secrets
import threading
import time
from flask import Flask, send_from_directory
from flask_socketio import SocketIO

# Create Flask app
app = Flask(__name__,
            template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates",
            static_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\static")

# Configure app
SECRET_KEY = secrets.token_hex(32)
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"

BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", 'jpg', "jpeg", "gif", 'pdf', "txt", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Background progress tracking example
progress_thread = None

def background_progress_tracking():
    while True:
        time.sleep(10)
        socketio.emit("progress_update", {"message": "Tracking progress..."})

def start_progress_tracking():
    global progress_thread
    if not progress_thread or not progress_thread.is_alive():
        progress_thread = threading.Thread(target=background_progress_tracking, daemon=True)
        progress_thread.start()

start_progress_tracking()
