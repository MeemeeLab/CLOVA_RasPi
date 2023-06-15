import websockets.sync.server as ws
import websockets.exceptions as ws_except
import threading

from typing import List, Callable

from clova.general.logger import BaseLogger


class RemoteInteractionInterface(BaseLogger):
    _connected_clients: List[ws.ServerConnection] = []
    _callbacks: List[Callable[[str], None]] = []

    def __init__(self) -> None:
        super().__init__()
        self._ws_thread_stop_event = threading.Event()
        self._ws_thread = threading.Thread(target=self.init)
        self._ws_thread.daemon = True
        self._ws_thread.start()

    def __del__(self) -> None:
        self._ws_thread_stop_event.set()
        super().__del__()

    def init(self) -> None:
        self.log("init", "Starting up RII")
        with ws.serve(self.connection_handler, "0.0.0.0", 9876) as server:
            server.serve_forever()

    def connection_handler(self, conn: ws.ServerConnection) -> None:
        self._connected_clients.append(conn)

        self.log("connection_handler", "RII Adapter connected")

        while True:
            # アダプターからのメッセージをコールバック
            if self._ws_thread_stop_event.is_set():
                break

            try:
                message = conn.recv(timeout=1)

                if isinstance(message, bytes):
                    self.log("connection_handler", "Received byte message; This message will be ignored as it's not supported.")
                    continue

                self.log("connection_handler", "RII Invoking: {}".format(message))

                for cb in self._callbacks:
                    cb(message)
            except TimeoutError:
                continue
            except ws_except.ConnectionClosed:
                break

        self._connected_clients.remove(conn)

    def bind_message_callback(self, cb: Callable[[str], None]) -> None:
        self._callbacks.append(cb)

    def send_all(self, message: str) -> None:
        for conn in self._connected_clients:
            conn.send(message)
