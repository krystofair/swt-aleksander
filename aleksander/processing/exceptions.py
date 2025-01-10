"""
    I didn't like explaining obvious things. :)
    But here you have classes for exceptions to do error handling in elegant way.
    For example, when something raise you only handle errors you know, others are probably BUGs. :)
    Btw exceptions should be like DomainEvents and contain only necessary information about error.
"""

class ProcessorException(Exception):
    """Base class for exceptions in processors."""
    pass
