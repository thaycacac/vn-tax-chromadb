from vn_tax_rag.ingest.chunking import chunk_document, extract_dieu_number, split_by_dieu


def test_split_by_dieu():
    text = """Preamble

Điều 1. Scope
This law covers tax.

Điều 2. Taxpayers
Individuals and organizations.
"""
    chunks = split_by_dieu(text)
    assert len(chunks) == 2
    assert chunks[0].startswith("Điều 1")
    assert extract_dieu_number(chunks[1]) == "2"


def test_chunk_document_with_header():
    text = """id: demo
tax_type: TNCN
title: Demo
---

Điều 1. One
Body one

Điều 2. Two
Body two
"""
    chunks, method = chunk_document(text)
    assert method == "dieu"
    assert len(chunks) == 2
