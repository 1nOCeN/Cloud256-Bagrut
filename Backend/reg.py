from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder=r"C:\Users\Admin\Documents\GitHub\Cloud256-Bagrut\Fronted\templates")
app.secret_key = 'your_secret_key'

# Ensure users.db is created if not already
def init_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        ''')
        conn.commit()
        conn.close()

# Route for the main program (after login)
@app.route("/mainprogram")
def main_program():
    return render_template("Mainprogram.html")

# Route for the sign-up page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form['Email']
        username = request.form['Username']
        password = request.form['Password']

        # Hash the password for security
        hashed_password = generate_password_hash(password, method='sha256')

        # Connect to the SQLite database and insert user data
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        if cursor.fetchone():
            flash("Email already exists! Please use a different one.", "danger")
            return redirect(url_for('signup'))

        # Insert the new user into the users table
        cursor.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                       (email, username, hashed_password))

        # Commit and close the connection
        conn.commit()
        conn.close()

        flash("Sign-up successful! Please log in.", "success")
        return redirect(url_for('login'))  # Redirect to login page after successful signup

    return render_template("signup.html")

# Route for the login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['Email']
        password = request.form['Password']

        # Connect to the SQLite database and check credentials
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Fetch user from the database
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):  # Check hashed password
            flash("Login successful!", "success")
            return redirect(url_for('main_program'))  # Redirect to main program after successful login
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template("Login.html")


if __name__ == "__main__":
    init_db()  # Ensure database and table are initialized
    app.run(host="192.168.10.14", port=5000, debug=True)
