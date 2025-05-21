import secrets, datetime
import mysql.connector
from flask import jsonify, request
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Function to connect to MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            database="cloud256"
        )
        return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None  # Return None instead of raising an exception

def get_user_by_email(email):
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error while fetching user by email: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def add_user(email, username, password_hash):
    hashed_password = generate_password_hash(password_hash, method="pbkdf2:sha256", salt_length=16)
    api_token = generate_api_token()  # Generate token here
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 1-day expiration

    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "INSERT INTO users (email, username, password_hash, api_token, token_expiration) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (email, username, hashed_password, api_token, expiration_time))
        connection.commit()
        return api_token  # Return the API token after registration
    except mysql.connector.IntegrityError:
        print("Integrity error: Duplicate email or username")
        return False
    except Error as e:
        print(f"Error while adding user: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


# Function to get all users except the current user
def get_all_users(current_username):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT username FROM users WHERE username != %s"
        cursor.execute(query, (current_username,))
        users = cursor.fetchall()
        return users
    except Error as e:
        print(f"Error retrieving users: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_encryption_key_from_db():
    """Retrieve the encryption key from the database."""
    connection = get_db_connection()
    if not connection:
        return None  # Return None if connection fails

    try:
        cursor = connection.cursor()
        query = "SELECT key_value FROM encryption_keys ORDER BY created_at DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            return result[0]  # Return the key as a string
        return None  # No key found
    except Error as e:
        print(f"Error retrieving encryption key: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def store_encryption_key_to_db(key_value):
    """Store a new encryption key in the database."""
    connection = get_db_connection()
    if not connection:
        return False  # Return False if connection fails

    try:
        cursor = connection.cursor()
        query = "INSERT INTO encryption_keys (key_value) VALUES (%s)"
        cursor.execute(query, (key_value,))
        connection.commit()
        return True  # Success
    except Error as e:
        print(f"Error storing encryption key: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Function to generate a random API token
def generate_api_token():
    return secrets.token_hex(32)  # Generates a secure 64-character hex token


def store_api_token(user_id, token, expires_in=3600):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "INSERT INTO api_tokens (user_id, token, expiration) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, token, expiration_time))
        connection.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Error storing API token: {e}")
        return False
    finally:
        cursor.close()
        connection.close()



def get_user_by_token(token):
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = """SELECT u.* FROM users u
                   JOIN api_tokens t ON u.id = t.user_id
                   WHERE t.token = %s AND t.expiration > %s"""
        cursor.execute(query, (token, datetime.datetime.utcnow()))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as e:
        print(f"Error retrieving user by token: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

# User login function (generate and save API token)
def login_user(email, password):
    user = get_user_by_email(email)

    if not user:
        return {"success": False, "message": "User not found"}

    if not check_password_hash(user["password_hash"], password):
        return {"success": False, "message": "Invalid password"}

    # Generate a new API token
    new_token = generate_api_token()
    if store_api_token(user["id"], new_token):
        return {"success": True, "api_token": new_token}
    else:
        return {"success": False, "message": "Error generating token"}

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"message": "Token is missing"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"message": "Invalid token format"}), 401

        token = parts[1]
        user = get_user_by_token(token)
        if not user:
            return jsonify({"message": "Invalid or expired token"}), 403

        return f(user, *args, **kwargs)

    return decorated_function

def update_user_token(user_id, token):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token valid for 1 day

    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "UPDATE users SET api_token = %s, token_expiration = %s WHERE id = %s"
        cursor.execute(query, (token, expiration_time, user_id))
        connection.commit()
        return True
    except Error as e:
        print(f"Error updating token: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_api_token_from_db(user_id):
    """Retrieve the API token from the database for a specific user."""
    connection = get_db_connection()
    if not connection:
        return None  # Return None if connection fails

    try:
        cursor = connection.cursor()
        query = "SELECT api_token FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Return the token if found
        return None  # No token found for the user
    except Error as e:
        print(f"Error retrieving API token: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

