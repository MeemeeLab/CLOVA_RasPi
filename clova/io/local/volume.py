from clova.general.logger import BaseLogger
from clova.general.queue import SpeechQueue

# ==================================
#       ボリューム制御クラス
# ==================================


class VolumeController(BaseLogger):
    vol_value = 1.0
    _vol_step = 7
    VOL_MIN_STEP = 0
    VOL_MAX_STEP = 12

    # ボリュームテーブル（後でちゃんと計算しないとバランス悪い）
    VOL_TABLE = [0.001, 0.01, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0]

    # コンストラクタ
    def __init__(self, global_speech_queue: SpeechQueue) -> None:
        super().__init__()

        self._vol_step = 7
        self._cb_waiting = False
        self._global_speech_queue = global_speech_queue

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def _speech_queue_cb(self) -> None:
        self._cb_waiting = False
        self._global_speech_queue.add("ボリュームを {} に設定しました。".format(str(self._vol_step)))

    # ボリューム [+] 押下時処理
    def vol_up_cb(self) -> None:
        if (self._vol_step < self.VOL_MAX_STEP):
            self._vol_step += 1
            self.vol_value = self.VOL_TABLE[self._vol_step]
            self.log("vol_up_cb", "Vol + [={}({})]".format(self._vol_step, self.vol_value))

            if not self._cb_waiting:
                self._cb_waiting = True
                self._global_speech_queue.add(self._speech_queue_cb)

    # ボリューム [-] 押下時処理
    def vol_down_cb(self) -> None:
        if (self._vol_step > self.VOL_MIN_STEP):
            self._vol_step -= 1
            self.vol_value = self.VOL_TABLE[self._vol_step]
            self.log("vol_down_cb", "Vol - [={}({})]".format(self._vol_step, self.vol_value))
            if not self._cb_waiting:
                self._cb_waiting = True
                self._global_speech_queue.add(self._speech_queue_cb)


# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test() -> None:
    # 現状何もしない
    pass


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    module_test()
