import logging

def get_route_logger(name: str):
    """
    A standard logger factory for routes
    """
    return logging.getLogger(name)
