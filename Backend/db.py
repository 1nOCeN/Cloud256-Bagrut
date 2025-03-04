import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

# Function to connect to MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="rootme1",
            database="cloud"
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
def add_user(email, username, password):
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
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
