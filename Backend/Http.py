from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_by_email, add_user  # Import functions from db.py

template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"

app = Flask(__name__, template_folder=template_folder)

app.secret_key = "your_secret_key"  # Required for session handling

# Base folder for user files
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

@app.route("/")
def home():
    return redirect(url_for("login"))


# Database connection helper
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


# Ensure user folder exists
def get_user_folder(username):
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


# Check if file is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Get user from the database by email
        user = get_user_by_email(email)

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        print("Generated Hash:", hashed_password)

        # Check the hash
        is_valid = check_password_hash(hashed_password, password)
        print("Password valid:", is_valid)

    return render_template("Login.html")






# Route: Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)  # Secure password

        # Add the new user to the database
        add_user(email, username, hashed_password)

        return redirect(url_for("login"))

    return render_template("signup.html")


# Route: Main Program (File Listing)
@app.route("/mainprogram")
def main_program():
    if "user_id" in session:
        # Fetch the username based on user_id from the database
        user_id = session["user_id"]
        conn = get_db_connection()
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()

        if user:
            username = user["username"]
            user_folder = get_user_folder(username)
            files = os.listdir(user_folder)
            return render_template("Mainprogram.html", files=files)
        else:
            return "User not found.", 404

    return redirect(url_for("login"))


# Route: Upload File
@app.route("/upload", methods=["POST"])
def upload_file():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    # Fetch the username based on user_id from the database
    conn = get_db_connection()
    user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user:
        username = user["username"]
        user_folder = get_user_folder(username)

        if "file" not in request.files:
            return "No file part in the request", 400
        file = request.files["file"]

        if file.filename == "":
            return "No file selected for uploading", 400
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(user_folder, filename))
            return redirect(url_for("main_program"))

    return "File not allowed", 400


# Route: Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    os.makedirs(app.config["BASE_UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)