class Server:
    def __init__(self, id: int, name: str, ip_address: str, status: str, last_checked: str):
        self.id = id
        self.name = name
        self.ip_address = ip_address
        self.status = status
        self.last_checked = last_checked