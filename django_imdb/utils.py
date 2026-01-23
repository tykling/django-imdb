"""Utils for django-imdb."""

import logging
from pathlib import Path
from typing import TextIO
from urllib.request import Request, urlopen

logger = logging.getLogger(f"django_imdb.{__name__}")
MiB = 1024 * 1024


def count_lines(f: TextIO) -> int:
    """Count lines in a byte iterable. Borrowed and adapted from imdb-sqlite."""
    lines = 0
    chunk = f.read(MiB)
    while chunk:
        lines += chunk.count("\n")
        chunk = f.read(MiB)
    return lines


def download_file(url: str, path: Path) -> None:
    """Download a file."""
    request = Request(url)  # noqa: S310
    logger.debug(f"Downloading {url} to {path} ...")
    with urlopen(request) as response, path.open("wb") as f:  # noqa: S310
        f.write(response.read())


def minsec(seconds: int) -> tuple[int, int]:
    """Return minutes and seconds."""
    spm = 60
    if seconds > spm:
        mins = seconds // spm
        secs = round(seconds % spm)
    else:
        mins = 0
        secs = seconds
    return mins, secs
