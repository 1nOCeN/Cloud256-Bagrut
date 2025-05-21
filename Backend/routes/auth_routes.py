from flask import render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from Backend.db import get_user_by_email, add_user, get_api_token_from_db, generate_api_token, store_api_token
from Backend import app

@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = None

    # Already logged in? Skip to main
    if session.get('user_id'):
        return redirect(url_for('main_program'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Basic validation
        if not email or not password:
            return redirect(url_for("login"))  # Redirect back if missing credentials

        # Check credentials
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            # Save user details in session
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            # Retrieve the API token from the database
            token = get_api_token_from_db(user["id"])

            # If no token exists in the DB, handle this scenario
            if not token:
                token = generate_api_token(user["id"])
                store_api_token(user["id"], token)

            # Redirect to the main program
            return redirect(url_for("main_program"))

        # Auth failed
        error_msg = "Invalid email or password"

    return render_template("Login.html", error=error_msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    # Get form data
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")

    # Validation
    if not email or not username or not password:
        return "All fields are required.", 400

    if "@" not in email or "." not in email:
        return "Invalid email format", 400

    if get_user_by_email(email):
        return "Email already exists.", 400

    if len(password) < 8:
        return "Password must be at least 8 characters", 400

    # Create user and get API token
    api_token = add_user(email, username, password)

    if api_token:
        return jsonify({"message": "Registration successful", "token": api_token})

    return "Error registering user.", 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))