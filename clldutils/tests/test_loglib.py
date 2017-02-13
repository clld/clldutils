# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
import logging
import sys

from clldutils.testing import capture


class LogTest(TestCase):
    def test_get_colorlog(self):
        from clldutils.loglib import get_colorlog

        def run():
            log = get_colorlog(__name__, sys.stdout)
            log.info('msg')

        with capture(run) as out:
            self.assertIn('msg', out)

    def test_Logging_context_manager(self):
        from clldutils.loglib import Logging

        def run():
            logger = logging.getLogger(__name__)
            logger.addHandler(logging.StreamHandler(sys.stdout))
            logger.setLevel(logging.WARN)

            logger.warn('warn')
            logger.debug('debug1')

            with Logging(logger):
                logger.debug('debug2')

        with capture(run) as out:
            self.assertEqual(out.split(), ['warn', 'debug2'])
