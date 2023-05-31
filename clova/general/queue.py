from collections import deque
import regex as re

from clova.general.logger import BaseLogger

# ==================================
#          発話キュークラス
# ==================================


class SpeechQueue(BaseLogger):
    REGEX_ASSUME_EMPTY = re.compile("^[\\p{P}|\\p{S}|\\p{Z}|\n]*$")

    # コンストラクタ
    def __init__(self):
        super().__init__()

        self._queue = deque()

    # デストラクタ
    def __del__(self):
        super().__del__()

    # 文字列・関数をキューに格納する
    def add(self, str_or_func):
        if callable(str_or_func):
            self.log("add", "SpeechQueue += function()")
            self._queue.append(str_or_func)
            return
        if str_or_func.strip() == "" or self.REGEX_ASSUME_EMPTY.match(str_or_func) is not None:
            self.log("add", "SpeechQueue却下: \'{}\'".format(str_or_func))
            return
        self.log("add", "SpeechQueue += \'{}\'".format(str_or_func))
        self._queue.append(str_or_func)

    # キューから文字列・関数を取得する
    def get(self):
        return self._queue.popleft()

    def clear(self):
        self._queue.clear()

    def __len__(self):
        return len(self._queue)


# ==================================
#      外部参照用のインスタンス
# ==================================
global_speech_queue = SpeechQueue()

# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test():
    # 現状何もしない
    pass


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()
