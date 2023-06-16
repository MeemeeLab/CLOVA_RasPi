import os
import os.path
import re
import http.server
import json
import requests
import urllib.parse
import urllib.request

from typing import Any, Optional, Dict, List

from clova.general.globals import global_speech_queue, global_config_prov

from clova.processor.skill.base_skill import BaseSkillProvider
from clova.general.logger import BaseLogger

# ==================================
#           LINE受信クラス
# ==================================


class LineReceiver(BaseLogger):
    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def conv_id_to_call_name(self, id: str) -> str:
        # 未サポート（やり方調査中）
        self.log("conv_id_to_call_name", "ID:{} の名前を取得できませんでした。".format(self.json_data["events"][0]["message"]["id"]))
        return "誰か"

    # 受信時処理
    def on_message_recv(self, body: bytes, query_data: Dict[str, List[str]]) -> None:
        # 取得データを展開
        self.log("on_message_recv", "POST body=")
        self.log("on_message_recv", body)
        self.log("on_message_recv", "POST query_data=")
        self.log("on_message_recv", query_data)

        # ボディー部分の JSonを取り出す
        self.json_data = json.loads(body)
        self.log("on_message_recv", "Json=")
        self.log("on_message_recv", self.json_data)

        # IDをハンドル名に変換
        sender = self.conv_id_to_call_name(self.json_data["events"][0]["message"]["id"])

        # ライン受信をまず通知
        sender_read = "{} さんから次のラインメッセージが届きました。".format(sender)
        global_speech_queue.add(sender_read)
        self.log("on_message_recv", "From>'{}'".format(sender_read))

        # メッセージを取得
        line_str = self.json_data["events"][0]["message"]["text"]
        self.log("on_message_recv", "LINE Message=")
        self.log("on_message_recv", line_str)

        # メッセージ読み上げ
        message_list = line_str.splitlines()

        if global_config_prov.verbose():
            self.log("on_message_recv", "LINE message=")

        for message in message_list:
            global_speech_queue.add(message)
            self.log("on_message_recv", "Send>'{}'".format(message))

# ==================================
#           LINE送信クラス
# ==================================


class LineSkillProvider(BaseSkillProvider, BaseLogger):
    POST_URL = "https://api.line.me/v2/bot/message/push"
    request_header = {"Content-Type": "application/json", "Authorization": "Bearer channel_access_token"}
    # TODO: Make TypedDict for request_body; idk bout line
    request_body: Any = {"to": "user ID", "messages": [{"type": "text", "text": "Message to send"}]}

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self.ACCESS_TOKEN = os.environ["LINE_CH_ACC_TOKEN"]

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    # メッセージ送信
    def send_message(self, to_id: str, message: str) -> None:
        # データをセット
        self.request_body["to"] = to_id
        self.request_body["messages"][0]["text"] = message
        self.request_header["Authorization"] = "Bearer {}".format(self.ACCESS_TOKEN)

        if global_config_prov.verbose():
            self.log("send_message", "HEADER:")
            self.log("send_message", self.request_header)
            self.log("send_message", "BODY:")
            self.log("send_message", self.request_body)

        # メッセージの送信
        requests.post(self.POST_URL, headers=self.request_header, json=self.request_body)

    def conv_call_name_to_id(self, call_name: str) -> str:
        found_id = ""
        default_id = ""

        for id_inf in global_config_prov.get_user_config()["sns"]["line"]["user_id"]:
            if (id_inf["name"] == "default"):
                default_id = id_inf["id"]
            elif (id_inf["call_name"] == call_name):
                found_id = id_inf["id"]

        if (found_id == ""):
            self.log("conv_call_name_to_id", "呼び名:{} のIDを取得できませんでした。デフォルトのIDを使用します。")
            found_id = default_id

        return found_id

    def get_prompt_addition(self) -> str:
        return "LineSkillProvider: これはモバイルメッセンジャーアプリケーションの「LINE」を送信するスキルです。 フォーマット: `CALL_LINE [name] [message]`"

    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Optional[str]:
        if not use_stub:
            # 新スキルコードをサポートしている場合、前処理しない
            # Bardはかなり頭が悪いので新スキルコードを使えない
            return None

        self.log("try_get_answer", "stub! expect unreliable response from skill")

        if ((("LINE" in prompt) or ("ライン" in prompt)) and (("送信して" in prompt) or ("送って" in prompt) or ("して" in prompt))):
            name_str = prompt.split("に")[0]

            # 正規表現パターンを定義
            pattern = r"^(?P<name_str>.+?)[ ]*に[ ]*(?P<message>.+?)\s*([と|って]+[ ]*[ライン|LINE]+[ ]*[して|を送って|送って|送信して]+)[。]*$"

            # 正規表現によるマッチング
            match = re.match(pattern, prompt)

            if match:
                # マッチした場合、name_str と Message 変数に格納
                name_str = match.group("name_str")
                message = match.group("message")
                self.log("try_get_answer", "name_str: {}".format(name_str))
                self.log("try_get_answer", "Message: {}".format(message))

                # メッセージ送信
                id = self.conv_call_name_to_id(name_str)
                self.log("try_get_answer", "Send[LINE]>Id:{},Msg:{}".format(id, message))
                self.send_message(id, message)

                answer_text = "{} に {} とラインメッセージ送りました".format(name_str, message)
                return answer_text

            else:
                # 該当がない場合は空で返信
                answer_text = "メッセージを解釈できませんでした。"
                self.log("try_get_answer", answer_text)
                return answer_text

        else:
            # 該当がない場合は空で返信
            self.log("try_get_answer", "No keyword for skill Line")
            return None

    def try_get_answer_post_process(self, response: str) -> Optional[str]:
        if not response.startswith("CALL_LINE"):
            return None

        args = response.split("\n")[0].split(" ")

        name_str = args[1]
        message = args[2]

        id = self.conv_call_name_to_id(name_str)
        self.log("try_get_answer_post_process", "Send[LINE]>Id:{},Msg:{}".format(id, message))
        self.send_message(id, message)

        return "{} に {} とラインメッセージ送りました".format(name_str, message)

# ==================================
#      LINE HTTPハンドラクラス
# ==================================


class HttpReqLineHandler(http.server.BaseHTTPRequestHandler):
    line_recv = LineReceiver()

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length")))  # type: ignore[arg-type]
        query_data = urllib.parse.parse_qs(body.decode(encoding="utf8", errors="replace"))

        self.line_recv.on_message_recv(body, query_data)

# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test() -> None:
    # APIキー類の読み込み
    sender = LineSkillProvider()
    ret = sender.try_get_answer("クローバに おはようございます！ って LINE して。", True)
    print(ret)


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()
