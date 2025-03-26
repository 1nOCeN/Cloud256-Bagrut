import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

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

# Function to add a new user
def add_user(email, username, password_hash):
    hashed_password = generate_password_hash(password_hash, method="pbkdf2:sha256", salt_length=16)
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, username, hashed_password))
        connection.commit()
        return True
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
