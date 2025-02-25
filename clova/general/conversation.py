import datetime
from typing import Dict, Union, Type, List, Callable, Optional

from clova.processor.conversation.base_conversation import BaseConversationProvider
from clova.processor.conversation.chatgpt import OpenAIChatGPTConversationProvider
from clova.processor.conversation.bard import BardConversationProvider

from clova.processor.skill.base_skill import BaseSkillProvider
from clova.processor.skill.timer import TimerSkillProvider
from clova.processor.skill.news import NewsSkillProvider
from clova.processor.skill.weather import WeatherSkillProvider
from clova.processor.skill.line import LineSkillProvider
from clova.processor.skill.datetime import DateTimeSkillProvider
from clova.processor.skill.music import MusicSkillProvider
from clova.processor.skill.alarm import AlarmSkillProvider

from clova.general.globals import global_speech_queue, global_config_prov, global_character_prov, global_led_ill, GLOBAL_CHARACTER_CONFIG_PROMPT

from clova.general.logger import BaseLogger

# ==================================
#          会話制御クラス
# ==================================


class ConversationController(BaseLogger):
    CONVERSATION_MODULES: Dict[str, Type[BaseConversationProvider]] = {
        "OpenAI-ChatGPT": OpenAIChatGPTConversationProvider,
        "Bard": BardConversationProvider
    }
    SKILL_MODULES: List[BaseSkillProvider] = [
        TimerSkillProvider(), NewsSkillProvider(), WeatherSkillProvider(), LineSkillProvider(),
        DateTimeSkillProvider(), MusicSkillProvider(), AlarmSkillProvider()
    ]

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self.system = global_config_prov.get_user_config()["apis"]["conversation"]["system"]
        assert self.system, "Conversation system must be specified"
        self.provider = self.CONVERSATION_MODULES[self.system]()

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    # 音声以外での待ち処理
    def check_for_interrupted_voice(self) -> Optional[Union[str, Callable[[], None]]]:
        if (len(global_speech_queue) != 0):
            return global_speech_queue.get()

        return None

    # 問いかけに答える
    def get_answer(self, prompt: str) -> str:
        # 無言なら無応答
        if (prompt == ""):
            return ""

        # 名前に応答
        if ((prompt == "ねえクローバー") or (prompt == "ねえクローバ")):
            return "はい。何でしょう。"

        # スキル
        for skill in self.SKILL_MODULES:
            result = skill.try_get_answer(prompt, not self.provider.supports_prompt_skill())
            if result is not None:
                return result

        # どれにも該当しないときには AI に任せる。
        kwargs = global_config_prov.get_user_config()["apis"]["conversation"]["params"] or {}

        if self.provider.supports_prompt_skill():
            actual_prompt = global_character_prov.get_character_prompt() + "\n" + GLOBAL_CHARACTER_CONFIG_PROMPT + "\n"
            actual_prompt = actual_prompt.replace("{CURRENT_DATETIME}", datetime.datetime.now().strftime('%Y年%m月%d日 %H時%M分'))
            actual_prompt = actual_prompt.replace("{SKILL_LIST}", "\n".join(list(map(lambda skill: skill.get_prompt_addition(), self.SKILL_MODULES))))
            actual_prompt = actual_prompt.replace("{STT_RESULT}", prompt) + "\n"
        else:
            actual_prompt = global_character_prov.get_character_prompt() + "\n" + prompt + "\n"

        self.log("get_answer", "actual_prompt: {}".format(actual_prompt))

        # 底面 LED をピンクに
        global_led_ill.set_all(global_led_ill.RGB_PINK)

        result = self.provider.get_answer(actual_prompt, **kwargs)

        if not result:
            # AI が利用不可の場合は謝るしかない…
            return "すみません。質問が理解できませんでした。"

        # スキル (post process)
        for skill in self.SKILL_MODULES:
            response = skill.try_get_answer_post_process(result)
            if response is not None:
                return response

        return result

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
