from typing import Final
from uuid import UUID
import re

ROOT_ID: Final[UUID] = UUID("0" * 32)
ROOT_NAME: Final[str] = ""

NAMESPACE_SEPARATOR: Final[str] = "."


# Corpus names in the context of pathnames will look like "xxx.yyy.zzz:corpus_name"
# Root level corpora will still look like ":corpus_name"
CORPUS_SEPARATOR: Final[str] = ":"


def is_pathname_format_valid(pathname: str) -> bool:
    tokens = pathname.split(CORPUS_SEPARATOR)
    if len(tokens) < 2:
        namespace_pathname = pathname
    elif len(tokens) == 2:
        if not is_name_format_valid(tokens[1]):
            return False
        namespace_pathname = tokens[0]
    else:
        return False

    tokens = namespace_pathname.split(NAMESPACE_SEPARATOR)
    # We allow only the root namespace to be empty string.
    # This needs to be specially handled since is_name_format_valid won't allow empty names
    if len(tokens) == 1 and tokens[0] == ROOT_NAME:
        return True

    for segment in tokens:
        if not is_name_format_valid(segment):
            print(f"Segment \"{segment}\" not valid")
            return False
    return True


NAME_REGEX: re.Pattern = re.compile(r"[A-Za-z_]+")


def is_name_format_valid(name: str) -> bool:
    return re.fullmatch(NAME_REGEX, name) is not None
