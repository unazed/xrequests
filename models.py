class Response:
    def __init__(self, status, message, headers, content):
        self.status = status
        self.message = message
        self.headers = headers
        self.content = content