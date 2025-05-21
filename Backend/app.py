# Backend/app.py
import os

from flask import redirect, render_template, url_for

from Backend import app, socketio
from Backend.routes import auth_routes, file_routes, chat_routes, api_routes

@app.route("/")
def home():
    # Just redirect to login
    return redirect(url_for("login"))

@app.route("/index")
def index():
    return render_template("index.html")

@app.errorhandler(500)
def server_error(e):
    return "Server error, please try again later", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)