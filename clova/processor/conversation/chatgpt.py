import os
import openai

from typing import Union

from clova.general.globals import global_config_prov

from clova.processor.conversation.base_conversation import BaseConversationProvider

from clova.general.logger import BaseLogger

# ==================================
#         OpenAI APIクラス
# ==================================


class OpenAIChatGPTConversationProvider(BaseConversationProvider, BaseLogger):
    OPENAI_CHARACTER_CONFIG = "あなたはサービス終了で使えなくなったクローバの後を次ぎました。"

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self.OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
        self.set_persona("")

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def set_persona(self, prompt: str, **kwargs: str) -> None:
        self._char_setting_str = self.OPENAI_CHARACTER_CONFIG + prompt

    def supports_prompt_skill(self) -> bool:
        return True

    def get_answer(self, prompt: str, **kwargs: str) -> Union[None, str]:
        openai.api_key = self.OPENAI_API_KEY

        self.log("get_answer", "OpenAI 応答作成中")

        try:
            ai_response = openai.ChatCompletion.create(
                model=kwargs["model"],
                messages=[
                    {"role": "system", "content": self._char_setting_str},
                    {"role": "user", "content": prompt},
                ]
            )  # type: ignore[no-untyped-call]
            if global_config_prov.verbose():
                self.log("get_answer", ai_response["choices"][0]["message"]["content"])  # 返信のみを出力

            self.log("get_answer", ai_response)

            if global_config_prov.verbose():
                self.log("get_answer", len(ai_response))

            if (len(ai_response) != 0):
                return ai_response["choices"][0]["message"]["content"]  # type: ignore[no-any-return]

            self.log("get_answer", "AIからの応答が空でした。")
            return None

        except openai.error.RateLimitError:
            return "OpenAIエラー：APIクオータ制限に達しました。しばらく待ってから再度お試しください。改善しない場合は、月間使用リミットに到達したか無料枠期限切れの可能性もあります。"
        except openai.error.AuthenticationError:
            return "OpenAIエラー：Open AI APIキーが不正です。"
        except openai.error.APIConnectionError:
            return "OpenAIエラー：Open AI APIに接続できませんでした。"
        except openai.error.ServiceUnavailableError:
            return "OpenAIエラー：Open AI サービス無効エラーです。"
        except openai.error.OpenAIError as e:
            return "OpenAIエラー：Open AI APIエラーが発生しました：{}".format(e)
        except Exception as e:
            return "不明なエラーが発生しました：{}".format(e)

        return None

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
