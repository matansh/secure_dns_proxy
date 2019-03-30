import logging
import os
from subprocess import getstatusoutput

import pytest

logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))


def _cmd(cmd: str) -> str:
    logging.debug('executing cli command: %s', cmd)
    status_code, output = getstatusoutput(cmd)
    assert status_code == 0, output  # will print output if status code is not 0
    return output


@pytest.fixture(scope='session', autouse=True)
def bring_up_instances():
    try:
        _cmd('docker-compose build')
        _cmd('docker-compose up -d')
        yield  # execute tests
    except:
        logging.exception('failed to bring up required containers')
    finally:
        _cmd('docker-compose down')  # in finally cuz we never wan't to leave orphan containers
