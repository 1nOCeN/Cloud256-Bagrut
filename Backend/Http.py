from operator import index

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, add_file_access_request, get_pending_requests, get_all_users
import os, time, websocket, requests
from flask_socketio import SocketIO, join_room

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
    return redirect("login")


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

        if get_user_by_email(email):
            return "Email already exists.", 400

        if add_user(email, username, password):
            return redirect(url_for("login"))
        else:
            return "Error registering user. Please try again.", 500

    return render_template("signup.html")

@app.route("/request_access", methods=["POST"])
def request_file_access():
    selected_user = request.form.get("user")  # The username of the owner
    filename = request.form.get("filename")  # The file the user wants access to
    requesting_user = session.get("username")  # The current user making the request

    if not requesting_user:
        return "Unauthorized", 403

    # Add the file access request to the database
    success = add_file_access_request(requesting_user, selected_user, filename)
    if success:
        # Notify the selected user (the owner) that they have a new request
        socketio.emit('file_request', {
            'from': requesting_user,
            'filename': filename
        }, room=selected_user)  # Send the notification to the selected user
        return "Request sent successfully"
    else:
        return "Error sending request", 500

@app.route("/pending_requests")
def pending_requests():
    owner = session.get("username")
    if not owner:
        return "Unauthorized", 403

    # Fetch all pending requests for this owner
    requests = get_pending_requests(owner)
    return render_template("pending_requests.html", requests=requests)

@socketio.on("connect")
def handle_connect():
    username = session.get("username")
    if username:
        join_room(username)

@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        # File upload logic goes here
        return upload_file()  # Call your existing upload_file function here

    return render_template("upload.html")  # Serve the upload page with form


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400  # Return a valid response if no file is selected

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400  # Handle the case where file is empty

    # Continue with file handling
    filename = secure_filename(file.filename)
    username = session.get("username", "guest")
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, filename)

    file.save(file_path)

    # Return a valid response after uploading the file
    return redirect(url_for("main_program", username=username))  # Redirect to the main program page


@app.route("/mainprogram", methods=["GET", "POST"])
def main_program():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    files = os.listdir(user_folder)  # Get the user's uploaded files
    users = get_all_users(username)  # Fetch all users except the logged-in user

    selected_user = request.form.get("user")  # Check if a user is selected
    selected_user_files = []

    if selected_user:
        selected_user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], selected_user)
        os.makedirs(selected_user_folder, exist_ok=True)
        selected_user_files = os.listdir(selected_user_folder)  # Get files for the selected user

    return render_template("Mainprogram.html",
                           files=files,
                           users=users,
                           selected_user=selected_user,
                           selected_user_files=selected_user_files)


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
    # Start one Flask app for the user
    from threading import Thread
    def run_user():
        app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)  # Flask instance for user

    # Start another Flask app for the owner
    def run_owner():
        app.run(host="127.0.0.1", port=5001, debug=True, use_reloader=False)  # Flask instance for owner

    # Running both on different ports
    user_thread = Thread(target=run_user)
    owner_thread = Thread(target=run_owner)

    user_thread.start()
    owner_thread.start()

