from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
import uuid

# Absolute path to your 'templates' directory
template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"

# Create Flask app and specify the custom templates folder
app = Flask(__name__, template_folder=template_folder)
app.secret_key = "your_secret_key"  # Needed for Flask sessions

# Set the base upload folder
BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
app.config["BASE_UPLOAD_FOLDER"] = BASE_UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

# Check if a file is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure the user's folder exists
def get_user_folder():
    user_id = session.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())  # Generate a unique ID for the user
        session["user_id"] = user_id
    user_folder = os.path.join(app.config["BASE_UPLOAD_FOLDER"], user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

# Home route to display the upload form
@app.route("/", methods=["GET", "POST"])
def upload_page():
    user_folder = get_user_folder()  # Ensure the user's folder exists
    if request.method == "POST":
        # Handle file upload
        if "file" not in request.files:
            return "No file part in the request", 400
        file = request.files["file"]
        if file.filename == "":
            return "No file selected for uploading", 400
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(user_folder, filename))
            return redirect(url_for("main_program"))
        else:
            return "File not allowed", 400
    return render_template("upload.html")

# Main program route to list user-specific files
@app.route("/mainprogram")
def main_program():
    user_folder = get_user_folder()
    files = os.listdir(user_folder)
    return render_template("Mainprogram.html", files=files)

# Route to serve files for the current user
@app.route("/serve/<filename>")
def serve_file(filename):
    user_folder = get_user_folder()
    return send_from_directory(user_folder, filename)

# Route to download a file for the current user
@app.route("/download/<filename>")
def download_file(filename):
    user_folder = get_user_folder()
    return send_from_directory(user_folder, filename, as_attachment=True)

# Route to delete a file for the current user
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for("main_program"))
    else:
        return "File not found", 404

if __name__ == "__main__":
    os.makedirs(app.config["BASE_UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
