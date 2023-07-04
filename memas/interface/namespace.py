from typing import Final
from uuid import UUID

ROOT_ID: Final[UUID] = UUID("0" * 32)
ROOT_NAME: Final[str] = ""

NAMESPACE_SEPARATOR: Final[str] = "."


# Corpus names in the context of pathnames will look like "xxx.yyy.zzz:corpus_name"
# Root level corpora will still look like ":corpus_name"
CORPUS_SEPARATOR: Final[str] = ":"


def is_pathname_format_valid(pathname: str) -> bool:
    tokens = pathname.split(CORPUS_SEPARATOR)
    if len(tokens) > 2:
        namespace_pathname = pathname
    elif len(tokens) == 2:
        if not is_name_format_valid(tokens[1]):
            return False
        namespace_pathname = tokens[0]
    else:
        return False

    tokens = namespace_pathname.split(NAMESPACE_SEPARATOR)
    for segment in tokens:
        if not is_name_format_valid(segment):
            return False
    return True


def is_name_format_valid(name: str) -> bool:
    # TODO: implement this
    return True
