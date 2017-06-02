#!/usr/bin/env python3.6
import json
import logging
import subprocess
import time

import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def absolute(p):
    return os.path.join(os.environ['CODEBUILD_SRC_DIR'], p)


def execute(c):
    logger.info('COMMAND ==> ' + c)
    c = subprocess.call(c, shell=True)
    logger.info('CODE ==> ' + str(c))
    return c


logger.info('Creating environment')
execute('virtualenv -p python3.6 {}'.format(absolute('venv')))

logger.info('Install requirement')
execute('{} install -r {}'.format(absolute('venv/bin/pip'), absolute('requirements.txt')))

stages = []

with open(absolute('zappa_settings.json')) as json_data:
    zappa = json.load(json_data)
    if 'api' in zappa:
        stages.append('api')
    if 'client' in zappa:
        stages.append('client')

for stage in stages:

    if os.environ['BRANCH'] != 'master':
        stage = stage + '_' + os.environ['BRANCH']

    logger.info('Sleeping for 30 seconds')
    time.sleep(30)

    logger.info('Trying to update zappa')
    code = execute('. {}; zappa update {}'.format(absolute('venv/bin/activate'), stage))

    if code != 0:
        logger.info('Update to zappa failed. Trying to deploy zappa')
        code = execute('. {}; zappa deploy {}'.format(absolute('venv/bin/activate'), stage))

        if code != 0:
            logger.debug('{} update or deploy not found!'.format(stage.capitalize()))
