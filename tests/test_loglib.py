import logging
import sys

from clldutils.loglib import Logging, get_colorlog


def test_get_colorlog(capsys):
    def run():
        log = get_colorlog(__name__, sys.stdout)
        log.info('msg')

    run()
    out, err = capsys.readouterr()
    assert 'msg' in out


def test_Logging_context_manager(capsys):
    def run():
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.WARN)

        logger.warning('warn')
        logger.debug('debug1')

        with Logging(logger):
            logger.debug('debug2')

    run()
    out, err = capsys.readouterr()
    assert out.split() == ['warn', 'debug2']
