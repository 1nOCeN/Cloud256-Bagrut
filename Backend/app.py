import os
from flask import Flask, jsonify, session
from flask_socketio import SocketIO
from db import token_required

# ייבוא המחלקות שלנו
from config import Config
from encryption import EncryptionManager
from files import FileManager
from auth import AuthManager
from ChatManager import ChatManager
from route import RouteHandlers
from Progress_socket import ProgressSocketServer
from Notify import notification_manager

class CloudStorageApp:
    """מחלקה ראשית לאפליקציית אחסון הענן"""

    def __init__(self):
        # יצירת האפליקציה
        self.config = Config()
        self.app = Flask(__name__,
                         template_folder=self.config.TEMPLATE_FOLDER,
                         static_folder=self.config.STATIC_FOLDER)

        # הגדרת תצורה
        self.app.secret_key = self.config.SECRET_KEY
        self.app.config["SESSION_TYPE"] = self.config.SESSION_TYPE
        self.app.config["BASE_UPLOAD_FOLDER"] = self.config.BASE_UPLOAD_FOLDER

        # יצירת SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.progress_server = ProgressSocketServer(host="0.0.0.0", port=5555)
        self.progress_server.start()

        # Attach to Flask app for access inside routes
        self.app.progress_server = self.progress_server

        # יצירת מנהלי המערכת
        self.encryption_manager = EncryptionManager()
        self.file_manager = FileManager(self.config.BASE_UPLOAD_FOLDER, self.encryption_manager)
        self.auth_manager = AuthManager()
        self.chat_manager = ChatManager(self.socketio)
        self.route_handlers = RouteHandlers(
            self.auth_manager,
            self.file_manager,
            self.chat_manager,
            self.config,
        )

        # רישום נתיבים
        self.register_routes()
        self.register_error_handlers()

    def check_notifications(self):
        username = session.get('username')
        if not username:
            return jsonify({'notifications': []}), 401

        notifications = notification_manager.get_notifications(username)
        return jsonify({'notifications': notifications})

    def register_routes(self):
        """רישום כל הנתיבים של האפליקציה"""

        # נתיבים בסיסיים
        self.app.add_url_rule("/", "home", self.route_handlers.home)
        self.app.add_url_rule("/index", "index", self.route_handlers.index)

        # נתיבי אימות
        self.app.add_url_rule("/login", "login", self.route_handlers.login, methods=["GET", "POST"])
        self.app.add_url_rule("/register", "register", self.route_handlers.register, methods=["GET", "POST"])
        self.app.add_url_rule("/logout", "logout", self.route_handlers.logout)

        # נתיבי קבצים
        self.app.add_url_rule("/upload", "upload_file", self.route_handlers.upload_file, methods=["GET", "POST"])
        self.app.add_url_rule("/mainprogram", "main_program", self.route_handlers.main_program)
        self.app.add_url_rule("/download/<filename>", "download_file", self.route_handlers.download_file)
        self.app.add_url_rule("/uploads/<filename>", "serve_file", self.route_handlers.serve_file)
        self.app.add_url_rule("/delete/<filename>", "delete_file", self.route_handlers.delete_file, methods=["POST"])

        # נתיבי צ'אט
        self.app.add_url_rule("/start_chat/<username>", "start_chat", self.route_handlers.start_chat, methods=["GET"])

        # נתיבים סטטיים
        self.app.add_url_rule('/static/<path:filename>', "serve_static", self.route_handlers.serve_static)

        # נתיבי API עם token_required wrapper
        self.app.add_url_rule("/api/get-token", "get_user_token",
                              token_required(self.route_handlers.get_user_token), methods=["GET"])
        self.app.add_url_rule("/api/my-files", "api_get_my_files",
                              token_required(self.route_handlers.api_get_my_files), methods=["GET"])

        self.app.add_url_rule("/check_notifications", "check_notifications", self.check_notifications, methods=["GET"])



    def register_error_handlers(self):
        """רישום מטפלי שגיאות"""

        @self.app.errorhandler(500)
        def server_error(e):
            return "Server error, please try again later", 500

        @self.app.errorhandler(404)
        def not_found(e):
            return "Page not found", 404

        @self.app.errorhandler(403)
        def forbidden(e):
            return "Access forbidden", 403

    def run(self, host="0.0.0.0", port=None, debug=True):
        """הרצת האפליקציה"""
        if port is None:
            port = int(os.environ.get("PORT", 5000))

        print(f"Starting Cloud Storage Application on {host}:{port}")
        print(f"Upload folder: {self.config.BASE_UPLOAD_FOLDER}")
        print(f"Debug mode: {debug}")

        self.socketio.run(self.app, host=host, port=port, debug=debug)



def create_app():
    """Factory function ליצירת האפליקציה"""
    return CloudStorageApp()


# הרצת האפליקציה
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)