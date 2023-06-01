import websockets.sync.server as ws
import websockets.exceptions as ws_except
import threading

from clova.general.logger import BaseLogger


class RemoteInteractionInterface(BaseLogger):
    _connected_clients = []
    _callbacks = []

    def __init__(self):
        super().__init__()
        self._ws_thread_stop_event = threading.Event()
        self._ws_thread = threading.Thread(target=self.init)
        self._ws_thread.daemon = True
        self._ws_thread.start()

    def __del__(self):
        self._ws_thread_stop_event.set()
        super().__del__()

    def init(self):
        self.log("init", "Starting up RII")
        with ws.serve(self.connection_handler, "0.0.0.0", 9876) as server:
            server.serve_forever()

    def connection_handler(self, conn):
        self._connected_clients.append(conn)

        self.log("connection_handler", "RII Adapter connected")

        while True:
            # アダプターからのメッセージをコールバック
            if self._ws_thread_stop_event.is_set():
                break

            try:
                message = conn.recv(timeout=1)
                self.log("connection_handler", "RII Invoking: {}".format(message))

                for cb in self._callbacks:
                    cb(message)
            except TimeoutError:
                continue
            except ws_except.ConnectionClosed:
                break

        self._connected_clients.remove(conn)

    def bind_message_callback(self, cb):
        self._callbacks.append(cb)

    def send_all(self, message):
        for conn in self._connected_clients:
            conn.send(message)


global_debug_interface = RemoteInteractionInterface()
