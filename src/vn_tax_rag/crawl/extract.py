from __future__ import annotations

import io
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pypdf import PdfReader


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return normalize_whitespace(text)


def find_pdf_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith(("javascript:", "mailto:", "#")):
            continue
        label = (a.get_text(" ", strip=True) or "").lower()
        abs_url = urljoin(page_url, href)
        if not abs_url.lower().startswith(("http://", "https://")):
            continue
        if abs_url in seen:
            continue

        score = 0
        if href.lower().endswith(".pdf") or abs_url.lower().endswith(".pdf"):
            score += 5
        if ".pdf" in label or label.endswith("pdf"):
            score += 4
        if "download" in href.lower() or "cdnchinhphu" in abs_url.lower():
            score += 2
        if "datafiles.chinhphu.vn" in abs_url.lower():
            score += 1
        if "pdf" in label or "đính kèm" in label or "tai lieu" in label:
            score += 1

        if score > 0:
            seen.add(abs_url)
            scored.append((score, abs_url))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in scored]


def pdf_to_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return normalize_whitespace("\n".join(parts))


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def looks_like_law_body(text: str) -> bool:
    if len(text) < 2000:
        return False
    required = ("Điều 1", "Điều 2")
    if not all(marker in text for marker in required):
        return False
    article_hits = len(re.findall(r"Điều\s+\d+", text))
    return article_hits >= 3
