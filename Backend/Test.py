from flask import Flask, request, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

# Define the Flask app and templates folder
template_folder = r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates"
app = Flask(__name__, template_folder=template_folder)

@app.route("/")
def home():
    return redirect(url_for("login"))
# Function to get a database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="cloud",  # Replace with your MySQL user
            password="rootme1",  # Replace with your MySQL password
            database="cloud"  # Replace with your actual database name
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Function to get a user by email from the database
def get_user_by_email(email):
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        connection.close()

# Function to add a new user to the database
def add_user(email, hashed_password):
    connection = get_db_connection()
    if not connection:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_password),
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Get user from the database
        user = get_user_by_email(email)
        if not user:
            return "User not found.", 404

        # Validate the password
        stored_hash = user["password"]
        if check_password_hash(stored_hash, password):
            print(f"Login successful for {email}")
            return redirect(url_for("main_program"))
        else:
            print(f"Password mismatch for {email}")
            return "Invalid credentials, please try again.", 401

    return render_template("Login.html")

# Main program route
@app.route("/main")
def main_program():
    return "Welcome to the main program!"

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user already exists
        if get_user_by_email(email):
            return "User already exists.", 400

        # Hash the password and add the user to the database
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        if add_user(email, hashed_password):
            print(f"New user registered: {email}")
            return redirect(url_for("login"))
        else:
            return "Error registering user. Please try again.", 500

    return render_template("signup.html")

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
