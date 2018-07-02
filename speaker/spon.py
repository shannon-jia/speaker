#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import logging
import socket
import struct

log = logging.getLogger(__name__)


class Spon(object):

    HEAD = b'\xFF\xFF'
    ACTION = {
        'CALL': 0x00,
        'ANSWER': 0x01,
        'HANGUP': 0x02,
        'STOP': 0x00,
        'START': 0x01,
        'STOP_EXT': 0x02,
        'START_EXT': 0x03,
        'STOP_SINGLE': 0x04,
        'START_SINGLE': 0x05
    }

    def __init__(self, host, port, local_term=1, broadcast_term=1):
        self.server_address = (host, port)
        self.local_term = local_term
        self.broadcast_term = broadcast_term
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(1)
        self.sock.settimeout(0.1)
        self.send_str = b''
        log.info('Connect to server {}: {}'.format(self.server_address,
                                                   self.sock))

    def sends(self):
        return self.send_to_server(self.send_str)

    def send_to_server(self, message):
        # send data
        data = None
        try:
            log.debug('Send to {}: {}'.format(self.server_address, message))
            self.sock.sendto(message, self.server_address)
            data, address = self.sock.recvfrom(1024)
            log.debug('Received from {}: {}'.format(address, data))
        except socket.error as e:
            log.error('Socket exception: {}'.format(e))
        except Exception as e:
            log.error('Other exception: {}'.format(e))
        finally:
            return data

    def terminal_control(self, action, dest, src_term=None):
        src = src_term or self.local_term
        act = self.ACTION.get(action.upper())
        if act is None:
            return None
        self.send_str = self.HEAD + b'\xC1'
        s = struct.Struct('<BHH')
        values = (act, src, dest)
        self.send_str += s.pack(*values)
        log.info('{} [0xC1]terminal_control({},{})'.format(action, dest, src))
        return self.sends()

    def broadcast_control(self, action, dests, src_term=None):
        src = src_term or self.broadcast_term
        if action.upper() == 'STOP':
            act = 0x00
        else:
            act = 0x01
        self.send_str = self.HEAD + b'\xC3'
        s = struct.Struct('<BHH')
        values = (act, src, 0x00)
        self.send_str += s.pack(*values)
        bits = []
        for i in range(16):
            bits.append(0x00)
        for d in dests:
            if (d > 128) or (d < 1):
                continue
            x = (d - 1) // 8
            y = (d - 1) - (x * 8)
            bits[x] |= (1 << y)
        p = struct.Struct('B')
        for i in range(16):
            self.send_str += p.pack(bits[i])
        log.info('{} broadcast[0xC3]_control({},{})'.format(action,
                                                            dests,
                                                            src))
        return self.sends()

    def broadcast_extend(self, action, dests, src_term=None):
        src = src_term or self.broadcast_term
        if action.upper() == 'STOP':
            act = 0x02
        else:
            act = 0x03
        self.send_str = self.HEAD + b'\xC3'
        s = struct.Struct('<BHH')
        values = (act, src, 0x00)
        self.send_str += s.pack(*values)
        bits = []
        for i in range(125):
            bits.append(0x00)
        for d in dests:
            if (d > 1000) or (d < 1):
                continue
            x = (d - 1) // 8
            y = (d - 1) - (x * 8)
            bits[x] |= (1 << y)
        p = struct.Struct('B')
        for i in range(125):
            self.send_str += p.pack(bits[i])
        log.info('{} broadcast[0xC3]_extend({},{})'.format(action, dests, src))
        return self.sends()

    def broadcast_single(self, action, dest, zone=0):
        if action.upper() == 'STOP':
            act = 0x04
        else:
            act = 0x05
        self.send_str = self.HEAD + b'\xC3'
        s = struct.Struct('<BHH')
        values = (act, dest, zone)
        self.send_str += s.pack(*values)
        log.info('{} broadcast[0xC3]_single({},{})'.format(action, dest, zone))
        return self.sends()

    def alarm_task(self, action, task, zone=0):
        if action.upper() == 'STOP':
            act = 0x00
        else:
            act = 0x01
        self.send_str = self.HEAD + b'\xCA'
        s = struct.Struct('<BHH')
        values = (act, task, 0)
        self.send_str += s.pack(*values)
        log.info('{} Alarm_Task[0xCA]({})'.format(action, task))
        return self.sends()


if __name__ == '__main__':
    log = logging.getLogger("")
    formatter = logging.Formatter("%(asctime)s %(levelname)s " +
                                  "[%(module)s:%(lineno)d] %(message)s")
    # log the things
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # ch.setLevel(logging.CRITICAL)
    # ch.setLevel(logging.INFO)

    ch.setFormatter(formatter)
    log.addHandler(ch)

    host = '192.168.1.169'
    port = 2048

    spon = Spon(host, port)

    message = b'\xff\xff\xc1\x00\x02\x00\x03\x00'
    reps = spon.send_to_server(message)
    log.info('Received: {}'.format(reps))

    message = b'\xff\xff\xcc\x00\x00\x00\x00\x00'
    reps = spon.send_to_server(message)
    log.info('Received: {}'.format(reps))

    message = b'\xff\xff\xc6\x00\x02\x00\x00\x00'
    reps = spon.send_to_server(message)
    log.info('Received: {}'.format(reps))

    spon.terminal_control('call', 2, 3)
    spon.terminal_control('answer', 4, 3)
    spon.terminal_control('hangup', 4, 3)

    spon.broadcast_control('start', [3, 4, 5, 16,
                                     98, 128, 127, 26], 4)
    spon.broadcast_control('stop', [3, 4], 2)
    spon.broadcast_extend('start', [3, 4, 5, 16,
                                    98, 128, 200, 256,
                                    345, 998, 1000], 3)
    spon.broadcast_extend('stop', [3], 4)
    spon.broadcast_single('start', 4, 3)
    print(spon.broadcast_single('stop', 4, 3))
