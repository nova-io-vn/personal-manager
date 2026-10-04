import argparse
import logging
from logging.handlers import RotatingFileHandler

import uvicorn

from app.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_dir / "backend.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal Manager local backend")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Personal Manager backend on loopback port %s", args.port)
    try:
        uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="info", access_log=False, log_config=None)
    except Exception:
        logger.exception("Backend startup failed")
        raise


if __name__ == "__main__":
    main()
