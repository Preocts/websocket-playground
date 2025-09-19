"""
1. Start a server
1. On join, send a welcome message with a client id
1. On join, register websocket with the id and a secret number
1. Once a minute, broadcast the current time
1. Once a minute, tell specific websockets their secret number
1. Clean up all connections on sigterm
"""

from __future__ import annotations

import time
import threading
import logging

from websockets.sync.server import serve
from websockets.sync.server import ServerConnection

logging.basicConfig(
    level="INFO",
    format="%(asctime)s : %(levelname)s : %(thread)s : %(message)s",
)
logger = logging.getLogger()


class TimeServer(threading.Thread):

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.server = serve(
            handler=self.handler,
            host=self.host,
            port=self.port,
            # process_request=self.process_request,
        )

    def run(self) -> None:
        """Start the thread."""
        logger.info("Starting TimeServer...")
        self.server.serve_forever()

    @staticmethod
    def handler(server: ServerConnection) -> None:
        logger.info("Handler triggered: %s", server.id)
        while True:
            message = server.recv()
            logger.info("HANDLER: %s", message)


def main() -> None:
    server = TimeServer("localhost", 5005)
    server.start()

    try:
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        server.server.shutdown()
        server.join()
        logger.info("Server stopped.")
