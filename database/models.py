class User:
    def __init__(self, user_id: int, username: str, status: str):
        self.id = user_id
        self.username = username
        self.status = status

class Server:
    def __init__(self, id: int, user_id: int, name: str, address: str, check_type: str, status: str, last_checked: str):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.address = address
        self.check_type = check_type
        self.status = status
        self.last_checked = last_checked

class Notification:
    def __init__(self, id: int, server_id: int, user_id: int, status: str, timestamp: str):
        self.id = id
        self.server_id = server_id
        self.user_id = user_id
        self.status = status
        self.timestamp = timestamp