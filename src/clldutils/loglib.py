"""
This module provides

- a function to a logger configured for logging with color-coded log levels: :func:`get_colorlog`
- a context manager allowing changing log levels per context: :class:`Logging`

Usage:

.. code-block:: python

    >>> from clldutils.loglib import Logging, get_colorlog
    >>> log = get_colorlog(__name__)
    >>> log.debug('nothing to see')
    >>> with Logging(log, level=logging.DEBUG):
    ...     log.debug('but now')
    DEBUG   but now
"""
import logging

import colorlog

__all__ = ['get_colorlog', 'Logging']


def get_colorlog(name, stream=None, level=logging.INFO) -> logging.Logger:
    """
    Get a logger set up with `colorlog`'s formatter.
    """
    logging.basicConfig(level=level)
    handler = colorlog.StreamHandler(stream)
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-7s%(reset)s %(message)s'))
    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = False
    log.addHandler(handler)
    return log


class Logging(object):
    """
    A context manager to execute a block of code at a specific logging level.
    """

    def __init__(self, logger, level=logging.DEBUG):
        self.level = level
        self.logger = logger
        self.prev_level = self.logger.getEffectiveLevel()
        root = logging.getLogger()
        self.root_logger_level = root.getEffectiveLevel()
        self.root_handler_level = root.handlers[0].level if root.handlers else logging.WARNING

    def __enter__(self):
        self.logger.setLevel(self.level)
        if self.logger.handlers:
            self.logger.handlers[0].setLevel(self.level)
        root = logging.getLogger()
        root.setLevel(self.level)
        if root.handlers:
            root.handlers[0].setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.prev_level)
        root = logging.getLogger()
        root.setLevel(self.root_logger_level)
        if root.handlers:
            root.handlers[0].setLevel(self.root_handler_level)
