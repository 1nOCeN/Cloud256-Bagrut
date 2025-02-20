from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, get_user_by_username
import os, time, json, websocket
from flask_socketio import SocketIO

# Flask setup
template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"
app = Flask(__name__, template_folder=template_folder)
socketio = SocketIO(app, cors_allowed_origins="*")

app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_default_secret")
app.config["SESSION_TYPE"] = "filesystem"

BASE_UPLOAD_FOLDER = os.path.normpath(r"\\DESKTOP-1EOTSNC\Cloud256-Database2")
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Route: Home (redirect to login)
@app.route("/")
def home():
    return redirect(url_for("login"))


# Route: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)
        if not user:
            return "User not found.", 404

        if check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            print(f"Login successful for {email}")
            return redirect(url_for("main_program"))
        else:
            return "Invalid credentials, please try again.", 401

    return render_template("Login.html")


# Route: Register
@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        if not email or not username or not password:
            return "All fields are required.", 400

        if get_user_by_email(email) or get_user_by_username(username):
            return "Email or username already exists.", 400

        if add_user(email, username, password):
            return redirect(url_for("login"))
        else:
            return "Error registering user. Please try again.", 500

    return render_template("signup.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        # File upload logic goes here
        return upload_file()  # Call your existing upload_file function here

    return render_template("upload.html")  # Serve the upload page with form


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    filename = secure_filename(file.filename)
    username = session.get("username", "guest")
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, filename)

    total_chunks = 5
    for i in range(1, total_chunks + 1):
        time.sleep(1)  # Simulate file upload delay
        progress = int((i / total_chunks) * 100)
        socketio.emit("upload_progress", {"progress": progress, "filename": filename}, broadcast=True)

    socketio.emit("upload_complete", {"filename": filename}, broadcast=True)
    return redirect(url_for("main_program"))

sio = socketio.Client()

# Event handler for upload progress
@sio.event
def upload_progress(data):
    print(f"Upload Progress: {data['progress']}% for {data['filename']}")

# Event handler for upload completion
@sio.event
def upload_complete(data):
    print(f"Upload Complete: {data['filename']}")

# Connect to the Flask-SocketIO server
sio.connect('http://127.0.0.1:5000')

# Keep the client running to listen for events
sio.wait()

# Route: Show Uploaded Files
@app.route("/mainprogram")
def main_program():
    username = session.get("username", "guest")
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)  # Ensure folder exists

    files = os.listdir(user_folder)
    return render_template("Mainprogram.html", files=files)

@app.route("/uploads/<filename>")
def serve_file(filename):
    username = session.get("username")  # Get current user
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)

    return send_from_directory(user_folder, filename)

@app.route("/download/<filename>")
def download_file(filename):
    username = session.get("username")  # Get the logged-in user's name
    if not username:
        return "User not logged in", 403  # Unauthorized if no session

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    return send_from_directory(user_folder, filename, as_attachment=True)

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    username = session.get("username")  # Get the logged-in user's name
    if not username:
        return "User not logged in", 403  # Unauthorized if no session

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)  # User's folder
    file_path = os.path.join(user_folder, filename)  # Full file path

    if os.path.exists(file_path):
        os.remove(file_path)  # Delete the file
        return redirect(url_for("main_program"))  # Refresh the file list
    else:
        return "File not found", 404


@app.route("/logout")
def logout():
    session.clear()  # Clear user session
    return redirect(url_for("login"))  # Redirect to login page

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
