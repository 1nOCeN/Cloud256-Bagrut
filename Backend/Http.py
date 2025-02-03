from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, get_user_by_username  # Import the DB functions
import os


template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"
app = Flask(__name__, template_folder=template_folder)

app.secret_key = "your_secret_key"

# Base folder for user files
BASE_UPLOAD_FOLDER = "user_files"  # Local folder for storing user uploads
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)  # Ensure the base folder exists
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
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
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not email or not username or not password:
            return "All fields are required.", 400

        if get_user_by_email(email) or get_user_by_username(username):
            return "Email or username already exists.", 400

        if add_user(email, username, password):
            return redirect(url_for("login"))
        else:
            return "Error registering user. Please try again.", 500

    return render_template("signup.html")


# Route: Main Program (File Management)
@app.route("/mainprogram")
def main_program():
    if "user_id" in session:
        username = session["username"]
        user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
        os.makedirs(user_folder, exist_ok=True)  # Ensure user folder exists

        files = os.listdir(user_folder)
        return render_template("Mainprogram.html", files=files, username=username)

    return redirect(url_for("login"))


# Route: Upload File
@app.route("/upload", methods=["POST"])
def upload_file():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    file = request.files.get("file")
    if not file or file.filename == "":
        return "No file selected for uploading", 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(user_folder, filename))
        return redirect(url_for("main_program"))

    return "File not allowed", 400


# Route: Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
