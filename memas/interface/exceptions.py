

class BadArgumentException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class IllegalNameException(BadArgumentException):
    def __init__(self, pathname: str) -> None:
        super().__init__(f"\"{pathname}\" is not a valid pathname")


class NamespaceExistsException(Exception):
    def __init__(self, pathname: str) -> None:
        super().__init__(f"\"{pathname}\" already exists")


class NotProperlyInitializedException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)

class SentenceLengthOverflowException(Exception):
    def __init__(self, sentence_len: int) -> None:
        super().__init__("Sentence length is {len} which exceededs limit".format(len=sentence_len))
