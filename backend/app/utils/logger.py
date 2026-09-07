import logging


def get_logger(name: str) -> logging.Logger:
    """Return a module logger and let the ASGI/runtime logging config own handlers."""
    return logging.getLogger(name)
