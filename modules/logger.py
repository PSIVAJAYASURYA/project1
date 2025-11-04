import os
from datetime import datetime


class AppLogger:
    def __init__(self, log_file="logs/error_log.txt"):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.log_file = log_file

    def _write_log(self, level, source, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] [{source}] {message}\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_info(self, source, message):
        self._write_log("INFO", source, message)

    def log_error(self, source, message):
        self._write_log("ERROR", source, message)
