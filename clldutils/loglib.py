# coding: utf8
from __future__ import unicode_literals, print_function, division
import logging

import colorlog


def get_colorlog(name, stream=None, level=logging.INFO):
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
        self.root_handler_level = root.handlers[0].level

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
