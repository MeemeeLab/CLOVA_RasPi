import json

from typing import Tuple, Optional, Dict, Union, List, Callable

from clova.config.config import ConfigurationProvider, ConfigCharacter, SystemConfig
from clova.general.queue import SpeechQueue

from clova.general.logger import BaseLogger

CHARACTER_CONFIG_PROMPT = """
{CURRENT_DATETIME}

使用可能なスキル：
```
{SKILL_LIST}
```
スキルを使用し、特殊な応答が可能です。
あなたがこれらの応答を使用する際、このフォーマットに従った回答をします。
説明等は含めないでください。これは機械によって読み取られます。
これらに該当すると思われない文章があった場合、そのまま日本語で応答してください。

以下がユーザーの文書です。これに応答して下さい。
```
{STT_RESULT}
```
"""

# ==================================
#       キャラクタ管理クラス
# ==================================


class CharacterProvider(BaseLogger):
    character: Optional[ConfigCharacter] = None
    systems: Optional[SystemConfig] = None
    current_character_num: int = -1
    character_index: List[str] = []
    characters_len: int = 0
    update_callbacks: List[Callable[[], None]] = []

    # コンストラクタ
    def __init__(self, global_config_prov: ConfigurationProvider, global_speech_queue: SpeechQueue) -> None:
        super().__init__()
        self._global_config_prov = global_config_prov
        self._global_speech_queue = global_speech_queue

        # キャラクタ設定ファイルの読み込み
        self.read_character_config_file()

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def bind_for_update(self, cb: Callable[[], None]) -> None:
        self.update_callbacks.append(cb)

    # キャラクタ設定
    def set_character(self, id: str) -> None:
        assert self.systems

        self.character = self.systems["characters"][id]
        self.current_character_num = self.character_index.index(id)
        for cb in self.update_callbacks:
            cb()
        select_speech = "キャラクタ {}さん CV {}が選択されました。".format(self.character["persona"]["name"], id)
        self.log("set_character", select_speech)
        self._global_speech_queue.add(select_speech)

    def get_character_settings(self) -> Dict[str, Dict[str, Union[str, Dict[str, str]]]]:
        if self.character is None:
            self.set_character(self._global_config_prov.get_user_config()["character"])

        return self.character  # type: ignore[return-value]

    # キャラクタの特徴を取得。
    def get_character_prompt(self) -> str:
        # OpenAI に指示するキャラクタの特徴をひとつの文字列化する。
        assert self.character

        description = ""
        if (self.character["persona"]["name"] != ""):
            description += "あなたの名前は {}です。\n".format(self.character["persona"]["name"])

        if (self.character["persona"]["gender"] != ""):
            description += "あなたの性別は {}です。\n".format(self.character["persona"]["gender"])

        if (self.character["persona"]["myself"] != ""):
            description += "あなたは一人称として {}を使います。\n".format(self.character["persona"]["myself"])

        if (self.character["persona"]["type"] != ""):
            description += "あなたの性格は {}\n".format(self.character["persona"]["type"])

        if (self.character["persona"]["talk_style"] != ""):
            description += "あなたの話し方は {}\n".format(self.character["persona"]["talk_style"])

        if (self.character["persona"]["detail"] != ""):
            description += "あなたは {}\n".format(self.character["persona"]["detail"])

        self.log("get_character_prompt", "character Description={}".format(description))
        return description

    # キャラクタに必要なクレデンシャル名を取得
    def get_requirements(self, id: str) -> Tuple[Tuple[str]]:
        assert self.systems
        return self._global_config_prov.get_requirements_config()["tts"][self.systems['characters'][id]["tts"]["system"]]["requires"]

    # 次のキャラクターを選択
    def select_next_character(self) -> None:
        num = self.current_character_num
        while True:
            # 次を選択
            if ((num + 1) < self.characters_len):
                num = num + 1
            else:
                num = 0

            # 選択可のキャラクタまで行くか、一周したら抜ける
            if (
                self._global_config_prov.meets_requirements(self.get_requirements(self.character_index[num])) or num == self.current_character_num
            ):
                break

        self.set_character(self.character_index[num])

    # キャラクタ設定ファイルを読み出す
    def read_character_config_file(self) -> None:
        with open("./assets/CLOVA_systems.json", "r", encoding="utf-8") as cfg_file:
            file_text = cfg_file.read()
        self.systems = json.loads(file_text)
        assert self.systems
        self.character_index = list(self.systems["characters"].keys())
        self.characters_len = len(self.character_index)


# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test() -> None:
    prov = CharacterProvider(ConfigurationProvider(), SpeechQueue())
    assert prov.systems
    print("characters.keys() = {}".format(str(prov.systems["characters"].keys())))


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    module_test()
