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
import queue

from websockets import ConnectionClosedOK, ConnectionClosed
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
    connection: ServerConnection
    send_queue: queue.Queue[str] = dataclasses.field(default_factory=queue.Queue)

    @classmethod
    def new(cls, connection: ServerConnection) -> Client:
        return cls(
            uid=str(uuid.uuid4()),
            secret=random.randint(0, 420),
            connection=connection,
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

        self._clients: set[Client] = set()

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

        client = Client.new(server)
        self._clients.add(client)

        server.send(json.dumps({"uid": client.uid, "secret": client.secret}))
        logger.info("Registered client %s with secret %d", client.uid, client.secret)

        while self.is_serving:
            try:
                client.connection.send(client.send_queue.get())

            except queue.Empty:
                pass

            except ConnectionClosed as err:
                logger.info("Client disconnected? (%s)", err)
                self._clients.remove(client)
                return None

            try:
                message = server.recv(timeout=0.1)

            except TimeoutError:
                continue

            except ConnectionClosedOK:
                logger.info("Client has disconnected from server: %s", server.id)
                return None

            logger.info("HANDLER: %s", message)

    def broadcast(self, message: str) -> None:
        """Queue a message to be delivered to all registered clients."""
        for client in self._clients.copy():
            client.send_queue.put(message)


def main() -> None:
    server = TimeServer("localhost", 5005)
    server.start()
    last_time_sent = 0
    try:
        while True:
            time.sleep(0.1)

            if int(time.time()) % 10 == 0 and int(time.time()) != last_time_sent:
                logger.info("Broadcasting time to all clients")
                last_time_sent = int(time.time())
                server.broadcast(f"Hello everyone! The unix time is currently {int(time.time())}")

    except KeyboardInterrupt:
        server.server.shutdown()
        server.join()
        logger.info("Server stopped.")
