class RequestException(Exception):
    pass

class UnknownScheme(RequestException):
    pass

class EmptyResponse(RequestException):
    pass

class UnsupportedEncoding(RequestException):
    pass