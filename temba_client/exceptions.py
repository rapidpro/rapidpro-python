class TembaException(Exception):
    def __str__(self):
        return self.message


class TembaConnectionError(TembaException):
    message = "Unable to connect to host"


class TembaBadRequestError(TembaException):
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        msgs = []
        if isinstance(self.errors, dict):
            for field, field_errors in self.errors.items():
                if isinstance(field_errors, str):  # e.g. {"detail": "message..."}
                    msgs.append(field_errors)
                else:
                    for error in field_errors:  # e.g. {"field1": ["msg1...", "msg2..."]}
                        msgs.append(error)
        elif isinstance(self.errors, list):
            msgs = self.errors

        return msgs[0] if len(msgs) == 1 else ". ".join(msgs)


class TembaTokenError(TembaException):
    message = "Authentication with provided token failed"


class TembaNoSuchObjectError(TembaException):
    message = "No such object exists"


class TembaRateExceededError(TembaException):
    message = (
        "You have exceeded the number of requests allowed per org in a given time window. "
        "Please wait %d seconds before making further requests"
    )

    def __init__(self, retry_after):
        self.retry_after = retry_after

    def __str__(self):
        return self.message % self.retry_after


class TembaHttpError(TembaException):
    def __init__(self, caused_by):
        self.caused_by = caused_by

    def __str__(self):
        return str(self.caused_by)


class TembaSerializationException(TembaException):
    def __init__(self, message):
        self.message = message


class TembaMultipleResultsError(TembaException):
    message = "Request for single object returned multiple objects"
