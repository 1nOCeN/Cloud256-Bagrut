from collections import defaultdict

class NotificationManager:
    def __init__(self):
        self.notifications = defaultdict(list)

    def add_notification(self, username, filename):
        self.notifications[username].append(filename)

    def get_notifications(self, username):
        files = self.notifications.get(username, [])
        self.notifications[username] = []  # clear after fetch
        return files

notification_manager = NotificationManager()
