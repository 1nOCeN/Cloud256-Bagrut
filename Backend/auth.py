from werkzeug.security import check_password_hash
from flask import session
from db import (get_user_by_email, add_user, get_api_token_from_db,
                generate_api_token, store_api_token, get_all_users)


class AuthManager:
    """מחלקה לניהול אימות משתמשים"""

    @staticmethod
    def login_user(email, password):
        """כניסת משתמש למערכת"""
        if not email or not password:
            return False, "Missing email or password", None

        # בדיקת פרטי המשתמש
        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return False, "Invalid email or password", None

        # שמירת פרטי המשתמש בסשן
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        # קבלת טוקן API
        token = get_api_token_from_db(user["id"])
        if not token:
            # יצירת טוקן חדש אם לא קיים
            token = generate_api_token(user["id"])
            store_api_token(user["id"], token)

        return True, "Login successful", user

    @staticmethod
    def register_user(email, username, password):
        """רישום משתמש חדש"""
        # ולידציה בסיסית
        if not email or not username or not password:
            return False, "All fields are required.", None

        if "@" not in email or "." not in email:
            return False, "Invalid email format", None

        if get_user_by_email(email):
            return False, "Email already exists.", None

        if len(password) < 8:
            return False, "Password must be at least 8 characters", None

        # יצירת משתמש וקבלת טוקן API
        api_token = add_user(email, username, password)

        if api_token:
            return True, "Registration successful", api_token

        return False, "Error registering user.", None

    @staticmethod
    def logout_user():
        """יציאת משתמש מהמערכת"""
        session.clear()

    @staticmethod
    def get_current_user():
        """קבלת המשתמש הנוכחי מהסשן"""
        return {
            'user_id': session.get('user_id'),
            'username': session.get('username')
        }

    @staticmethod
    def is_logged_in():
        """בדיקה אם המשתמש מחובר"""
        return session.get('user_id') is not None

    @staticmethod
    def get_user_api_token(user_id):
        """קבלת טוכן API של המשתמש"""
        return get_api_token_from_db(user_id)

    @staticmethod
    def get_all_users_except(username):
        """קבלת כל המשתמשים חוץ מהמשתמש הנוכחי"""
        return get_all_users(username)