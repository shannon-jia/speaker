# -*- coding: utf-8 -*-

"""Main module."""

import logging
from urllib.parse import urlparse
from .speaker import SpeakerV1
from .bosch import Bosch
log = logging.getLogger(__name__)


class Speaker_Bosch(SpeakerV1):
    """
    Spon Speaker system driver for SAM V1
    """

    CLIENT_UDP_TIMEOUT = 5.0

    def __init__(self, loop, spk_svr, release_time=20,
                 user='admin', passwd='admin'):
        super().__init__(loop)
        _url = urlparse(spk_svr)
        self.host = _url.hostname or 'localhost'
        self.port = _url.port or 2048
        self.timeout = release_time
        self.server = Bosch(self.loop,
                            self.host, self.port,
                            user, passwd)

    def __str__(self):
        return "Speaker V1 and Bosch system"

    async def _do_action(self, act, args=None, status=None):
        act_list = act.split('_')
        if (len(act_list) < 2):
            log.warn('Invalid speaker device name: {}'.format(act))
            return False
        if act_list[0].upper() != 'SPK':
            log.warn('Invalid speaker device name: {}'.format(act))
            return False
        dest_id = int(act_list[1])
        if status == 'AUTO':
            self._register(act, status, self.timeout+1)
        else:
            self._register(act, status, 0)
        if status == 'OFF':
            cmd = 'stop'
        else:
            cmd = 'start'
        log.debug('Cmd: {}, dest_id: {}'.format(cmd, dest_id))
        if self.server:
            reps = self.server.startCall()
            log.info('Received from speaker server: {}'.format(reps))
        else:
            log.error('invalid speaker server.')

    def _release(self, act, args=None, status='OFF'):
        # act_list = act.split('_')
        # if (len(act_list) < 2):
        #     log.warn('Invalid speaker device name: {}'.format(act))
        #     return False
        # if act_list[0].upper() != 'SPK':
        #     log.warn('Invalid speaker device name: {}'.format(act))
        #     return False
        # dest_id = int(act_list[1])
        # if self.server:
        #     reps = self.server.alarm_task('stop', dest_id)
        #     log.info('Received from speaker server: {}'.format(reps))
        # else:
        #     log.error('invalid speaker server.')
        return
