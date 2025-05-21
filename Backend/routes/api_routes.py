import os
from Backend import app
from Backend import token_required

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