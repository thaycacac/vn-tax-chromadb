from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from vn_tax_rag.config import Settings
from vn_tax_rag.crawl.extract import (
    find_pdf_links,
    html_to_text,
    looks_like_law_body,
    pdf_to_text,
)
from vn_tax_rag.crawl.fetcher import Fetcher
from vn_tax_rag.crawl.seeds import Seed, load_seeds
from vn_tax_rag.logging_setup import StepLoggerAdapter


def _write_processed(path: Path, seed: Seed, source_url: str, body: str) -> None:
    header = {
        "id": seed.id,
        "tax_type": seed.tax_type,
        "title": seed.title,
        "source_url": source_url,
        "page_url": seed.url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    lines = [f"{key}: {value}" for key, value in header.items()]
    content = "\n".join(lines) + "\n---\n\n" + body.strip() + "\n"
    path.write_text(content, encoding="utf-8")


def crawl_seed(
    seed: Seed,
    settings: Settings,
    fetcher: Fetcher,
    log: StepLoggerAdapter,
) -> bool:
    raw_dir = settings.raw_dir / seed.id
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_path = settings.processed_dir / f"{seed.id}.txt"
    settings.processed_dir.mkdir(parents=True, exist_ok=True)

    log.step("crawl.fetch", id=seed.id, url=seed.url)
    html_bytes = b""
    status = 0
    content_type = ""
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            status, html_bytes, content_type = fetcher.get_bytes(seed.url)
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log.step("crawl.fetch.retry", id=seed.id, attempt=attempt, error=str(exc))
            time.sleep(settings.crawl_delay_seconds * attempt)

    if last_error is not None:
        log.step("crawl.fetch.failed", id=seed.id, error=str(last_error))
        return False

    log.step("crawl.fetch.done", id=seed.id, status=status, content_type=content_type)

    if status >= 400:
        log.step("crawl.fetch.failed", id=seed.id, status=status)
        return False

    html_path = raw_dir / "page.html"
    html_path.write_bytes(html_bytes)
    html = html_bytes.decode("utf-8", errors="replace")

    meta_path = raw_dir / "meta.json"
    meta_path.write_text(
        json.dumps(
            {
                "id": seed.id,
                "tax_type": seed.tax_type,
                "title": seed.title,
                "url": seed.url,
                "status": status,
                "content_type": content_type,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    body = ""
    source_url = seed.url

    if "pdf" in content_type.lower() or seed.url.lower().endswith(".pdf"):
        body = pdf_to_text(html_bytes)
        (raw_dir / "document.pdf").write_bytes(html_bytes)
    else:
        text_from_html = html_to_text(html)
        pdf_links = find_pdf_links(html, seed.url)
        log.step("crawl.pdf_links", id=seed.id, count=len(pdf_links))

        # Prefer PDF attachments; Cong Bao HTML pages are metadata shells.
        for pdf_url in pdf_links:
            log.step("crawl.fetch_pdf", id=seed.id, url=pdf_url)
            try:
                pdf_status, pdf_bytes, pdf_ct = fetcher.get_bytes(pdf_url)
            except Exception as exc:  # noqa: BLE001
                log.step("crawl.fetch_pdf.failed", id=seed.id, error=str(exc))
                continue
            log.step(
                "crawl.fetch_pdf.done",
                id=seed.id,
                status=pdf_status,
                content_type=pdf_ct,
                bytes=len(pdf_bytes),
            )
            if pdf_status >= 400 or len(pdf_bytes) < 1000:
                continue
            (raw_dir / "document.pdf").write_bytes(pdf_bytes)
            try:
                candidate = pdf_to_text(pdf_bytes)
            except Exception as exc:  # noqa: BLE001
                log.step("crawl.pdf_extract.failed", id=seed.id, error=str(exc))
                continue
            log.step("crawl.pdf_extract", id=seed.id, chars=len(candidate))
            if looks_like_law_body(candidate) or len(candidate) > len(body):
                body = candidate
                source_url = pdf_url
            if looks_like_law_body(body):
                break

        if not looks_like_law_body(body) and looks_like_law_body(text_from_html):
            body = text_from_html
            source_url = seed.url
        elif not body and text_from_html:
            body = text_from_html
            source_url = seed.url

    if not body or len(body) < 200:
        log.step("crawl.empty", id=seed.id, chars=len(body))
        return False

    _write_processed(processed_path, seed, source_url, body)
    log.step(
        "crawl.processed",
        id=seed.id,
        path=str(processed_path),
        chars=len(body),
    )
    return True


def run_crawl(settings: Settings, log: StepLoggerAdapter) -> dict[str, int]:
    log.step("crawl.start", seeds=str(settings.seeds_path))
    seeds = load_seeds(settings.seeds_path)
    log.step("crawl.seeds_loaded", count=len(seeds))

    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher()
    ok = 0
    failed = 0
    try:
        for index, seed in enumerate(seeds):
            success = crawl_seed(seed, settings, fetcher, log)
            if success:
                ok += 1
            else:
                failed += 1
            if index < len(seeds) - 1:
                time.sleep(settings.crawl_delay_seconds)
    finally:
        fetcher.close()

    log.step("crawl.done", ok=ok, failed=failed)
    return {"ok": ok, "failed": failed, "total": len(seeds)}
