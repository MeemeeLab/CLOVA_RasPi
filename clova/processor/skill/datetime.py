import datetime

from typing import Union

from clova.processor.skill.base_skill import BaseSkillProvider

from clova.general.logger import BaseLogger

# ==================================
#             日時クラス
# ==================================


class DateTimeSkillProvider(BaseSkillProvider, BaseLogger):
    weekday_dict = {"Mon": "月", "Tue": "火", "Wed": "水", "Thu": "木", "Fri": "金", "Sat": "土", "Sun": "日"}

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def get_prompt_addition(self) -> str:
        return "DateTimeSkillProvider: これは今日の日付を応答するスキルです。 フォーマット: `CALL_DATETIME [date|time]`"

    # 日時 質問に答える。日時の問い合わせではなければ None を返す
    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Union[None, str]:
        if not use_stub:
            # 新スキルコードをサポートしている場合、前処理しない
            # Bardはかなり頭が悪いので新スキルコードを使えない
            return None

        self.log("try_get_answer", "stub! expect unreliable response from skill")

        if ("今" not in prompt) and ("何" not in prompt) and (("日" not in prompt) or ("時" not in prompt)):
            return None

        if ("今何時" in prompt):
            now = datetime.datetime.now()
            answer_text = "今は{0}時{1}分{2}秒です".format(now.hour, now.minute, now.second)
            self.log("try_get_answer", now)
            return answer_text

        elif ("何日" in prompt):
            now = datetime.datetime.now()
            answer_text = "今日は{0}年{1}月{2}日{3}曜日です".format(now.year, now.month, now.day, self.weekday_dict[now.strftime("%a")])
            self.log("try_get_answer", now)
            return answer_text

        # 該当がない場合は空で返信
        return None

    def try_get_answer_post_process(self, response: str) -> Union[None, str]:
        if not response.startswith("CALL_DATETIME"):
            return None

        args = response.split("\n")[0].split(" ")
        if args[1] == "date":
            now = datetime.datetime.now()
            answer_text = "今は{0}時{1}分{2}秒です".format(now.hour, now.minute, now.second)
            self.log("try_get_answer_post_process", now)
            return answer_text
        if args[1] == "time":
            now = datetime.datetime.now()
            answer_text = "今日は{0}年{1}月{2}日{3}曜日です".format(now.year, now.month, now.day, self.weekday_dict[now.strftime("%a")])
            self.log("try_get_answer_post_process", now)
            return answer_text
        return None

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
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()
