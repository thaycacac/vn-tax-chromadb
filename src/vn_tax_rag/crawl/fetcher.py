from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger("vn_tax_rag")

DEFAULT_HEADERS = {
    "User-Agent": (
        "vn-tax-rag/0.1 (+https://github.com/local/vn-tax-rag; research crawler; "
        "respectful rate-limited fetches of public legal texts)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "vi,en;q=0.8",
}


class Fetcher:
    def __init__(self, timeout: float = 90.0, verify_ssl: bool = False) -> None:
        # Some government CDN endpoints present incomplete certificate chains.
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
            verify=verify_ssl,
        )

    def close(self) -> None:
        self._client.close()

    def get_bytes(self, url: str) -> tuple[int, bytes, str]:
        if not url.lower().startswith(("http://", "https://")):
            raise ValueError(f"Unsupported URL scheme: {url}")
        response = self._client.get(url)
        content_type = response.headers.get("content-type", "")
        return response.status_code, response.content, content_type

    def get_text(self, url: str) -> tuple[int, str]:
        status, content, _ = self.get_bytes(url)
        return status, content.decode("utf-8", errors="replace")


def absolutize(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def is_http_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))


def is_pdf_url(url: str, content_type: str = "") -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or "application/pdf" in content_type.lower()
