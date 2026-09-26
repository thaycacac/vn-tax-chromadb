from __future__ import annotations

from openai import OpenAI

from vn_tax_rag.config import Settings

SYSTEM_PROMPT = """\
Bạn là trợ lý tra cứu luật thuế Việt Nam.
BẮT BUỘC: mọi câu trả lời phải viết bằng tiếng Việt (không dùng tiếng Anh).
Chỉ trả lời dựa trên CONTEXT được cung cấp.
Nếu CONTEXT không đủ, trả lời đúng câu: "Trong dữ liệu hiện có không đủ căn cứ để trả lời."
Khi trả lời, nêu căn cứ: tên văn bản và Điều (nếu có).
Không bịa thêm điều luật ngoài CONTEXT.
Trả lời ngắn gọn, rõ ràng, dễ hiểu.
"""


def build_llm_client(settings: Settings) -> OpenAI:
    kwargs: dict = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return OpenAI(**kwargs)


def build_context(results: dict) -> str:
    parts: list[str] = []
    for index, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0]),
        start=1,
    ):
        article = meta.get("article", "?")
        header = (
            f"[Đoạn {index}] van_ban={meta.get('title')} | loai_thue={meta.get('tax_type')} | "
            f"dieu={article} | distance={dist:.4f} | source={meta.get('source')}"
        )
        parts.append(f"{header}\n{doc}")
    return "\n\n---\n\n".join(parts)


def generate_answer(settings: Settings, question: str, context: str) -> str:
    client = build_llm_client(settings)
    user_prompt = (
        "Yêu cầu bắt buộc: hãy trả lời hoàn toàn bằng tiếng Việt.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"CÂU HỎI:\n{question}\n\n"
        "Viết câu trả lời bằng tiếng Việt, có nêu Điều/văn bản nếu có trong CONTEXT."
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
