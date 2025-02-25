import threading as th
import time
import datetime
import re

from typing import Optional

from clova.general.globals import global_speech_queue

from clova.processor.skill.base_skill import BaseSkillProvider

from clova.general.logger import BaseLogger

# ==================================
#         タイマー管理クラス
# ==================================
# タイマー管理クラス


class TimerSkillProvider(BaseSkillProvider, BaseLogger):
    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self._stop_event = th.Event()
        self._is_timer_set = False
        self._is_alarm_on = False
        self._timer_thread = th.Thread(target=self._thread_timer, args=(), name="TimerMain", daemon=True)
        self._timer_thread.start()
        self._duration = ""

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

        self.stop()
        self._stop_event.set()
        self._timer_thread.join()
        self.log("DTOR", "_timer_thread Joined!")

    def get_prompt_addition(self) -> str:
        return "TimerSkillProvider: これは指定時間後に自動返答するスキルです。 フォーマット: `CALL_TIMER [duration_in_seconds]`"

    # タイマの監視を開始
    def start(self) -> None:
        if (not self._is_timer_set):
            self.log("start", "Timer started!")
            self._is_timer_set = True

    # タイマの監視を停止

    def stop(self) -> None:
        if (self._is_timer_set):
            self.log("stop", "Timer stopped!")
            self._is_timer_set = False

    # タイマのスレッド関数
    def _thread_timer(self) -> None:
        while not self._stop_event.wait(1):
            self._timer_update()

    # タイマの監視処理

    def _timer_update(self) -> None:
        if (self._is_timer_set):
            self.log("_timer_update", "Waiting Timer!")
            if (datetime.datetime.now() >= self.target_time):
                # self._is_timer_set = False
                self._is_alarm_on = True
                self.log("_timer_update", "Time UP!!!!")
                answer_text = "{} 経ちました。".format(self._duration)
                global_speech_queue.add(answer_text)
                self.log("_timer_update", answer_text)
                self.target_time += datetime.timedelta(seconds=10)
                # self.Stop()

    # タイマーの 要求に答える。タイマーの要求ではなければ None を返す
    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Optional[str]:
        if (not self._is_alarm_on):
            if not use_stub:
                # 新スキルコードをサポートしている場合、前処理しない
                # Bardはかなり頭が悪いので新スキルコードを使えない
                return None

            self.log("try_get_answer", "stub! expect unreliable response from skill")

            if ((re.match(".*後に.*知らせて", prompt) is not None) or (re.match(".*後に.*タイマ.*セット", prompt) is not None)):
                self.log("try_get_answer", "Match1")
                pos = prompt.find("後")
                duration = prompt[:pos]
                self._duration = duration
                self.log("try_get_answer", duration)
                if (duration != ""):
                    answer_text = "{}後にタイマーをセットします。".format(duration)
                    self.set_duration(duration)
                    self.log("try_get_answer", answer_text)
                    # self._is_timer_set = True #??
                    return answer_text
                else:
                    return None
            else:
                return None
        else:
            if ("わかりました" in prompt) or ("了解" in prompt) or ("止めて" in prompt):
                answer_text = "タイマ通知を終了します。"
                self._is_alarm_on = False
                self._is_timer_set = False
                self.stop()
                self.log("try_get_answer", answer_text)
                return answer_text
            else:
                # answer_text = "{} 経ちました。".format(self._duration)
                # global_speech_queue.AddToQueue(answer_text)

                answer_text = "終了待ちです。"
                self.log("try_get_answer", answer_text)
                return answer_text

    def try_get_answer_post_process(self, response: str) -> Optional[str]:
        if not response.startswith("CALL_TIMER"):
            return None

        args = response.split("\n")[0].split(" ")
        secs = int(args[1])
        self.target_time = datetime.datetime.now() + datetime.timedelta(seconds=secs)
        self.log("set_duration", "{} = {} sec @ {}".format(args[1], secs, self.target_time))
        self._is_timer_set = True
        self.start()
        return "タイマーをセットしました"

    # 満了までの期間から、満了日時分秒を割り出す
    def set_duration(self, duration: str) -> None:
        if (("時間" in duration) or ("分" in duration) or ("秒" in duration)):
            secs = self.parse_time(duration)
            self.target_time = datetime.datetime.now() + datetime.timedelta(seconds=secs)
            self.log("set_duration", "{} = {} sec @ {}".format(duration, secs, self.target_time))
            self._is_timer_set = True
            self.start()
            # is_timer_set = True

    # 文字列の時分秒の部分を字句解析して秒に変換
    def parse_time(self, time_string: str) -> int:
        self.log("parse_time", "time_string={}".format(time_string))
        time_pattern = r"(?:(\d+)時間)?(?:(\d+)分)?(?:(\d+)秒)?"
        match = re.match(time_pattern, time_string)
        assert match
        hours, minutes, seconds = map(int, match.groups(default=0))
        self.log("parse_time", "{}時間 {}分 {}秒 = {}sec".format(hours, minutes, seconds, ((hours * 3600) + (minutes * 60) + seconds)))
        return ((hours * 3600) + (minutes * 60) + seconds)

# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test2() -> None:
    tmr = TimerSkillProvider()
    # seconds = tmr.ParseTime("3時間40分59秒後")
    seconds = tmr.parse_time("1分10秒後")
    print(seconds)


def module_test() -> None:
    tmr = TimerSkillProvider()
    tmr.try_get_answer("1分10秒後に知らせて", True)

    test_event = th.Event()
    test_thread = th.Thread(target=WaitForTestOrEnterKey, args=(test_event,))
    test_thread.start()

    while not test_event.is_set():
        # 他のスレッドが動ける処理をここに記述
        if (not tmr._is_timer_set):
            break
        time.sleep(0.5)

    print("Finished Test!")


def WaitForTestOrEnterKey(event: th.Event) -> None:
    input("Press Enter to FINISH...")
    event.set()


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()
