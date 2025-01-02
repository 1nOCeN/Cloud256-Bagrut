from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify
import os
import requests

# Create the Flask application
app = Flask(__name__)

# Set the folder where uploaded files will be saved
UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Define allowed file extensions (optional)
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to display the upload form and list files
@app.route("/")
def upload_form():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return f'''
    <!doctype html>
    <title>Upload File</title>
    <h1>Upload a File</h1>
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <h2>Uploaded Files</h2>
    <ul>
        {''.join([f'<li>{file} - <a href="/download/{file}">Download</a> | <a href="/delete/{file}">Delete</a></li>' for file in files])}
    </ul>
    '''

# Route to handle file upload
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
        return redirect(url_for("upload_form"))
    else:
        return "File not allowed", 400

# Route to download a file
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

# Route to delete a file
@app.route("/delete/<filename>")
def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for("upload_form"))
    else:
        return "File not found", 404


    # URL of the Flask server
    url = "http://192.168.10.14:5000/upload"

    # Path to the file you want to upload
    file_path = "/path/to/your/file.txt"

    # Open the file in binary mode and send it as a POST request
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

    # Print the server's response
    print(response.text)


# Run the server
if __name__ == "__main__":
    app.run(host="192.168.10.14", port=5000, debug=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)  # Ensure upload folder exists