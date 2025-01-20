import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash


# Function to connect to MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="cloud",  # Default MySQL user for XAMPP
            password="rootme1",  # Default password for XAMPP MySQL is empty
            database="cloud"  # Replace with your actual database name
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None


# Function to get user by username
def get_user_by_username(username):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    return None

def add_user(email, username, password):
    # Hash the password using PBKDF2
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # Now insert into the database
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, username, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()
        print("User added successfully")


# Function to get user by email
def get_user_by_email(email):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    return None
