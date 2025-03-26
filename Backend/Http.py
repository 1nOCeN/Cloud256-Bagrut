from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, get_encryption_key_from_db, store_encryption_key_to_db, get_all_users
import os
from flask_socketio import SocketIO, join_room, emit
from cryptography.fernet import Fernet  # Encryption library
from io import BytesIO

# Hardcoded paths - typical in dev environments
app = Flask(__name__, template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates", static_folder= r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\static")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Simple secret key - not production quality but works
app.secret_key = "b5jT$9c!KpQw#2Ls"
app.config["SESSION_TYPE"] = "filesystem"

# Network share for storage
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Encryption key generation (should be stored securely and reused)
def generate_key():
    # In a real app, generate once and store securely
    return Fernet.generate_key()

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Store this key securely (for simplicity, using this here)
encryption_key = generate_key()
cipher_suite = Fernet(encryption_key)

def get_encryption_key():
    """Retrieve the stored encryption key or generate a new one if not found."""
    key = get_encryption_key_from_db()
    if key:
        return key.encode()  # Ensure it's in bytes format
    else:
        key = Fernet.generate_key()
        store_encryption_key_to_db(key.decode())  # Store new key
        return key

# Load encryption key
encryption_key = get_encryption_key()
cipher_suite = Fernet(encryption_key)

def encrypt_file(file_path):
    """Encrypt the file and save the encrypted version."""
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Encrypt the file data
    encrypted_data = cipher_suite.encrypt(file_data)

    # Save the encrypted file
    encrypted_file_path = file_path + ".enc" # Append .enc to encrypted file
    with open(encrypted_file_path, "wb") as f:
        f.write(encrypted_data)

    return encrypted_file_path


# Basic file constraints
ALLOWED_EXTENSIONS = {"png", 'jpg', "jpeg", "gif", 'pdf', "txt", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# Quick helper function
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    # Just redirect to login
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = None

    # Already logged in? Skip to main
    if session.get('user_id'):
        return redirect(url_for('main_program'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Basic validation
        if not email or not password:
            return "Missing email or password", 400

        # Check credentials
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main_program"))

        # Auth failed
        error_msg = "Invalid email or password"
        return "Invalid credentials", 401

    return render_template("Login.html", error=error_msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    # Get form data
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm_password")  # Not used, but kept from form

    # Quick validation
    if not email or not username or not password:
        return "All fields are required.", 400

    # Super simple email check
    if "@" not in email or "." not in email:
        return "Invalid email format", 400

    # Check for existing user
    if get_user_by_email(email):
        return "Email already exists.", 400

    # Basic password strength check
    if len(password) < 8:
        return "Password must be at least 8 characters", 400

    # Try to add user
    if add_user(email, username, password):
        return redirect(url_for("login"))
    return "Error registering user.", 500


@app.route("/start_chat/<username>", methods=["GET"])
def start_chat(username):
    current_user = session.get("username")
    # Can't chat with yourself
    if current_user == username:
        return "You can't chat with yourself", 400

    # Create a unique room id by combining usernames alphabetically
    room = f"{min(current_user, username)}_{max(current_user, username)}"
    return render_template("Chat.html", room=room, username=username)


# Socket stuff for chat
@socketio.on('connect')
def handle_connect():
    print(f'User {session["username"]} connected')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print(f'{username} has entered the room {room}')

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']

    # Debug print
    print(f"Broadcasting message from {username}: {message}")

    # Send it out to everyone in the room
    emit('receive_message', {'username': username, 'message': message}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    print(f'User {session["username"]} disconnected')


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        return render_template("upload.html")

    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    print(f"Received file: {file.filename}")  # Debugging

    if not allowed_file(file.filename):
        return f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

    filename = secure_filename(file.filename)
    username = session.get("username")

    if not username:
        return redirect(url_for("login"))

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    temp_file_path = os.path.join(user_folder, filename)
    try:
        file.save(temp_file_path)
        print(f"File saved to {temp_file_path}")  # Debugging
    except Exception as e:
        print(f"Error saving file: {e}")  # Debugging
        return f"Error saving file: {str(e)}", 500

    encrypted_file_path = encrypt_file(temp_file_path)

    os.remove(temp_file_path)  # Removing original file after encryption

    print(f"File encrypted and saved as {encrypted_file_path}")  # Debugging

    return redirect(url_for("main_program"))

@app.route("/mainprogram", methods=["GET", "POST"])
def main_program():
    # Must be logged in
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    # Setup user folder
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    # Get user's files
    try:
        files = os.listdir(user_folder)
    except Exception as e:
        files = []  # Empty if error

    # Get all other users
    users = get_all_users(username)

    # Handle viewing other user's files
    selected_user = request.form.get("user")
    selected_user_files = []

    if selected_user:
        selected_user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], selected_user)
        os.makedirs(selected_user_folder, exist_ok=True)

        try:
            selected_user_files = os.listdir(selected_user_folder)
        except Exception as e:
            selected_user_files = []

    # Sort alphabetically
    files.sort()
    selected_user_files.sort()

    # Show the main program page
    return render_template(
        "Mainprogram.html",
        files=files,
        users=users,
        selected_user=selected_user,
        selected_user_files=selected_user_files
    )

@app.route("/uploads/<filename>")
def serve_file(filename):
    username = session.get("username")
    if not username:
        return "Unauthorized", 403

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    encrypted_file_path = os.path.join(user_folder, filename)

    if not os.path.exists(encrypted_file_path):
        return "File not found", 404

    try:
        # Read and decrypt the file content
        with open(encrypted_file_path, 'rb') as f:
            encrypted_file_content = f.read()

        decrypted_file_content = cipher_suite.decrypt(encrypted_file_content)

        # Create a temporary file for download
        decrypted_file = BytesIO(decrypted_file_content)
        decrypted_file.seek(0)  # Move pointer to beginning

        return send_from_directory(user_folder, filename, as_attachment=True)

    except Exception as e:
        return f"Error retrieving file: {str(e)}", 500

def decrypt_file(encrypted_file_path):
    """Decrypt the file and save the decrypted version."""
    with open(encrypted_file_path, "rb") as f:
        encrypted_data = f.read()

    # Decrypt the file data
    decrypted_data = cipher_suite.decrypt(encrypted_data)

    # Save the decrypted file
    decrypted_file_path = encrypted_file_path.replace(".enc", "")  # Remove .enc
    with open(decrypted_file_path, "rb") as f:
        f.write(decrypted_data)
    return decrypted_file_path


@app.route("/download/<filename>")
def download_file(filename):
    """Handle file download with decryption."""
    username = session.get("username")
    if not username:
        return "User not logged in", 403

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    encrypted_file_path = os.path.join(user_folder, filename)  # Append .enc

    # Debugging
    print(f"Looking for file: {encrypted_file_path}")

    if not os.path.exists(encrypted_file_path):
        print("File not found!")
        return "File not found", 404

    try:
        # Read encrypted file
        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        # Debugging: Check file size
        print(f"Encrypted file size: {len(encrypted_data)} bytes")

        # Decrypt the content
        decrypted_data = cipher_suite.decrypt(encrypted_data)

        # Debugging: Check decrypted file size
        print(f"Decrypted file size: {len(decrypted_data)} bytes")

        # Serve as an in-memory file
        decrypted_file = BytesIO(decrypted_data)
        decrypted_file.seek(0)

        return send_file(
            decrypted_file,
            as_attachment=True,
            download_name=filename.replace(".enc", ""),  # Remove .enc from the filename
            mimetype="application/octet-stream"
        )

    except Exception as e:
        print(f"Error decrypting file: {str(e)}")  # Debugging
        return f"Error retrieving file: {str(e)}", 500




@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    username = session.get("username")
    if not username:
        return "User not logged in", 403

    file_path = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username, filename)

    # Try to delete
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            return f"Error deleting file: {str(e)}", 500

        return redirect(url_for("main_program"))

    return "File not found", 404

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(500)
def server_error(e):
    return "Server error, please try again later", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
