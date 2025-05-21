from flask import render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
from Backend import app, allowed_file
from Backend.db import get_all_users
from Backend.encryption import encrypt_file
from progress_tracker import start_progress_tracking
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from Backend.db import get_encryption_key_from_db, store_encryption_key_to_db

def generate_aes_key():
    return os.urandom(32)  # AES-256

def get_encryption_key():
    key = get_encryption_key_from_db()
    if key:
        return base64.b64decode(key)  # decode from base64 string
    else:
        key = generate_aes_key()
        store_encryption_key_to_db(base64.b64encode(key).decode())  # encode to base64 string
        return key

encryption_key = generate_aes_key()

def encrypt_file(file_path):
    key = encryption_key  # Consider calling get_encryption_key() here
    nonce = os.urandom(12)  # GCM nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as f:
        data = f.read()

    encrypted = encryptor.update(data) + encryptor.finalize()

    with open(file_path + ".enc", "wb") as f:
        f.write(nonce + encryptor.tag + encrypted)  # prepend nonce + tag

    return file_path + ".enc"


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
        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        # Extract nonce (12 bytes), tag (16 bytes), and ciphertext
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

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
            return f"File type not allowed. Allowed types: {', '.join(app.config['ALLOWED_EXTENSIONS'])}", 400

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

@app.route("/download/<filename>")
def download_file(filename):
    username = session.get("username")
    if not username:
        return "Unauthorized", 403

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    encrypted_file_path = os.path.join(user_folder, filename)

    if not os.path.exists(encrypted_file_path):
        return "File not found", 404

    try:
        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

        decrypted_file = BytesIO(decrypted_data)
        decrypted_file.seek(0)

        return send_file(
            decrypted_file,
            as_attachment=True,
            download_name=filename.replace(".enc", ""),
            mimetype="application/octet-stream"
        )
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

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
