import os
from http.cookies import SimpleCookie
from bardapi import Bard, BardCookies  # type: ignore[import]
from typing import Union

from clova.processor.conversation.base_conversation import BaseConversationProvider

from clova.general.logger import BaseLogger

# Bard にはタイマー&音楽スキル以外いらないかも


class BardConversationProvider(BaseConversationProvider, BaseLogger):
    CHARACTER_CONFIG = "あなたはサービス終了で使えなくなったクローバの後を次ぎました。"

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self.BARD_PSID = os.environ["BARD_PSID"]
        self.cookies: SimpleCookie[str] = SimpleCookie()
        self.cookies.load(self.BARD_PSID)

        self.bard = Bard(token=self.BARD_PSID) if "__Secure-1PSID" not in self.cookies else BardCookies(cookie_dict=self.cookies)
        self.set_persona("")

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def supports_prompt_skill(self) -> bool:
        return False

    def set_persona(self, prompt: str, **kwargs: str) -> None:
        self._char_setting_str = self.CHARACTER_CONFIG + prompt

    def get_answer(self, prompt: str, **kwargs: str) -> Union[str, None]:
        self.log("get_answer", "Bard 応答作成中")
        actual_prompt = self._char_setting_str + "\n" + prompt

        result = self.bard.get_answer(actual_prompt)

        self.log("get_answer", result)

        self.bard.conversation_id, self.bard.response_id, self.bard.choice_id = ("", "", "")
        self.bard._reqid = 0

        return result["content"]  # type: ignore[no-any-return]
