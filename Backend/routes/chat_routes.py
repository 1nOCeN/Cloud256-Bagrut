from flask import render_template, session
from flask_socketio import join_room, emit
from Backend import app, socketio, background_progress_tracking
import threading
from progress_tracker import thread_lock


@app.route("/start_chat/<username>", methods=["GET"])
def start_chat(username):
    current_user = session.get("username")
    # Can't chat with yourself
    if current_user == username:
        return "You can't chat with yourself", 400

    # Create a unique room id by combining usernames alphabetically
    room = f"{min(current_user, username)}_{max(current_user, username)}"
    return render_template("Chat.html", room=room, username=username)


# Socket stuff for chat
@socketio.on('connect')
def handle_connect():
    print(f'User {session.get("username", "Unknown")} connected')

    # Start progress tracking thread if not already running
    global progress_thread
    with thread_lock:
        if progress_thread is None or not progress_thread.is_alive():
            progress_thread = threading.Thread(target=background_progress_tracking)
            progress_thread.daemon = True
            progress_thread.start()


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print(f'{username} has entered the room {room}')


@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']

    # Debug print
    print(f"Broadcasting message from {username}: {message}")

    # Send it out to everyone in the room
    emit('receive_message', {'username': username, 'message': message}, room=room)


@socketio.on('disconnect')
def handle_disconnect():
    print(f'User {session.get("username", "Unknown")} disconnected')