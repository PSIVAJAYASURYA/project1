import datetime
import os

class AppLogger:
    def __init__(self, logfile="logs/logs.txt"):
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        self.logfile = logfile

    def _write(self, level, source, message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{now}] [{level}] [{source}] {message}\n"
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(text)

    def log_info(self, message, source="APP"):
        self._write("INFO", source, message)

    def log_error(self, source, message):
        self._write("ERROR", source, message)
