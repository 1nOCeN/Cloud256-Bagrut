import os
import secrets


class Config:
    """מחלקה לניהול הגדרות האפליקציה"""

    def __init__(self):
        self.SECRET_KEY = secrets.token_hex(32)
        self.SESSION_TYPE = "filesystem"
        self.BASE_UPLOAD_FOLDER = r"\\DESKTOP-1EOTSNC\Cloud256-Database2"
        self.TEMPLATE_FOLDER = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"
        self.STATIC_FOLDER = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\static"

        # הגדרות קבצים
        self.ALLOWED_EXTENSIONS = {"png", 'jpg', "jpeg", "gif", 'pdf', "txt", "docx"}
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

        # יצירת תיקייה אם לא קיימת
        os.makedirs(self.BASE_UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(self, filename):
        """בדיקה אם סוג הקובץ מותר"""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.ALLOWED_EXTENSIONS