"""
1. Connect to a server
1. Echo all server messages
1. When given a secret number, send it back
"""

from __future__ import annotations

import logging
import threading
import time

from websockets import ConnectionClosed
from websockets.sync.client import connect

logging.basicConfig(
    level="INFO",
    format="%(asctime)s : %(levelname)s : %(thread)s : %(message)s",
)
logger = logging.getLogger()


class TimeClient(threading.Thread):

    def __init__(self, uri: str) -> None:
        super().__init__()
        self.uri = uri
        self._is_running = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._is_running.is_set()

    def run(self) -> None:
        """Start the thread."""
        self._is_running.set()

        with connect(uri=self.uri) as websocket:
            logger.info("Client connected: %s", websocket.id)

            while self.is_running:

                try:

                    message = websocket.recv(timeout=0.2)

                except TimeoutError:
                    continue

                except ConnectionClosed as err:
                    logger.info("Server has disconnected: %s", err)
                    self._is_running.clear()
                    return None

                logger.info("Recieved message: %s", message)

    def stop(self) -> None:
        self._is_running.clear()


def main() -> None:
    client = TimeClient("ws://localhost:5005")
    client.start()

    try:
        while client.is_running:
            time.sleep(0.1)

    except KeyboardInterrupt:
        client.stop()

    finally:
        client.join()

    logger.info("Client stopped.")
