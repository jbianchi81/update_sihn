class Logger:
    LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
    
    def __init__(self, level='INFO'):
        self.level = self.LEVELS.get(level.upper(), 20)

    def log(self, level, message):
        if self.LEVELS.get(level, 20) >= self.level:
            print(f"{level}: {message}")

    def debug(self, message):
        self.log('DEBUG', message)

    def info(self, message):
        self.log('INFO', message)

    def warning(self, message):
        self.log('WARNING', message)

    def error(self, message):
        self.log('ERROR', message)

    def critical(self, message):
        self.log('CRITICAL', message)

# Example usage
# logger = Logger(level='DEBUG')
# logger.debug("This is a debug message")
# logger.info("This is an info message")

