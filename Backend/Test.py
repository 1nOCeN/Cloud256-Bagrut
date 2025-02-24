@app.route("/request_access", methods=["GET", "POST"])
def request_file_access():
    if request.method == "POST":
        filename = request.form.get("filename")
        username = session.get("username", "Guest")

        file_access_requests.append({"user": username, "filename": filename})

        return f"Access request sent for {filename}"

    return render_template("request_access.html")
