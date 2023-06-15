import sqlite3
import os
import platform

from clova.general.logger import BaseLogger

from typing import Tuple

BASE_CONF_PATH = os.path.expanduser("~/.config")


class Database(BaseLogger):
    def __init__(self) -> None:
        super().__init__()

        if platform.system() == "Linux":
            if not os.path.isdir(BASE_CONF_PATH):
                os.mkdir(BASE_CONF_PATH)

            self.base_clova_path = os.path.join(BASE_CONF_PATH, "clova")
            self.db_path = os.path.join(BASE_CONF_PATH, "clova", "dat.db")
        else:
            self.log("CTOR", "Setting DB path to ./dat.db because platform.system() was not linux")
            self.base_clova_path = "."
            self.db_path = "./dat.db"

        if not os.path.isdir(self.base_clova_path):
            os.mkdir(self.base_clova_path)

        self.connect_db()

    def __del__(self) -> None:
        self.conn.close()
        return super().__del__()

    def connect_db(self) -> None:
        self.log("connect_db", "Connecting to sqlite3 db: {}".format(self.db_path))
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

    def execute(self, query: str, commit: bool) -> Tuple[Tuple[object]]:
        self.log("execute", "> {}".format(query))

        cur = self.conn.cursor()
        cur.execute(query)

        result = cur.fetchall()

        if commit:
            self.conn.commit()

        cur.close()
        return result  # type: ignore[return-value]
