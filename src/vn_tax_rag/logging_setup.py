from __future__ import annotations

import logging
import sys
from pathlib import Path


STEP_PREFIX = "STEP"


class StepLoggerAdapter(logging.LoggerAdapter):
    def step(self, name: str, **fields: object) -> None:
        extras = " ".join(f"{key}={value}" for key, value in fields.items())
        message = f"{STEP_PREFIX} {name}"
        if extras:
            message = f"{message} {extras}"
        self.info(message)


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> StepLoggerAdapter:
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(level)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    return StepLoggerAdapter(logging.getLogger("vn_tax_rag"), {})
