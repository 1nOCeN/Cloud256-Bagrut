import os
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import send_file


class FileManager:
    """מחלקה לניהול קבצים - העלאה, הורדה, מחיקה"""

    def __init__(self, base_upload_folder, encryption_manager):
        self.base_upload_folder = base_upload_folder
        self.encryption_manager = encryption_manager

    def get_user_folder(self, username):
        """קבלת תיקיית המשתמש"""
        user_folder = os.path.join(self.base_upload_folder, username)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder

    def get_user_files(self, username, offset=0, limit=None, show_all=False):
        """קבלת רשימת קבצים של המשתמש"""
        user_folder = self.get_user_folder(username)

        try:
            files = [f for f in os.listdir(user_folder) if f.endswith('.enc')]

            if show_all:
                return files, False, 0

            if limit:
                files_to_display = files[offset:offset + limit]
                show_more = len(files) > (offset + limit)
                return files_to_display, show_more, offset + limit

            return files, False, 0

        except Exception as e:
            print(f"Error getting user files: {e}")
            return [], False, 0

    def save_and_encrypt_files(self, files, username):
        """שמירה והצפנת קבצים"""
        user_folder = self.get_user_folder(username)
        encrypted_file_paths = []

        for file in files:
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            temp_file_path = os.path.join(user_folder, filename)

            try:
                # שמירת קובץ זמני
                file.save(temp_file_path)
                print(f"File saved to {temp_file_path}")

                # הצפנת הקובץ
                encrypted_file_path = self.encryption_manager.encrypt_file(temp_file_path)
                encrypted_file_paths.append(encrypted_file_path)

                # מחיקת הקובץ המקורי
                os.remove(temp_file_path)

                print(f"File encrypted and saved as {encrypted_file_path}")

            except Exception as e:
                print(f"Error processing file {filename}: {e}")
                raise

        return encrypted_file_paths

    def get_encrypted_file_path(self, username, filename):
        """קבלת נתיב קובץ מוצפן"""
        user_folder = self.get_user_folder(username)
        return os.path.join(user_folder, filename)

    def download_decrypted_file(self, username, filename):
        """הורדת קובץ מפוענח"""
        encrypted_file_path = self.get_encrypted_file_path(username, filename)

        if not os.path.exists(encrypted_file_path):
            return None, "File not found"

        try:
            # קריאת קובץ מוצפן
            with open(encrypted_file_path, "rb") as encrypted_file:
                encrypted_data = encrypted_file.read()

            # פענוח הקובץ
            decrypted_data = self.encryption_manager.decrypt_file_data(encrypted_data)

            # יצירת קובץ זיכרון להורדה
            decrypted_file = BytesIO(decrypted_data)
            decrypted_file.seek(0)

            return send_file(
                decrypted_file,
                as_attachment=True,
                download_name=filename.replace(".enc", ""),
                mimetype="application/octet-stream"
            ), None

        except Exception as e:
            print(f"Error decrypting file: {str(e)}")
            return None, f"Error retrieving file: {str(e)}"

    def delete_file(self, username, filename):
        """מחיקת קובץ"""
        file_path = self.get_encrypted_file_path(username, filename)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True, None
            except Exception as e:
                return False, f"Error deleting file: {str(e)}"

        return False, "File not found"

    def file_exists(self, username, filename):
        """בדיקה אם קובץ קיים"""
        file_path = self.get_encrypted_file_path(username, filename)
        return os.path.exists(file_path)