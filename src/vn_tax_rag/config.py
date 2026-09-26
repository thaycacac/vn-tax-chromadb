from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    chroma_path: Path
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    seeds_path: Path
    collection_name: str
    crawl_delay_seconds: float
    embedding_model: str
    llm_base_url: str | None
    llm_api_key: str
    llm_model: str


def _resolve(path_str: str, root: Path) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    return path


def load_settings(env_file: Path | None = None) -> Settings:
    root = PROJECT_ROOT
    dotenv_path = env_file or (root / ".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    data_dir = _resolve(os.getenv("DATA_DIR", "./data"), root)
    return Settings(
        project_root=root,
        chroma_path=_resolve(os.getenv("CHROMA_PATH", "./chroma_data"), root),
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        processed_dir=data_dir / "processed",
        seeds_path=_resolve(os.getenv("SEEDS_PATH", "./config/seeds.yaml"), root),
        collection_name=os.getenv("COLLECTION_NAME", "vn_tax_law"),
        crawl_delay_seconds=float(os.getenv("CRAWL_DELAY_SECONDS", "1.5")),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL",
            "paraphrase-multilingual-MiniLM-L12-v2",
        ),
        llm_base_url=os.getenv("LLM_BASE_URL") or None,
        llm_api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama",
        llm_model=os.getenv("LLM_MODEL", "qwen2.5:3b"),
    )
