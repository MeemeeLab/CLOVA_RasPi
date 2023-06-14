try:
    import RPi.GPIO as GPIO
except BaseException:
    from fake_rpi.RPi import GPIO

from clova.general.logger import Logger

from clova.general.logger import BaseLogger

ALIVE_SWITCH_INPUTS = {}

# ==================================
#           キー入力クラス
# ==================================


class SwitchInput(BaseLogger):
    # PIN_FRONT_SW = 26
    # PIN_FRONT_SW = 4	# 起動に使うので、これはサポート対象外とする
    PIN_BACK_SW_MINUS = 2
    PIN_BACK_SW_PLUS = 3
    PIN_BACK_SW_BT = 5
    PIN_BACK_SW_MUTE = 7
    # PIN_POWER_SW = 22 # 電源OFFキーに使っているので、これはサポート対象外とする

    KEY_UP = False
    KEY_DOWN = True

    def __init__(self, pin, cb_func):
        super().__init__()

        assert pin is None, "SwitchInput() is now obsolete; use SwitchInput.init() for further use"
        assert cb_func is None, "SwitchInput() is now obsolete; use SwitchInput.init() for further use"

        self._cb_list = []
        self._pin = None

    # コンストラクタ
    def init(pin, cb_func):
        logger = Logger("SwitchInput")

        if pin in ALIVE_SWITCH_INPUTS:
            logger.log("init", "Returning already existing SwitchInput; pin={}".format(pin))
            ALIVE_SWITCH_INPUTS[pin]._cb_list.append(cb_func)
            return ALIVE_SWITCH_INPUTS[pin]

        cls = SwitchInput(None, None)
        cls._pin = pin

        cls._cb_list.append(cb_func)

        cls.log("init", "GPIO.setup({}, {}, {})".format(cls._pin, GPIO.IN, GPIO.PUD_UP))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(cls._pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(cls._pin, GPIO.FALLING, callback=cls._internal_cb, bouncetime=200)

        ALIVE_SWITCH_INPUTS[cls._pin] = cls

        return cls

    # デストラクタ
    def __del__(self):
        super().__del__()

        self.log("DTOR", "Pin={}".format(self._pin))
        self.release()

    def _internal_cb(self, pin):
        for cb in self._cb_list:
            cb(pin)

    # 解放処理
    def release(self):
        self.log("release", "Relase key({})".format(self._pin))
        GPIO.remove_event_detect(self._pin)
        GPIO.cleanup(self._pin)
        del ALIVE_SWITCH_INPUTS[self._pin]

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
