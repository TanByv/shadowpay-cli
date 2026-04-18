import datetime
from pathlib import Path

DEBUG_LOG_FILE = Path("debug_raw.log")


def log_raw_data(direction: str, transport: str, data: str) -> None:
    """Log raw data to a file with timestamp and metadata."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{transport}] [{direction}]\n{data}\n{'-' * 80}\n"

    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
