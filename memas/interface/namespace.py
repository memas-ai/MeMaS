import logging
import re
from typing import Final
from uuid import UUID

_log = logging.getLogger(__name__)


ROOT_ID: Final[UUID] = UUID("0" * 32)
ROOT_NAME: Final[str] = ""

NAMESPACE_SEPARATOR: Final[str] = "."


# Corpus names in the context of pathnames will look like "xxx.yyy.zzz:corpus_name"
# Root level corpora will still look like ":corpus_name"
CORPUS_SEPARATOR: Final[str] = ":"


def mangle_corpus_pathname(parent_pathname: str, corpus_name: str) -> str:
    return parent_pathname + CORPUS_SEPARATOR + corpus_name


def is_namespace_pathname_valid(pathname: str) -> bool:
    if CORPUS_SEPARATOR in pathname:
        return False

    tokens = pathname.split(NAMESPACE_SEPARATOR)
    # We allow only the root namespace to be empty string.
    # This needs to be specially handled since is_name_format_valid won't allow empty names
    if len(tokens) == 1 and tokens[0] == ROOT_NAME:
        return True

    for segment in tokens:
        if not is_name_format_valid(segment):
            _log.info(f"Segment \"{segment}\" not valid")
            return False
    return True


def is_corpus_pathname_valid(pathname: str) -> bool:
    tokens = pathname.split(CORPUS_SEPARATOR)
    if len(tokens) != 2:
        return False

    return is_name_format_valid(tokens[1]) and is_namespace_pathname_valid(tokens[0])


NAME_REGEX: re.Pattern = re.compile(r"[A-Za-z0-9_]+")


def is_name_format_valid(name: str) -> bool:
    return re.fullmatch(NAME_REGEX, name) is not None
