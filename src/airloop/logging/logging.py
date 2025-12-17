import logging

def get_logger(name: str):
    logger = logging.getLogger(name=__name__)
    return logger
    