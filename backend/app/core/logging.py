import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # Third-party clients are noisy at INFO level and may log request URLs.
    for noisy in ("httpx", "httpcore", "google_genai", "groq", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
