from enum import Enum


class MemasInternalException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class IllegalStateException(MemasInternalException):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class StatusCode(Enum):
    # The request could not be understood by the server due to incorrect syntax. The client SHOULD NOT repeat the request without modifications.
    BAD_REQUEST = 400
    # Indicates that the request requires user authentication information. The client MAY repeat the request with a suitable Authorization header field
    UNAUTHORIZED = 401
    # Unauthorized request. The client does not have access rights to the content. Unlike 401, the client’s identity is known to the server.
    FORBIDDEN = 403
    # The server can not find the requested resource.
    NOT_FOUND = 404
    # The request HTTP method is known by the server but has been disabled and cannot be used for that resource.
    METHOD_NOT_ALLOWED = 405


# Each memas error needs to have an unique error code
class ErrorCode(Enum):
    NamespaceExists = "namespace_exists"
    NamespaceDoesNotExist = "namespace_does_not_exist"
    NamespaceIllegalName = "namespace_illegal_name"


class MemasException(Exception):
    def __init__(self, error_code: ErrorCode, msg: str, additional_details: str = None) -> None:
        super().__init__(msg)
        self.status_code: StatusCode = StatusCode.BAD_REQUEST
        self.error_code: ErrorCode = error_code
        self.msg: str = msg
        self.additional_details: str = additional_details

    def return_obj(self):
        resp = {"error_code": self.error_code.value, "msg": self.msg}
        if self.additional_details:
            resp["details"] = self.additional_details
        return resp


class IllegalNameException(MemasException):
    def __init__(self, pathname: str) -> None:
        super().__init__(ErrorCode.NamespaceIllegalName, f"\"{pathname}\" is not a valid pathname")


class NamespaceExistsException(MemasException):
    def __init__(self, pathname: str, additional_details: str = None) -> None:
        super().__init__(ErrorCode.NamespaceExists, f"\"{pathname}\" already exists", additional_details)


class NamespaceDoesNotExistException(MemasException):
    def __init__(self, pathname: str, additional_details: str = None) -> None:
        super().__init__(ErrorCode.NamespaceDoesNotExist,
                         f"\"{pathname}\" does not exists, you need to create the resource first", additional_details)


# TODO: properly specify this exception type
class SentenceLengthOverflowException(Exception):
    def __init__(self, sentence_len: int) -> None:
        super().__init__("Sentence length is {len} which exceededs limit".format(len=sentence_len))
