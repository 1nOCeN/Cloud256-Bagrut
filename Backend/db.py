import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash


# Function to connect to MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="cloud",
            password="rootme1",
            database="cloud"
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        raise e  # Raise the exception so the caller knows the connection failed


# Function to get user by email
def get_user_by_email(email):
    connection = get_db_connection()
    try:
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            return user
    except Error as e:
        print(f"Error while fetching user by email: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return None


# Function to get user by username
def get_user_by_username(username):
    connection = get_db_connection()
    try:
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            return user
    except Error as e:
        print(f"Error while fetching user by username: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return None


# Function to add a new user
def add_user(email, username, password):
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    connection = get_db_connection()
    try:
        if connection:
            cursor = connection.cursor()
            query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (email, username, hashed_password))
            connection.commit()
            print("User added successfully")
            return True
    except mysql.connector.IntegrityError as e:
        print(f"Integrity error (e.g., duplicate email or username): {e}")
    except Error as e:
        print(f"Error while adding user: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return False
