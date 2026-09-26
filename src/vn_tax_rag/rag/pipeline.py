from __future__ import annotations

from vn_tax_rag.config import Settings
from vn_tax_rag.logging_setup import StepLoggerAdapter
from vn_tax_rag.rag.generate import build_context, generate_answer
from vn_tax_rag.rag.retrieve import retrieve
from vn_tax_rag.rag.store import collection_exists, get_collection


def run_ask(
    settings: Settings,
    log: StepLoggerAdapter,
    question: str,
    n_results: int = 4,
    tax_type: str | None = None,
    show_context: bool = False,
) -> str:
    log.step("rag.start", question=question[:80])
    if not collection_exists(settings):
        raise RuntimeError(
            f"Collection '{settings.collection_name}' not found. Run: vn-tax ingest"
        )

    collection = get_collection(settings)
    log.step(
        "rag.retrieve",
        n_results=n_results,
        tax_type=tax_type or "ALL",
        collection_count=collection.count(),
    )
    results = retrieve(collection, question, n_results=n_results, tax_type=tax_type)
    hits = len(results["ids"][0]) if results.get("ids") else 0
    log.step("rag.retrieve.done", hits=hits)

    if hits == 0:
        return "Không tìm thấy đoạn nào phù hợp trong dữ liệu hiện có."

    context = build_context(results)
    if show_context:
        print("\n=== Retrieved context ===\n")
        print(context)
        print("\n=== Answer ===\n")

    log.step("rag.generate", model=settings.llm_model)
    answer = generate_answer(settings, question, context)
    log.step("rag.generate.done", chars=len(answer))

    print("\nTrả lời:\n")
    print(answer)
    print("\nNguồn:")
    for index, (doc_id, meta, dist) in enumerate(
        zip(results["ids"][0], results["metadatas"][0], results["distances"][0]),
        start=1,
    ):
        print(
            f"  {index}. {meta.get('title')} | tax_type={meta.get('tax_type')} | "
            f"article={meta.get('article', '?')} | distance={dist:.4f} | id={doc_id}"
        )
        if meta.get("source_url"):
            print(f"     url: {meta.get('source_url')}")

    log.step("rag.done")
    return answer
