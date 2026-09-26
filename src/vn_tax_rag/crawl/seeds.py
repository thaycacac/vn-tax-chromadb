from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Seed:
    id: str
    tax_type: str
    title: str
    url: str


def load_seeds(path: Path) -> list[Seed]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("seeds") or []
    seeds: list[Seed] = []
    for item in items:
        seeds.append(
            Seed(
                id=str(item["id"]),
                tax_type=str(item["tax_type"]).upper(),
                title=str(item["title"]),
                url=str(item["url"]),
            )
        )
    return seeds
