# ==================================
#           ロガークラス
# ==================================


class Logger:
    def __init__(self, name: str) -> None:
        self._loggerName = name

    def log(self, component_name: str, data: object) -> None:
        print("[{}:{}] {}".format(self._loggerName, component_name, data))


# ==================================
#         ログベースクラス
# ==================================


class BaseLogger:
    def __init__(self) -> None:
        self._parent_class_name = self.__class__.__name__
        self._logger = Logger(self._parent_class_name)
        self.log('CTOR', 'Creating <{}> class'.format(self._parent_class_name))

    def __del__(self) -> None:
        self.log('DTOR', 'Destructing <{}> class'.format(self._parent_class_name))

    def log(self, component_name: str, data: object) -> None:
        self._logger.log(component_name, data)
