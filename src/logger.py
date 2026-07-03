# Fichier : src/logger.py
# Logging centralise : fichier tournant dans logs/ + console.
import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = "logs"


def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        fh = RotatingFileHandler(
            os.path.join(_LOG_DIR, "networksentinel.log"),
            maxBytes=500_000,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        # Pas de dossier logs accessible (ex: droits) : console uniquement.
        pass
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger
