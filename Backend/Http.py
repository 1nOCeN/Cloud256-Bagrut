from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

# Absolute path to your 'templates' directory
template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"

# Create Flask app and specify the custom templates folder
app = Flask(__name__, template_folder=template_folder)

# Set the folder where uploaded files will be saved
UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

# Check if a file is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route to display the main program
@app.route("/")
def main_program():
    # List files in the upload folder
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("Mainprogram.html", files=files)  # Render template from 'templates' folder

# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part in the request", 400
    file = request.files["file"]
    if file.filename == "":
        return "No file selected for uploading", 400
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return redirect(url_for("main_program"))
    else:
        return "File not allowed", 400

# Route to serve files
@app.route("/serve/<filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Route to download a file
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

# Route to delete a file
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for("Mainprogram.html"))
    else:
        return "File not found", 404

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="192.168.10.14", port=5000, debug=True)
