from __future__ import annotations

import re


DIEU_PATTERN = re.compile(r"(?=^Điều\s+\d+)", re.MULTILINE)


def strip_header(text: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    body = text
    if "\n---" in text:
        header, body = text.split("\n---", 1)
        for line in header.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip()
    return meta, body.strip()


def split_by_dieu(text: str) -> list[str]:
    parts = DIEU_PATTERN.split(text)
    chunks = [
        part.strip()
        for part in parts
        if part.strip() and re.match(r"^Điều\s+\d+", part.strip())
    ]
    return chunks


def split_by_size(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def extract_dieu_number(chunk: str) -> str | None:
    match = re.match(r"Điều\s+(\d+)", chunk)
    return match.group(1) if match else None


def chunk_document(text: str) -> tuple[list[str], str]:
    meta, body = strip_header(text)
    _ = meta
    chunks = split_by_dieu(body)
    method = "dieu"
    if not chunks:
        # Keep preamble before first Điều as its own chunk when present
        chunks = split_by_size(body)
        method = "size"
    return chunks, method
