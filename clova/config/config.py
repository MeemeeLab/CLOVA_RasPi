import os
import json
import dotenv

from typing import Tuple

from clova.general.logger import BaseLogger

dotenv.load_dotenv()

# ==================================
#       設定パラメータ管理クラス
# ==================================


class ConfigurationProvider(BaseLogger):
    general_config = None
    GENERAL_CONFIG_FILENAME = "./CLOVA_RasPi.json"
    requirements_config = None
    REQUIREMENTS_CONFIG_FILENAME = "./assets/CLOVA_requirements.json"

    # コンストラクタ
    def __init__(self):
        super().__init__()

        self.log("CTOR", "GENERAL_CONFIG_FILENAME={}".format(self.GENERAL_CONFIG_FILENAME))
        self.log("CTOR", "REQUIREMENTS_CONFIG_FILENAME={}".format(self.REQUIREMENTS_CONFIG_FILENAME))

        self.load_config_file()
        self.assert_current_config_requirements()

    # デストラクタ
    def __del__(self):
        super().__del__()

    def get_general_config(self):
        return self.general_config

    def get_requirements_config(self):
        return self.requirements_config

    # 全設定パラメータを読み取る
    def load_config_file(self):
        with open(self.GENERAL_CONFIG_FILENAME, "r", encoding="utf-8") as cfg_file:
            file_text = cfg_file.read()
        self.general_config = json.loads(file_text)
        with open(self.REQUIREMENTS_CONFIG_FILENAME, "r", encoding="utf-8") as cfg_file:
            file_text = cfg_file.read()
        self.requirements_config = json.loads(file_text)

    # 全設定パラメータを書き込む
    def save_general_config_file(self, conf):
        with open(self.GENERAL_CONFIG_FILENAME, "w", encoding="utf-8") as cfg_file:
            json.dump(conf, cfg_file, indent='\t', ensure_ascii=False)
            cfg_file.write("\n")

    def assert_current_config_requirements(self):
        if self.general_config["apis"]["tts"]["system"] is not None:
            assert self.is_requirements_met(self.requirements_config["tts"][self.general_config["apis"]["tts"]["system"]]["requires"]), "TTS API Key requirements are not satisfied."
        if self.general_config["apis"]["stt"]["system"] is not None:
            assert self.is_requirements_met(self.requirements_config["stt"][self.general_config["apis"]["stt"]["system"]]["requires"]), "STT API Key requirements are not satisfied."
        if self.general_config["apis"]["conversation"]["system"] is not None:
            assert self.is_requirements_met(self.requirements_config["conversation"][self.general_config["apis"]["conversation"]
                                            ["system"]]["requires"]), "Conversation API Key requirements are not satisfied."

    def is_requirements_met(self, req: Tuple[Tuple[str]]) -> bool:
        for requirement_group in req:
            # グループ内の要件のいずれかがos.environに存在するかをチェックします
            if any(requirement in os.environ and os.environ[requirement] != "" for requirement in requirement_group):
                continue  # 少なくとも1つの要件が満たされている場合は、次のグループに進みます
            else:
                return False  # グループ内の要件がいずれも満たされていない場合はFalseを返します
        return True

    def verbose(self):
        return "CLOVA_DEBUG" in os.environ and os.environ["CLOVA_DEBUG"] == "1"

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
