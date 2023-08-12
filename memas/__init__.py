from logging.config import fileConfig
# Configure root logger. This must happen here so it's configured before the child loggers are created.
fileConfig("logging.ini")
