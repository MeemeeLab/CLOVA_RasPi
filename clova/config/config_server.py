import json
import http.server

from urllib.parse import parse_qs

from clova.general.globals import global_config_prov

# TODO: add support for changing apis
# TODO: add support for checking requirements met before changing

# ==================================
#    Setting HTTPハンドラクラス
# ==================================


class HttpReqSettingHandler(http.server.BaseHTTPRequestHandler):

    # GETリクエストを受け取った場合の処理
    def do_GET(self):
        # キャラクタの選択肢を作成する。
        with open("./assets/CLOVA_systems.json", "r", encoding="utf-8") as char_file:
            file_text = char_file.read()
        char_cfg_json = json.loads(file_text)

        char_selection = ""
        for index, char_data in char_cfg_json["characters"].items():
            line_data = "            <option value=\"{}\">{} (CV: {})</option>\n".format(index, char_data["persona"]["name"], index)
            char_selection += line_data
        if global_config_prov.verbose():
            self.log("do_GET", char_selection)

        # HTMLファイルを読み込む
        with open("./assets/index.html", "r", encoding="utf-8") as html_file:
            html = html_file.read()

        html = html.replace("{characterSelList}", char_selection)

        sys_config = global_config_prov.get_general_config()

        # 変数の値をHTMLに埋め込む
        html = html.replace("{DefaultCharSel}", str(sys_config["character"]))
        html = html.replace("{MicChannels}", str(sys_config["hardware"]["audio"]["microphone"]["num_ch"]))
        html = html.replace("{MicIndex}", str(sys_config["hardware"]["audio"]["microphone"]["index"]))
        html = html.replace("{SilentThreshold}", str(sys_config["hardware"]["audio"]["microphone"]["silent_thresh"]))
        html = html.replace("{TerminateSilentDuration}", str(sys_config["hardware"]["audio"]["microphone"]["term_duration"]))
        html = html.replace("{SpeakerChannels}", str(sys_config["hardware"]["audio"]["speaker"]["num_ch"]))
        html = html.replace("{SpeakerIndex}", str(sys_config["hardware"]["audio"]["speaker"]["index"]))
        if global_config_prov.verbose():
            self.log("do_GET", html)  # for debug

        # HTTPレスポンスを返す
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    # POSTリクエストを受け取った場合の処理
    def do_POST(self):
        sys_config = global_config_prov.get_general_config()

        # POSTデータを取得する
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        post_data = post_data.decode("utf-8")

        data = parse_qs(post_data)

        self.log("do_POST", data)  # for debug

        # 変数を更新する
        sys_config["character"] = data["default_char_sel"][0]
        sys_config["hardware"]["audio"]["microphone"]["num_ch"] = int(data["mic_channels"][0])
        sys_config["hardware"]["audio"]["microphone"]["index"] = int(data["mic_index"][0])
        sys_config["hardware"]["audio"]["microphone"]["silent_thresh"] = int(data["silent_thresh"][0])
        sys_config["hardware"]["audio"]["microphone"]["term_duration"] = int(data["term_duration"][0])
        sys_config["hardware"]["audio"]["speaker"]["num_ch"] = int(data["speaker_channels"][0])
        sys_config["hardware"]["audio"]["speaker"]["index"] = int(data["speaker_index"][0])

        self.log("do_POST", "default_char_sel={}".format(sys_config["character"]))
        self.log("do_POST", "mic num_ch={}".format(sys_config["hardware"]["audio"]["microphone"]["num_ch"]))
        self.log("do_POST", "mic index={}".format(sys_config["hardware"]["audio"]["microphone"]["index"]))
        self.log("do_POST", "mic silent_thresh={}".format(sys_config["hardware"]["audio"]["microphone"]["silent_thresh"]))
        self.log("do_POST", "mic term_duration={}".format(sys_config["hardware"]["audio"]["microphone"]["term_duration"]))
        self.log("do_POST", "spk num_ch={}".format(sys_config["hardware"]["audio"]["speaker"]["num_ch"]))
        self.log("do_POST", "spk index={}".format(sys_config["hardware"]["audio"]["speaker"]["index"]))

        global_config_prov.save_general_config_file(sys_config)

        # HTTPレスポンスを返す
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()
