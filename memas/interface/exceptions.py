

class NamespaceExistsException(Exception):
    def __init__(self, pathname: str) -> None:
        super().__init__(f"\"{pathname}\" already exists")
