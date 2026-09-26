from __future__ import annotations

from pathlib import Path

from vn_tax_rag.config import Settings
from vn_tax_rag.ingest.chunking import chunk_document, extract_dieu_number, strip_header
from vn_tax_rag.logging_setup import StepLoggerAdapter
from vn_tax_rag.rag.store import get_collection, upsert_chunks


def run_ingest(settings: Settings, log: StepLoggerAdapter) -> dict[str, int]:
    log.step("ingest.start", processed_dir=str(settings.processed_dir))
    settings.processed_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(settings.processed_dir.glob("*.txt"))
    log.step("ingest.files", count=len(files))
    if not files:
        log.step("ingest.empty")
        return {"files": 0, "chunks": 0}

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for path in files:
        raw = path.read_text(encoding="utf-8")
        file_meta, _ = strip_header(raw)
        chunks, method = chunk_document(raw)
        tax_type = (file_meta.get("tax_type") or "UNKNOWN").upper()
        title = file_meta.get("title") or path.stem
        source_url = file_meta.get("source_url") or file_meta.get("page_url") or ""

        log.step(
            "ingest.chunk",
            file=path.name,
            chunks=len(chunks),
            method=method,
            tax_type=tax_type,
        )

        for index, chunk in enumerate(chunks):
            doc_id = f"{path.stem}__{index:04d}"
            dieu = extract_dieu_number(chunk)
            meta = {
                "tax_type": tax_type,
                "title": title,
                "source": path.name,
                "source_url": source_url,
                "chunk_index": index,
                "chunk_method": method,
            }
            if dieu is not None:
                meta["article"] = dieu
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append(meta)

    collection = get_collection(settings, reset=True)
    upsert_chunks(collection, ids=ids, documents=documents, metadatas=metadatas)
    log.step("ingest.done", files=len(files), chunks=len(ids), collection=settings.collection_name)
    return {"files": len(files), "chunks": len(ids)}
