import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


APP_FOLDER = "RS3D Printer Status Bar"


def log_directory():
    candidates = []
    if os.environ.get("PROGRAMDATA"):
        candidates.append(Path(os.environ["PROGRAMDATA"]) / APP_FOLDER / "logs")
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / APP_FOLDER / "logs")
    candidates.append(Path(__file__).resolve().parent.parent / "logs")
    for folder in candidates:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            probe = folder / f".write-test-{os.getpid()}"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return folder
        except OSError:
            continue
    return Path.cwd()


LOG_DIR = log_directory()


def get_file_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    target = str(LOG_DIR / filename)
    if not any(getattr(handler, "baseFilename", None) == target for handler in logger.handlers):
        handler = RotatingFileHandler(target, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(process)d | %(threadName)s | %(message)s"
        ))
        logger.addHandler(handler)
    return logger
