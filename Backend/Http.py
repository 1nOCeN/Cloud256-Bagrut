from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_by_username, add_user  # Import functions from db.py


template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"  # Use your actual path here


app = Flask(__name__ , template_folder=template_folder)

app.secret_key = "your_secret_key"  # Required for session handling

# Base folder for user files
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


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


# Route: Login Page
@app.route("/")
@app.route("/login", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Check if the user exists in the database
        user = get_user_by_username(username)
        if user and user["password"] == password:
            # If credentials are correct, set session
            session["user_id"] = user["id"]
            return redirect(url_for("main_program"))
        else:
            return "Invalid credentials, please try again."

    return render_template("Login.html")


# Route: Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Add the new user to the database
        add_user(username, password)
        return redirect(url_for("login"))

    return render_template("signup.html")


# Route: Main Program (File Listing)
@app.route("/mainprogram")
def main_program():
    if "user_id" in session:
        return render_template("Mainprogram.html")
    return redirect(url_for("login"))


    username = session["username"]
    user_folder = get_user_folder(username)
    files = os.listdir(user_folder)
    return render_template("Mainprogram.html", files=files)


# Route: Upload File
@app.route("/upload", methods=["POST"])
def upload_file():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
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
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    os.makedirs(app.config["BASE_UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
