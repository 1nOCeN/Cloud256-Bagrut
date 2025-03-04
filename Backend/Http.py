from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db import get_user_by_email, add_user, get_all_users
import os
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__, template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates")
socketio = SocketIO(app, cors_allowed_origins="*")

app.secret_key = "b5jT$9c!KpQw#2Ls"
app.config["SESSION_TYPE"] = "filesystem"

BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", 'jpg', "jpeg", "gif", 'pdf', "txt", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = None

    if session.get('user_id'):
        return redirect(url_for('main_program'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Missing email or password", 400

        user = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main_program"))

        error_msg = "Invalid email or password"
        return "Invalid credentials", 401

    return render_template("Login.html", error=error_msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm_password")

    if not email or not username or not password:
        return "All fields are required.", 400

    if "@" not in email or "." not in email:
        return "Invalid email format", 400

    if get_user_by_email(email):
        return "Email already exists.", 400

    if len(password) < 8:
        return "Password must be at least 8 characters", 400

    if add_user(email, username, password):
        return redirect(url_for("login"))
    return "Error registering user.", 500


@app.route("/start_chat/<username>", methods=["GET"])
def start_chat(username):
    current_user = session.get("username")
    if current_user == username:
        return "You can't chat with yourself", 400

    room = f"{min(current_user, username)}_{max(current_user, username)}"
    return render_template("Chat.html", room=room, username=username)


# Handle new connections
@socketio.on('connect')
def handle_connect():
    print(f'User {session["username"]} connected')

# Handle when a user joins a specific chat room
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print(f'{username} has entered the room {room}')

# Handle when a message is sent in the chat
@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']

    # Debugging log for message received on the server
    print(f"Broadcasting message from {username}: {message}")

    # Broadcast the message to the room
    emit('receive_message', {'username': username, 'message': message}, room=room)

# Handle when a user leaves the chat room
@socketio.on('disconnect')
def handle_disconnect():
    print(f'User {session["username"]} disconnected')


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        return render_template("upload.html")  # This renders the form for uploading files

    # POST logic to handle file upload
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    if not allowed_file(file.filename):
        return f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

    filename = secure_filename(file.filename)
    username = session.get("username")

    if not username:
        return redirect(url_for("login"))

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)

    os.makedirs(user_folder, exist_ok=True)

    try:
        file.save(os.path.join(user_folder, filename))
    except Exception as e:
        return f"Error saving file: {str(e)}", 500

    return redirect(url_for("main_program"))



@app.route("/mainprogram", methods=["GET", "POST"])
def main_program():
    # Ensure the user is logged in
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    # Define the user's folder for storing files
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)
    os.makedirs(user_folder, exist_ok=True)

    # Try to list the files in the user's folder, handle errors gracefully
    try:
        files = os.listdir(user_folder)
    except Exception as e:
        files = []  # If error, set files to an empty list

    # Get the list of all users in the system (for file access purposes)
    users = get_all_users(username)

    selected_user = request.form.get("user")  # If a user has been selected, fetch their files
    selected_user_files = []

    # If a user is selected, show their files
    if selected_user:
        selected_user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], selected_user)
        os.makedirs(selected_user_folder, exist_ok=True)

        try:
            selected_user_files = os.listdir(selected_user_folder)
        except Exception as e:
            selected_user_files = []  # If error, set selected user's files to an empty list

    # Sort files alphabetically for display
    files.sort()
    selected_user_files.sort()

    # Render the template with user files and the option to select another user
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
    return send_from_directory(user_folder, filename)


@app.route("/download/<filename>")
def download_file(filename):
    username = session.get("username")
    if not username:
        return "User not logged in", 403

    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username)

    if not os.path.exists(os.path.join(user_folder, filename)):
        return "File not found", 404

    return send_from_directory(user_folder, filename, as_attachment=True)


@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    username = session.get("username")
    if not username:
        return "User not logged in", 403

    file_path = os.path.join(app.config["BASE_UPLOAD_FOLDER"], username, filename)

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
