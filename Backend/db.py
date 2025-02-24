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

# Function to request file access
def add_file_access_request(requester_username, owner_username, filename):
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO file_access_requests (requester_username, owner_username, filename, status, request_time)
            VALUES (%s, %s, %s, 'pending', NOW())
        """
        cursor.execute(query, (requester_username, owner_username, filename))
        connection.commit()
        return True
    except Error as e:
        print(f"Error while inserting file access request: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Function to get pending requests for a specific owner
def get_pending_requests(owner):
    connection = get_db_connection()  # Get database connection
    try:
        cursor = connection.cursor(dictionary=True)

        # SQL query to get all pending requests for a specific owner
        query = """SELECT * FROM file_access_requests 
                   WHERE owner_username = %s AND status = 'pending'"""

        cursor.execute(query, (owner,))  # Execute the query with the owner parameter
        return cursor.fetchall()  # Return all pending requests
    except Error as e:
        print(f"Error retrieving pending requests: {e}")
        return []  # Return empty list if an error occurs
    finally:
        if cursor:
            cursor.close()  # Close the cursor
        if connection:
            connection.close()  # Close the connection


# Function to update request status (approve/deny)
def update_request_status(request_id, status):
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = "UPDATE file_access_requests SET status = %s WHERE id = %s"
        cursor.execute(query, (status, request_id))
        connection.commit()
        return True
    except Error as e:
        print(f"Error updating request status: {e}")
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

# Function to get files owned by a specific user
def get_user_files(username):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT files.filename FROM files 
        INNER JOIN users ON users.id = files.owner_id 
        WHERE users.username = %s
        """
        cursor.execute(query, (username,))
        return [row["filename"] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error fetching files: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
