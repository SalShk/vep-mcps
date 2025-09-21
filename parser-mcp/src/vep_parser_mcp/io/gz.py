from __future__ import annotations
import gzip
from typing import TextIO

def open_read(path: str) -> TextIO:
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path, "r", encoding="utf-8")

def open_write(path: str) -> TextIO:
    return gzip.open(path, "wt") if path.endswith(".gz") else open(path, "w", encoding="utf-8")
