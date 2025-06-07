import os
from flask import render_template, redirect, url_for, request, jsonify, session, current_app, flash
from db import token_required


class RouteHandlers:
    """מחלקה למטפלי נתיבי Flask"""

    def __init__(self, auth_manager, file_manager, chat_manager, config):
        self.auth_manager = auth_manager
        self.file_manager = file_manager
        self.chat_manager = chat_manager
        self.config = config

    def home(self):
        """דף הבית - הפניה לכניסה"""
        return redirect(url_for("index"))

    def index(self):
        """דף אינדקס"""
        return render_template("index.html")

    def login(self):
        """כניסה למערכת"""
        # אם כבר מחובר, הפנה לדף הראשי
        if self.auth_manager.is_logged_in():
            return redirect(url_for('main_program'))

        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            success, message, user = self.auth_manager.login_user(email, password)

            if success:
                return redirect(url_for("main_program"))
            else:
                return render_template("Login.html", error=message)

        return render_template("Login.html", error=None)

    def register(self):
        """רישום למערכת"""
        if request.method == "GET":
            return render_template("signup.html")

        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        success, message, api_token = self.auth_manager.register_user(email, username, password)

        if success:
            return jsonify({"message": message, "token": api_token})
        else:
            return message, 400 if "already exists" in message else 500

    def logout(self):
        """יציאה מהמערכת"""
        self.auth_manager.logout_user()
        return redirect(url_for("login"))

    from flask import current_app

    def upload_file(self):
        if request.method == "GET":
            return render_template("upload.html")

        if not self.auth_manager.is_logged_in():
            return redirect(url_for("login"))

        if "file" not in request.files:
            return "No file part", 400

        files = request.files.getlist("file")
        if not files:
            return "No file selected", 400

        current_user = self.auth_manager.get_current_user()
        username = current_user['username']

        # Check file extensions
        for file in files:
            if file.filename and not self.config.allowed_file(file.filename):
                return f"File type not allowed. Allowed types: {', '.join(self.config.ALLOWED_EXTENSIONS)}", 400

        try:
            # Save and encrypt files, get list of saved filenames
            encrypted_file_paths = self.file_manager.save_and_encrypt_files(files, username)

            # Notify user for each file upload complete
            for path in encrypted_file_paths:
                filename = os.path.basename(path)
                current_app.progress_server.notify_upload_complete(username, filename)

            flash("File uploaded and encrypted successfully!", "success")
            return redirect(url_for("main_program"))

        except Exception as e:
            return f"Error saving files: {str(e)}", 500

    def main_program(self):
        """דף ראשי - רשימת קבצים"""
        if not self.auth_manager.is_logged_in():
            return redirect(url_for("login"))

        current_user = self.auth_manager.get_current_user()
        username = current_user['username']

        # פרמטרים מה-URL
        show_all = request.args.get("show_all", default=False, type=bool)
        offset = request.args.get("offset", default=0, type=int)

        # קבלת קבצים
        if show_all:
            files_to_display, show_more, new_offset = self.file_manager.get_user_files(
                username, show_all=True)
        else:
            files_to_display, show_more, new_offset = self.file_manager.get_user_files(
                username, offset=offset, limit=5)

        # אם זו בקשת AJAX, החזר רק את רשימת הקבצים
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template("file_list_partial.html",
                                   files=files_to_display,
                                   show_more=show_more,
                                   offset=new_offset)

        # קבלת רשימת משתמשים
        users = self.auth_manager.get_all_users_except(username)

        return render_template("Mainprogram.html",
                               files=files_to_display,
                               users=users,
                               show_more=show_more,
                               offset=new_offset)

    def download_file(self, filename):
        """הורדת קובץ"""
        if not self.auth_manager.is_logged_in():
            return "User not logged in", 403

        current_user = self.auth_manager.get_current_user()
        username = current_user['username']

        result, error = self.file_manager.download_decrypted_file(username, filename)

        if error:
            return error, 404

        return result

    def serve_file(self, filename):
        """הגשת קובץ מוצפן (לצפייה)"""
        if not self.auth_manager.is_logged_in():
            return "Unauthorized", 403

        current_user = self.auth_manager.get_current_user()
        username = current_user['username']

        user_folder = os.path.join(self.config.BASE_UPLOAD_FOLDER, username)
        encrypted_file_path = os.path.join(user_folder, filename)

        if not os.path.exists(encrypted_file_path):
            return "File not found", 404

        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()

            # פענוח הקובץ
            decrypted_data = self.file_manager.encryption_manager.decrypt_file_data(encrypted_data)

            # הגשת הקובץ המפוענח
            from io import BytesIO
            from flask import send_file
            decrypted_file = BytesIO(decrypted_data)
            decrypted_file.seek(0)

            return send_file(
                decrypted_file,
                as_attachment=True,
                download_name=filename.replace(".enc", ""),
                mimetype="application/octet-stream"
            )

        except Exception as e:
            return f"Error retrieving file: {str(e)}", 500

    def delete_file(self, filename):
        """מחיקת קובץ"""
        if not self.auth_manager.is_logged_in():
            return "User not logged in", 403

        current_user = self.auth_manager.get_current_user()
        username = current_user['username']

        success, error = self.file_manager.delete_file(username, filename)

        if success:
            return redirect(url_for("main_program"))
        else:
            return error, 404

    def start_chat(self, username):
        """התחלת צ'אט"""
        current_user = self.auth_manager.get_current_user()
        current_username = current_user['username']

        room, error = self.chat_manager.create_chat_room(current_username, username)

        if error:
            return error, 400

        return render_template("Chat.html", room=room, username=username)

    def serve_static(self, filename):
        """הגשת קבצים סטטיים"""
        from flask import send_from_directory
        return send_from_directory(self.config.STATIC_FOLDER, filename)

    def get_user_token(self, user):
        """API - קבלת טוקן משתמש"""
        return {"api_token": user["api_token"]}

    def api_get_my_files(self, user):
        """API - קבלת קבצי המשתמש"""
        files, _, _ = self.file_manager.get_user_files(user["username"], show_all=True)
        return {"files": files}

