import base64
import  threading, time, os, secrets
from flask import Flask, send_from_directory, send_file, jsonify
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, get_encryption_key_from_db, store_encryption_key_to_db, get_all_users, \
    login_user, token_required, generate_api_token, store_api_token, get_api_token_from_db
from flask_socketio import SocketIO, join_room, emit
from io import BytesIO
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


# Hardcoded paths - typical in dev environments
app = Flask(__name__, template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates", static_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\static"
)
socketio = SocketIO(app, cors_allowed_origins="*")

SECRET_KEY = secrets.token_hex(32)
# Simple secret key - not production quality but works
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"

# Network share for storage
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

def start_progress_tracking():
    global progress_thread
    if not progress_thread or not progress_thread.is_alive():
        print("Starting progress tracking thread...")  # Debugging
        progress_thread = threading.Thread(target=background_progress_tracking)
        progress_thread.daemon = True  # Allow thread to exit when main program exits
        progress_thread.start()
    else:
        print("Progress tracking thread is already running.")  # Debugging


progress_thread = None
thread_lock = threading.Lock()

@socketio.on("connect")
def start_thread():
    global progress_thread
    with thread_lock:
        if progress_thread is None or not progress_thread.is_alive():
            progress_thread = threading.Thread(target=background_progress_tracking)
            progress_thread.daemon = True
            progress_thread.start()

def background_progress_tracking():
    """Example background function to track file progress."""
    while True:
        time.sleep(10)  # Simulate periodic updates
        socketio.emit("progress_update", {"message": "Tracking progress..."})

@app.route("/api/get-token", methods=["GET"])
@token_required  # Ensure user authentication
def get_user_token(user):
    return {"api_token": user["api_token"]}


@app.route("/api/my-files", methods=["GET"])
@token_required
def api_get_my_files(user):
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], user["username"])

    if not os.path.exists(user_folder):
        return {"files": []}  # Return empty if no files found

    files = [f for f in os.listdir(user_folder) if f.endswith('.enc')]
    return {"files": files}

# Encryption key generation (should be stored securely and reused)
def generate_aes_key():
        return os.urandom(32)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Store this key securely (for simplicity, using this here)
encryption_key = generate_aes_key()

def get_encryption_key():
    key = get_encryption_key_from_db()
    if key:
        # Decrypt AES key using RSA private key
        encrypted_key = base64.b64decode(key)
        aes_key = rsa_private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        return aes_key
    else:
        aes_key = generate_aes_key()

        # Encrypt AES key with RSA public key before storing
        encrypted_key = rsa_public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        store_encryption_key_to_db(base64.b64encode(encrypted_key).decode())
        return aes_key


def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Save private key
    with open("private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Save public key
    with open("public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def load_rsa_keys():
    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open("public_key.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    return private_key, public_key

rsa_private_key, rsa_public_key = load_rsa_keys()

def encrypt_file(file_path):
    key = encryption_key
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as f:
        data = f.read()

    encrypted = encryptor.update(data) + encryptor.finalize()

    with open(file_path + ".enc", "wb") as f:
        f.write(nonce + encryptor.tag + encrypted)  # prepend nonce and tag

    return file_path + ".enc"


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

@app.route("/index")
def index():
    return render_template("index.html")

from flask import redirect, url_for, session, request, render_template

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
            return redirect(url_for("login"))  # Redirect back if missing credentials

        # Check credentials
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            # Save user details in session
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            # Retrieve the API token from the database
            token = get_api_token_from_db(user["id"])

            # If no token exists in the DB, handle this scenario (e.g., generate a new token or handle it accordingly)
            if not token:
                # Optionally generate a new token here and store it in the DB if it's missing
                token = generate_api_token(user["id"])
                store_api_token(user["id"], token)

            # Redirect to the main program
            return redirect(url_for("main_program"))

        # Auth failed
        error_msg = "Invalid email or password"

    return render_template("Login.html", error=error_msg)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    # Get form data
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")

    # Validation
    if not email or not username or not password:
        return "All fields are required.", 400

    if "@" not in email or "." not in email:
        return "Invalid email format", 400

    if get_user_by_email(email):
        return "Email already exists.", 400

    if len(password) < 8:
        return "Password must be at least 8 characters", 400

    # Create user and get API token
    api_token = add_user(email, username, password)

    if api_token:
        return jsonify({"message": "Registration successful", "token": api_token})

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


@socketio.on('connect')
def handle_connect():
    username = session.get("username")
    if username:
        join_room(f"user_{username}")
        print(f"User {username} connected and joined room user_{username}")


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

    start_progress_tracking()

    if "file" not in request.files:
        return "No file part", 400

    files = request.files.getlist("file")
    if not files:
        return "No file selected", 400

    print(f"Received files: {[file.filename for file in files]}")  # Debugging

    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    encrypted_file_paths = []
    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            return f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

        filename = secure_filename(file.filename)
        temp_file_path = os.path.join(user_folder, filename)
        try:
            file.save(temp_file_path)
            print(f"File saved to {temp_file_path}")  # Debugging
        except Exception as e:
            print(f"Error saving file: {e}")  # Debugging
            return f"Error saving file: {str(e)}", 500

        encrypted_file_path = encrypt_file(temp_file_path)
        encrypted_file_paths.append(encrypted_file_path)

        os.remove(temp_file_path)  # Removing original file after encryption

        print(f"File encrypted and saved as {encrypted_file_path}")  # Debugging

    return redirect(url_for("main_program"))


@app.route("/mainprogram")
def main_program():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    try:
        files = os.listdir(user_folder)
        files = [f for f in files if f.endswith('.enc')]  # Only list encrypted files
    except Exception as e:
        files = []

    # Check if 'show_all' is passed in the query parameters
    show_all = request.args.get("show_all", default=False, type=bool)

    if show_all:
        # Return all files if "show_all" is True
        files_to_display = files
        show_more = False  # No need for a "Show More" button
        offset = 0  # Initialize offset to 0 when showing all files
    else:
        # Handle the offset if it's passed from the frontend
        offset = request.args.get("offset", default=0, type=int)

        # Limit the files to 5 initially or based on the offset
        files_to_display = files[offset:offset + 5]
        show_more = len(files) > (offset + 5)  # Check if more files are available

    # If this is an AJAX request, return only the file list HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("file_list_partial.html", files=files_to_display, show_more=show_more, offset=offset + 5)

    users = get_all_users(username)

    return render_template(
        "Mainprogram.html",
        files=files_to_display,
        users=users,
        show_more=show_more,
        offset=offset + 5  # Increase the offset for the next request (only if not showing all files)
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
        with open(encrypted_file_path, 'rb') as f:
            # Assuming the first 16 bytes are the IV
            iv = f.read(16)
            encrypted_data = f.read()

        # Set up AES decryption
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Optional: remove padding if you used PKCS7
        from cryptography.hazmat.primitives import padding
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_data) + unpadder.finalize()

        # Serve decrypted file
        decrypted_file = BytesIO(decrypted_data)
        decrypted_file.seek(0)

        return send_file(
            decrypted_file,
            as_attachment=True,
            download_name=filename.replace(".enc", ""),
            mimetype="application/octet-stream"
        )

    except Exception as e:
        return f"Error retrieving file: {str(e)}", 500

@app.route("/send_file/<recipient>", methods=["GET", "POST"])
def send_file_to_user(recipient):
    sender = session.get("username")
    if not sender:
        return redirect(url_for("login"))

    # Prevent sending file to self
    if sender == recipient:
        return "You cannot send a file to yourself", 400

    # Check recipient exists in DB (you already have get_all_users)
    all_users = [u['username'] for u in get_all_users(sender)]
    if recipient not in all_users:
        return "Recipient user not found", 404

    if request.method == "GET":
        return render_template("send_file.html", recipient=recipient)

    # POST method - handle file upload
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    if not allowed_file(file.filename):
        return f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

    filename = secure_filename(file.filename)

    # Save file temporarily
    temp_path = os.path.join(app.config["BASE_UPLOAD_FOLDER"], "temp", filename)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    file.save(temp_path)

    # Encrypt the file
    encrypted_path = encrypt_file(temp_path)

    # Remove temp plain file
    os.remove(temp_path)

    # Move encrypted file to recipient folder
    recipient_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], recipient)
    os.makedirs(recipient_folder, exist_ok=True)
    final_path = os.path.join(recipient_folder, os.path.basename(encrypted_path))
    os.rename(encrypted_path, final_path)

    # Notify recipient via SocketIO about new file
    room = f"user_{recipient}"
    socketio.emit("new_file_received", {
        "from": sender,
        "filename": os.path.basename(final_path),
        "message": f"New file '{filename}' received from {sender}"
    }, room=room)

    return redirect(url_for("main_program"))


@app.route("/download/<filename>")
def download_file(filename):
    """Handle file download with AES decryption."""
    username = session.get("username")
    if not username:
        return "User not logged in", 403

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    encrypted_file_path = os.path.join(user_folder, filename)

    if not os.path.exists(encrypted_file_path):
        return "File not found", 404

    try:
        # Read encrypted file content
        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        # Extract nonce (12 bytes), tag (16 bytes), and ciphertext
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        # Create AES-GCM cipher
        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Create in-memory file for download
        decrypted_file = BytesIO(decrypted_data)
        decrypted_file.seek(0)

        return send_file(
            decrypted_file,
            as_attachment=True,
            download_name=filename.replace(".enc", ""),  # Clean filename
            mimetype="application/octet-stream"
        )

    except Exception as e:
        print(f"Error decrypting file: {str(e)}")
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
    socketio.run(app, host="0.0.0.0", port=port, debug=True)