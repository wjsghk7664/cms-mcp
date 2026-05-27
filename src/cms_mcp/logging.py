from __future__ import annotations

import logging


def configure_logging(level: str = "WARNING") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.WARNING))
    for name in ("httpx", "httpcore", "mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)

