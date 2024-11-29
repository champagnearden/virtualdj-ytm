from datetime import datetime
class Logger:
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    DEBUG = log_levels[0]
    INFO = log_levels[1]
    WARNING = log_levels[2]
    ERROR = log_levels[3]
    CRITICAL = log_levels[4]
    
    def __init__(self, log_level):
        self.log_level = log_level

    def write_in_file(self, message):
        with open("vdj.log", "a", encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {message}\n")

    def log(self, message, level):
        msg = f"[{level}] {message}"
        if (self.log_levels.index(level) >= self.log_levels.index(self.log_level)):
            print(msg)
            self.write_in_file(msg)