import threading
import time
from flask_socketio import join_room, emit
from flask import session


class ChatManager:
    """מחלקה לניהול צ'אט וחיבורי WebSocket"""

    def __init__(self, socketio):
        self.socketio = socketio
        self.progress_thread = None
        self.thread_lock = threading.Lock()

        # רישום event handlers
        self.register_socket_events()

    def register_socket_events(self):
        """רישום אירועי Socket.IO"""

        @self.socketio.on("connect")
        def handle_connect():
            username = session.get("username")
            if username:
                join_room(f"user_{username}")
                print(f"User {username} connected and joined room user_{username}")

            self.start_progress_tracking()

        @self.socketio.on('join')
        def on_join(data):
            username = data['username']
            room = data['room']
            join_room(room)
            print(f'{username} has entered the room {room}')

        @self.socketio.on('message')
        def handle_message(data):
            room = data['room']
            message = data['message']
            username = data['username']

            print(f"Broadcasting message from {username}: {message}")

            # שליחת הודעה לכל המשתתפים בחדר
            emit('receive_message', {
                'username': username,
                'message': message
            }, room=room)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            username = session.get("username", "Unknown")
            print(f'User {username} disconnected')

    def start_progress_tracking(self):
        """התחלת מעקב התקדמות ברקע"""
        with self.thread_lock:
            if self.progress_thread is None or not self.progress_thread.is_alive():
                print("Starting progress tracking thread...")
                self.progress_thread = threading.Thread(target=self.background_progress_tracking)
                self.progress_thread.daemon = True
                self.progress_thread.start()
            else:
                print("Progress tracking thread is already running.")

    def background_progress_tracking(self):
        """פונקציה לרקע למעקב התקדמות"""
        while True:
            time.sleep(10)  # סימולציה של עדכונים תקופתיים
            self.socketio.emit("progress_update", {"message": "Tracking progress..."})

    @staticmethod
    def create_chat_room(current_user, target_user):
        """יצירת חדר צ'אט ייחודי בין שני משתמשים"""
        if current_user == target_user:
            return None, "You can't chat with yourself"

        # יצירת ID חדר ייחודי על ידי שילוב שמות המשתמשים באלפבית
        room = f"{min(current_user, target_user)}_{max(current_user, target_user)}"
        return room, None

    def emit_to_user(self, username, event, data):
        """שליחת הודעה למשתמש ספציפי"""
        self.socketio.emit(event, data, room=f"user_{username}")

    def emit_to_room(self, room, event, data):
        """שליחת הודעה לחדר ספציפי"""
        self.socketio.emit(event, data, room=room)