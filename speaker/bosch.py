#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import asyncio
import logging

log = logging.getLogger(__name__)


class TcpClientProtocol(asyncio.Protocol):

    def __init__(self, master):
        self.master = master

    def connection_made(self, transport):
        self.transport = transport
        self.master.connected = True

    def data_received(self, data):
        log.debug('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        log.error('The server closed the connection')
        self.master.connected = None


class Bosch(object):
    TYPE_OIP_Login = b'\x02\x70\x44\x00\x22\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x61\x64\x6d\x69\x6e\x05\x00\x00\x00\x61\x64\x6d\x69\x6e'
    TYPE_OIP_StartCall = b'\x03\x70\x44\x00\x39\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x50\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x41\x4c\x4c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x78\x69\x61\x6f\x66\x61\x6e\x67'
    TYPE_OIP_KeepAlive = b'\x27\x70\x44\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    def __init__(self, loop, host, port,
                 user='admin', passwd='admin'):
        self.loop = loop
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.connected = None
        self.loop.create_task(self._do_connect())
        self.transport = None
        self.loop.call_later(6, self.keepAlive)

    async def _do_connect(self):
        while True:
            await asyncio.sleep(5)
            if self.connected:
                continue
            try:
                xt, _ = await self.loop.create_connection(
                    lambda: TcpClientProtocol(self),
                    self.host,
                    self.port)
                log.info('Connection create on {}'.format(xt))
                self.transport = xt
                self.login()
            except OSError:
                log.error('Server not up retrying in 5 seconds...')
            except Exception as e:
                log.error('Error when connect to server: {}'.format(e))

    def call(self, cmd):
        if self.transport:
            self.transport.write(cmd)
            log.debug('send cmd to server: {}'.format(cmd))
        else:
            log.error('Invalid server transport.')

    def login(self):
        log.info('send cmd to server: [login]')
        self.call(self.TYPE_OIP_Login)

    def keepAlive(self):
        log.info('send cmd to server: [keepAlive]')
        self.call(self.TYPE_OIP_KeepAlive)
        self.loop.call_later(5, self.keepAlive)

    def startCall(self):
        log.info('send cmd to server: [startCall]')
        self.call(self.TYPE_OIP_StartCall)


class EchoServerClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('======== Server =========: Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('======== Server =========: Data received: {!r}'.format(message))

        print('======== Server =========: Send: {!r}'.format(message))
        self.transport.write(data)

        #
        # print('Close the client socket')
        # self.transport.close()


if __name__ == '__main__':
    log = logging.getLogger("")
    formatter = logging.Formatter("%(asctime)s %(levelname)s " +
                                  "[%(module)s:%(lineno)d] %(message)s")
    # log the things
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(formatter)
    log.addHandler(ch)

    loop = asyncio.get_event_loop()

    bosch = Bosch(loop,
                  '127.0.0.1',
                  8888)

    coro = loop.create_server(EchoServerClientProtocol, '127.0.0.1', 8888)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
