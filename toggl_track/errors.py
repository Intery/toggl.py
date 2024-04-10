class TogglException(Exception):
    """
    Base exception class for Toggl.py
    """
    pass


class HTTPException(TogglException):
    def __init__(self, response, message):
        self.response = response
        self.stats = response.status

        error = "{} {}: {}".format(response.status, response.reason, message)
        super().__init__(error)


class LoginFailure(TogglException):
    """
    Thrown when client login fails, usually due to invalid credentials.
    """
    pass


class PaymentRequired(HTTPException):
    """
    Thrown in the case of a 402 error.
    """
    pass
