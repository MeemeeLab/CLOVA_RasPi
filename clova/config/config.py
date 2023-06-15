import os
import json
import dotenv

from typing import Tuple, Optional, Dict, TypedDict

from clova.general.logger import BaseLogger

dotenv.load_dotenv()


class ConfigTTSParams(TypedDict):
    language: str
    name: str
    gender: str
    rate: str
    pitch: str
    speed: str
    emotion: str


class ConfigTTS(TypedDict):
    system: str
    params: ConfigTTSParams


class ConfigPersona(TypedDict):
    name: str
    myself: str
    gender: str
    type: str
    talk_style: str
    detail: str


class ConfigCharacter(TypedDict):
    tts: ConfigTTS
    persona: ConfigPersona


class SystemConfig(TypedDict):
    characters: Dict[str, ConfigCharacter]


class ConfigRequirement(TypedDict):
    requires: Tuple[Tuple[str]]


class RequirementsConfig(TypedDict):
    stt: Dict[str, ConfigRequirement]
    tts: Dict[str, ConfigRequirement]
    conversation: Dict[str, ConfigRequirement]


class ConfigAPI(TypedDict):
    system: Optional[str]
    params: Optional[Dict[str, str]]


class ConfigLineUser(TypedDict):
    name: str
    call_name: str
    id: str


class ConfigLine(TypedDict):
    user_id: Tuple[ConfigLineUser]


class ConfigSNS(TypedDict):
    line: ConfigLine


class ConfigMicrophone(TypedDict):
    num_ch: int
    index: int
    silent_thresh: int
    term_duration: int


class ConfigSpeaker(TypedDict):
    num_ch: int
    index: int


class ConfigAudio(TypedDict):
    microphone: ConfigMicrophone
    speaker: ConfigSpeaker


class ConfigHardware(TypedDict):
    audio: ConfigAudio


class UserConfig(TypedDict):
    character: str
    apis: Dict[str, ConfigAPI]
    hardware: ConfigHardware
    sns: ConfigSNS


# ==================================
#       設定パラメータ管理クラス
# ==================================


class ConfigurationProvider(BaseLogger):
    _user_config: Optional[UserConfig] = None
    _requirements_config: Optional[RequirementsConfig] = None
    USER_CONFIG_FILENAME = "./CLOVA_RasPi.json"
    REQUIREMENTS_CONFIG_FILENAME = "./assets/CLOVA_requirements.json"

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self.log("CTOR", "GENERAL_CONFIG_FILENAME={}".format(self.USER_CONFIG_FILENAME))
        self.log("CTOR", "REQUIREMENTS_CONFIG_FILENAME={}".format(self.REQUIREMENTS_CONFIG_FILENAME))

        self.load_config_file()
        self.assert_current_config_requirements()

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def get_user_config(self) -> UserConfig:
        assert self._user_config
        return self._user_config

    def get_requirements_config(self) -> RequirementsConfig:
        assert self._requirements_config
        return self._requirements_config

    # 全設定パラメータを読み取る
    def load_config_file(self) -> None:
        with open(self.USER_CONFIG_FILENAME, "r", encoding="utf-8") as cfg_file:
            file_text = cfg_file.read()
        self._user_config = json.loads(file_text)
        with open(self.REQUIREMENTS_CONFIG_FILENAME, "r", encoding="utf-8") as cfg_file:
            file_text = cfg_file.read()
        self._requirements_config = json.loads(file_text)

    # 全設定パラメータを書き込む
    def commit_user_config(self, conf: UserConfig) -> None:
        with open(self.USER_CONFIG_FILENAME, "w", encoding="utf-8") as cfg_file:
            json.dump(conf, cfg_file, indent='\t', ensure_ascii=False)
            cfg_file.write("\n")

    def assert_current_config_requirements(self) -> None:
        assert self._requirements_config and self._user_config

        if self._user_config["apis"]["tts"]["system"] is not None:
            assert self.meets_requirements(self._requirements_config["tts"][self._user_config["apis"]["tts"]["system"]]["requires"]), "TTS API Key requirements are not satisfied."
        if self._user_config["apis"]["stt"]["system"] is not None:
            assert self.meets_requirements(self._requirements_config["stt"][self._user_config["apis"]["stt"]["system"]]["requires"]), "STT API Key requirements are not satisfied."
        if self._user_config["apis"]["conversation"]["system"] is not None:
            assert self.meets_requirements(self._requirements_config["conversation"][self._user_config["apis"]["conversation"]["system"]]["requires"]), "Conversation API Key requirements are not satisfied."

    def meets_requirements(self, req: Tuple[Tuple[str]]) -> bool:
        for requirement_group in req:
            # グループ内の要件のいずれかがos.environに存在するかをチェックします
            if any(requirement in os.environ and os.environ[requirement] != "" for requirement in requirement_group):
                continue  # 少なくとも1つの要件が満たされている場合は、次のグループに進みます
            else:
                return False  # グループ内の要件がいずれも満たされていない場合はFalseを返します
        return True

    def verbose(self) -> bool:
        return "CLOVA_DEBUG" in os.environ and os.environ["CLOVA_DEBUG"] == "1"

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
