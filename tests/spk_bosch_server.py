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
        log.info('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        log.error('The server closed the connection')
        self.master.connected = None


class EchoServerClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('======== Server =========: Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data
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

    coro = loop.create_server(EchoServerClientProtocol, '127.0.0.1', 2048)
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
