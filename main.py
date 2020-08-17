import os
import sys
# import ssl
import logging
import asyncio
import websockets
import json
import argparse
# import http
import concurrent


class SignalServer(object):
    """
    Сигнальный сервер для WebRTC-подключения
    """
    def __init__(self, loop, options):
        self.loop = loop
        self.server = None
        self.addr = options.addr
        self.port = options.port
        self.keepalive_timeout = options.keepalive_timeout

    async def message_hanler(self, ws):
        message = await ws.recv()

        parse_msg = json.loads(message)

        if parse_msg['type'] == 'offer':
            """
            Здесь нужно будет пробросить полученный SDP дальше на бэкенд
            """
            sdp = parse_msg['sdp']

        if parse_msg['type'] == 'answer':
            """
            Здесь полученный от бэкенда SDP пробросим в браузер
            """

    async def recv_msg_ping(self, ws, raddr):
        '''
        Wait for a message forever, and send a regular ping to prevent bad routers
        from closing the connection.
        '''
        msg = None
        while msg is None:
            try:
                msg = await asyncio.wait_for(ws.recv(), self.keepalive_timeout)
            except (asyncio.TimeoutError, concurrent.futures._base.TimeoutError):
                print(f'Ping message to {raddr}')
                await ws.ping()
        return msg

    async def connection_handler(self, ws):
        raddr = ws.remote_address
        print(f'Новое подключение: {raddr}')
        while True:
            # Receive command, wait forever if necessary
            await self.recv_msg_ping(ws, raddr)
            await self.message_hanler(ws)

    def run(self):
        async def handler(ws, path):
            """
            Все входящие подключения копятся здесь
            """
            raddr = ws.remote_address
            print("Connected to {!r}".format(raddr))
            try:
                await self.connection_handler(ws)
            except websockets.ConnectionClosed:
                print("Connection to peer {!r} closed, exiting handler".format(raddr))

        print("Listening on https://{}:{}".format(self.addr, self.port))
        wsd = websockets.serve(handler, self.addr, self.port, max_queue=16)

        # Setup logging
        logger = logging.getLogger('websockets')
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())

        # Run the server
        self.server = self.loop.run_until_complete(wsd)

    async def stop(self):
        print('Stopping server... ', end='')
        self.server.close()
        await self.server.wait_closed()
        self.loop.stop()
        print('Stopped.')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--addr', default='', help='Address to listen on (default: all interfaces, both ipv4 and ipv6)')
    parser.add_argument('--port', default=8443, type=int, help='Port to listen on')
    parser.add_argument('--keepalive-timeout', dest='keepalive_timeout', default=30,
                        type=int, help='Timeout for keepalive (in seconds)')

    options = parser.parse_args(sys.argv[1:])

    loop = asyncio.get_event_loop()

    r = SignalServer(loop, options)

    print('Starting server...')
    while True:
        r.run()
        loop.run_forever()
        print('Restarting server...')


if __name__ == '__main__':
    main()
