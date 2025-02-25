from clova.general.conversation import ConversationController
from clova.general.voice import VoiceController

from clova.general.globals import global_led_ill, global_vol, global_character_prov, global_speech_queue, global_debug_interface

from clova.processor.skill.line import LineSkillProvider, HttpReqLineHandler
from clova.processor.skill.timer import TimerSkillProvider

from clova.io.network.http_server import HttpServer
from clova.config.config_server import HttpReqSettingHandler
from clova.io.local.switch import SwitchInput

from clova.general.logger import Logger

import platform
import time


def main() -> None:
    logger = Logger("LAUNCHER")

    # 会話モジュールのインスタンス作成
    conv = ConversationController()

    # HTTPサーバー系のインスタンス作成
    line_svr = HttpServer(8080, HttpReqLineHandler)
    config_svr = HttpServer(8000, HttpReqSettingHandler)

    # LINE送信モジュールのインスタンス
    line_sender = LineSkillProvider()

    # 底面 LED を黄色に
    global_led_ill.set_all(global_led_ill.RGB_YELLOW)

    # LEDを使うモジュールにインスタンスをコピー
    voice = VoiceController()

    # キー準備
    char_switch = SwitchInput.init(SwitchInput.PIN_BACK_SW_BT, lambda _: global_character_prov.select_next_character())
    plus_switch = SwitchInput.init(SwitchInput.PIN_BACK_SW_PLUS, lambda _: global_vol.vol_up_cb())
    minus_switch = SwitchInput.init(SwitchInput.PIN_BACK_SW_MINUS, lambda _: global_vol.vol_down_cb())

    # タイマ準備
    tmr = TimerSkillProvider()

    debug_interface_messages = []
    global_debug_interface.bind_message_callback(lambda message: debug_interface_messages.append(message))

    system = platform.system()
    is_debug_session = False
    if system == "Windows" or system == "Darwin":
        logger.log("main", "\033[93mplatform.system()がWindowsまたはDarwinを返しました。プログラムはデバッグセッションであることを想定し、メインループで実際にマイクを起動しません。\033[0m")
        is_debug_session = True

    # メインループ
    while True:
        str_or_func = conv.check_for_interrupted_voice()

        # 割り込み音声ありの時
        if str_or_func is not None:
            if callable(str_or_func):
                str_or_func()
                continue

            global_debug_interface.send_all(str_or_func)

            audio = voice.text_to_speech(str_or_func)
            if (audio is not None):
                voice.play_audio(audio)
            else:
                logger.log("main", "音声ファイルを取得できませんでした。")

        # 割り込み音声無の時
        else:
            answer_result = None

            # 録音
            if not is_debug_session:
                record_data = voice.microphone_record()
            else:
                time.sleep(10)
                record_data = b""

            stt_result = None

            if len(debug_interface_messages):
                # デバッグインタフェースからのメッセージ
                stt_result = debug_interface_messages.pop(0)
            elif record_data is None:
                continue
            else:
                # テキストに返還
                stt_result = voice.speech_to_text(record_data)

                if stt_result is None:
                    logger.log("main", "発話なし")
                    continue

            logger.log("main", "発話メッセージ:{}".format(stt_result))

            # 終了ワードチェック
            if (stt_result == "終了") or (stt_result == "終了。"):
                answer_result = "わかりました。終了します。さようなら。"
                is_exit = True

            else:
                # 会話モジュールから、問いかけに対する応答を取得
                answer_result = conv.get_answer(stt_result)
                is_exit = False

            # 応答が空でなかったら再生する。
            if ((answer_result is not None) and (answer_result != "")):
                global_debug_interface.send_all(answer_result)
                logger.log("main", "応答メッセージ:{}".format(answer_result))

                answered_text_list = answer_result.split("\n")
                for line in answered_text_list:
                    global_speech_queue.add(line)

            # 終了ワードでループから抜ける
            if (is_exit):
                tmr.stop()
                logger.log("main", "Exit!!!")
                break

    # 底面 LED をオフに
    global_led_ill.set_all(global_led_ill.RGB_OFF)

    line_svr.__del__()
    config_svr.__del__()
    line_sender.__del__()
    char_switch.__del__()
    plus_switch.__del__()
    minus_switch.__del__()


if __name__ == "__main__":
    main()
