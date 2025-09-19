"""
1. Start a server
1. On join, send a welcome message with a client id
1. On join, register websocket with the id and a secret number
1. Once a minute, broadcast the current time
1. Once a minute, tell specific websockets their secret number
1. Clean up all connections on sigterm
"""

from __future__ import annotations

import dataclasses
import json
import logging
import threading
import time
import random
import uuid

from websockets import ConnectionClosedOK
from websockets.sync.server import ServerConnection
from websockets.sync.server import serve

logging.basicConfig(
    level="INFO",
    format="%(asctime)s : %(levelname)s : %(thread)s : %(message)s",
)
logger = logging.getLogger()


@dataclasses.dataclass(frozen=True)
class Client:
    uid: str
    secret: int

    @classmethod
    def new(cls) -> Client:
        return cls(
            uid=str(uuid.uuid4()),
            secret=random.randint(0, 420),
        )


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
        self._serving = threading.Event()

    @property
    def is_serving(self) -> bool:
        return self._serving.is_set()

    def run(self) -> None:
        """Start the thread."""
        logger.info("Starting TimeServer...")
        self._serving.set()
        self.server.serve_forever()
        self._serving.clear()

    def handler(self, server: ServerConnection) -> None:
        logger.info("Handler triggered: %s", server.id)

        client = Client.new()
        server.send(json.dumps({"uid": client.uid, "secret": client.secret}))
        logger.info("Registered client %s with secret %d", client.uid, client.secret)

        while self.is_serving:
            try:
                message = server.recv(timeout=0.2)

            except TimeoutError:
                continue

            except ConnectionClosedOK:
                logger.info("Client has disconnected from server: %s", server.id)
                return None

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
