import threading as th
import datetime

from typing import Optional

from clova.general.globals import global_speech_queue, global_db

from clova.processor.skill.base_skill import BaseSkillProvider

from clova.general.logger import BaseLogger

from clova.io.local.switch import SwitchInput

DATABASE_INIT = """
CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    alarm_ts TIMESTAMP NOT NULL
)
"""


class AlarmSkillProvider(BaseSkillProvider, BaseLogger):
    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self._watchdog_stop = th.Event()
        self._alarm_stop = th.Event()
        self._watchdog_thread = th.Thread(target=self._thread_watchdog, args=(), name="AlarmWatchdog", daemon=True)
        self._watchdog_thread.start()

        self.stop_btn = SwitchInput.init(SwitchInput.PIN_BACK_SW_MUTE, lambda _: self._alarm_stop.set())

        self.init_db()

    def init_db(self) -> None:
        global_db.execute(DATABASE_INIT, True)

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

        self._watchdog_stop.set()
        self._alarm_stop.set()
        self._watchdog_thread.join()
        self.log("DTOR", "_watchdog_thread join")

    def get_prompt_addition(self) -> str:
        return "AlarmSkillProvider: これは指定時間に自動鳴動するスキルです。 時刻はISO 8601フォーマットです。 例：`2023-06-02T19:57:10+09:00` フォーマット: `CALL_ALARM <(iso8601)|delete_all>`"

    # タイマのスレッド関数
    def _thread_watchdog(self) -> None:
        while not self._watchdog_stop.wait(1):
            self._watchdog_update()

    # タイマの監視処理

    def _watchdog_update(self) -> None:
        result = global_db.execute("SELECT id FROM alarms WHERE alarm_ts < strftime('%s', 'now') LIMIT 1", False)
        if len(result) and len(result[0]):
            id = result[0][0]
            self.log("_watchdog_update", "SELECT found alarm with id '{}'".format(id))
            global_db.execute("DELETE FROM alarms WHERE id = '{}'".format(id), True)
            self.alarm()

    def alarm(self) -> None:
        dt = datetime.datetime.now()
        global_speech_queue.add("現在時刻は{}、です。ミュートボタンを押してアラームを停止します。".format(dt.strftime("%H時%M分")))

        if self._alarm_stop.is_set():
            self._alarm_stop.clear()
            return

        global_speech_queue.add(self.alarm)

    # タイマーの 要求に答える。タイマーの要求ではなければ None を返す
    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Optional[str]:
        if not use_stub:
            # 新スキルコードをサポートしている場合、前処理しない
            # Bardはかなり頭が悪いので新スキルコードを使えない
            return None

        if "アラーム" in prompt:
            self.log("try_get_answer", "\x1b[33m現在の言語モデルはアラーム機能をサポートしません。\x1b[0m")
            return "現在の言語モデルはアラーム機能をサポートしません。"

        return None

    def delete_all(self) -> None:
        global_db.execute("DELETE FROM alarms", True)

    def push_ts(self, ts: int) -> None:
        assert isinstance(ts, int)
        global_db.execute("INSERT INTO alarms (alarm_ts) VALUES ('{}')".format(str(ts)), True)

    def try_get_answer_post_process(self, response: str) -> Optional[str]:
        if not response.startswith("CALL_ALARM"):
            return None

        args = response.split("\n")[0].split(" ")

        if args[1] == "delete_all":
            self.delete_all()
            return "設定されたアラームをすべて削除しました。"

        self.log("try_get_answer_post_process", args[1])

        try:
            dt = datetime.datetime.fromisoformat(args[1])
        except Exception:
            return "すみません。もう一度お願いします。"

        self.push_ts(int(dt.timestamp()))

        return "{} にアラームを設定しました。".format(dt.strftime('%Y年%m月%d日 %H時%M分'))

# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test() -> None:
    pass


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================


if __name__ == "__main__":
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()
