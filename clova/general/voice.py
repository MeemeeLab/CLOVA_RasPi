import time
import pyaudio
import threading
import numpy as np
import audioop
import ffmpeg  # type: ignore[import]

from subprocess import Popen

from typing import Dict, Type, List, Optional, IO, Tuple

from clova.general.globals import global_led_ill, global_config_prov, global_character_prov, global_vol, global_speech_queue, global_debug_interface

from clova.processor.stt.base_stt import BaseSTTProvider
from clova.processor.stt.google_cloud_speech import GoogleCloudSpeechSTTProvider
from clova.processor.stt.speech_recognition_google import SpeechRecognitionGoogleSTTProvider

from clova.processor.tts.base_tts import BaseTTSProvider
from clova.processor.tts.google_text_to_speech import GoogleTextToSpeechTTSProvider
from clova.processor.tts.voice_text import VoiceTextTTSProvider
from clova.processor.tts.voice_vox import VoiceVoxTTSProvider
from clova.processor.tts.ai_talk import AITalkTTSProvider

from clova.general.logger import BaseLogger

# 音声ファイル設定
SPEECH_FORMAT = pyaudio.paInt16

# 再生設定
PCM_PLAY_SIZEOF_CHUNK = 512

# 録音設定
GOOGLE_SPEECH_RATE = 16000
GOOGLE_SPEECH_SIZEOF_CHUNK = int(GOOGLE_SPEECH_RATE / 10)

# ==================================
#        音声取得・再生クラス
# ==================================


class VoiceController(BaseLogger):
    STT_MODULES: Dict[str, Type[BaseSTTProvider]] = {
        "GoogleCloudSpeech": GoogleCloudSpeechSTTProvider,
        "SpeechRecognitionGoogle": SpeechRecognitionGoogleSTTProvider
    }
    TTS_MODULES: Dict[str, Type[BaseTTSProvider]] = {
        "GoogleTextToSpeech": GoogleTextToSpeechTTSProvider,
        "VoiceText": VoiceTextTTSProvider,
        "VoiceVox": VoiceVoxTTSProvider,
        "AITalk": AITalkTTSProvider
    }

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        # 設定パラメータを読み込み
        conf = global_config_prov.get_user_config()
        self.mic_num_ch = conf["hardware"]["audio"]["microphone"]["num_ch"]
        self.mic_device_index = conf["hardware"]["audio"]["microphone"]["index"]
        self.silent_threshold = conf["hardware"]["audio"]["microphone"]["silent_thresh"]
        self.terminate_silent_duration = conf["hardware"]["audio"]["microphone"]["term_duration"]
        self.speaker_num_ch = conf["hardware"]["audio"]["speaker"]["num_ch"]
        self.speaker_device_index = conf["hardware"]["audio"]["speaker"]["index"]
        self.log("CTOR", "MiC:NumCh={}, Index={}, Threshold={}, Duration={}, SPK:NumCh={}, Index={}".format(self.mic_num_ch, self.mic_device_index,
                 self.silent_threshold, self.terminate_silent_duration, self.speaker_num_ch, self.speaker_device_index))  # for debug

        global_character_prov.bind_for_update(self._update_system_conf)
        global_debug_interface.bind_message_callback(self._interface_message)

        self._update_system_conf()

        self._wav_conversion_ffmpeg_waiting: Optional[Popen[bytes]] = None
        self._interface_pending_message: List[str] = []

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def _update_system_conf(self) -> None:
        self.log("_update_system_conf", "called")
        self._tts_system = global_config_prov.get_user_config()["apis"]["tts"]["system"] or global_character_prov.get_character_settings()["tts"]["system"]
        self._stt_system = global_config_prov.get_user_config()["apis"]["stt"]["system"]

        self._tts_kwargs = global_config_prov.get_user_config()["apis"]["tts"]["params"] or global_character_prov.get_character_settings()["tts"]["params"]
        self._stt_kwargs = global_config_prov.get_user_config()["apis"]["stt"]["params"]

        assert isinstance(self._tts_system, str)
        assert isinstance(self._stt_system, str)
        assert isinstance(self._tts_kwargs, dict)
        assert isinstance(self._stt_kwargs, dict)

        self.tts = self.TTS_MODULES[self._tts_system]()
        self.stt = self.STT_MODULES[self._stt_system]()

    def _interface_message(self, message: str) -> None:
        self._interface_pending_message.append(message)

    # マイクからの録音
    def microphone_record(self) -> Optional[bytes]:
        # 底面 LED を赤に
        global_led_ill.set_all(global_led_ill.RGB_RED)

        # デバッグインタフェースにメッセージがある時は即座に返す
        if self._interface_pending_message:
            self._interface_pending_message.pop(0)
            return None

        # PyAudioのオブジェクトを作成
        pyaud = pyaudio.PyAudio()

        # 録音開始
        self.log("microphone_record", "聞き取り中：")

        # 底面 LED を暗緑に
        global_led_ill.set_all(global_led_ill.RGB_DARKGREEN)

        # 録音準備
        rec_stream = pyaud.open(format=SPEECH_FORMAT,
                                channels=self.mic_num_ch,
                                rate=GOOGLE_SPEECH_RATE,
                                input=True,
                                input_device_index=self.mic_device_index,
                                frames_per_buffer=GOOGLE_SPEECH_SIZEOF_CHUNK)

        # 無音検出用パラメータ
        silent_frames = 0  # 無音期間 フレームカウンタ
        max_silent_frames = int(self.terminate_silent_duration * GOOGLE_SPEECH_RATE / 1000 / GOOGLE_SPEECH_SIZEOF_CHUNK)  # 最大無音フレームカウンタ

        # 最大最小の初期化
        maxpp_data_max = 0
        maxpp_data_min = 32767

        # 初回のボツッ音を発話開始と認識してしまうので、ダミーで最初１フレーム分読んでおく（応急処置）
        rec_stream.read(GOOGLE_SPEECH_SIZEOF_CHUNK)

        # 録音停止から始める
        recording = False

        # バッファ初期化
        rec_frames = []

        # 録音ループ
        while True:
            # デバッグインタフェースにメッセージがある時は即座に返す
            if self._interface_pending_message:
                self._interface_pending_message.pop(0)

                # 録音停止
                rec_stream.stop_stream()
                rec_stream.close()

                # PyAudioオブジェクトを終了
                pyaud.terminate()

                return None

            # データ取得
            data = rec_stream.read(GOOGLE_SPEECH_SIZEOF_CHUNK)

            # ピーク平均の算出
            maxpp_data = audioop.maxpp(data, 2)

            # 最大値、最小値の格納
            if maxpp_data < maxpp_data_min:
                maxpp_data_min = maxpp_data
            if maxpp_data > maxpp_data_max:
                maxpp_data_max = maxpp_data

            # 無音しきい値未満
            if maxpp_data < self.silent_threshold:
                # 無音期間 フレームカウンタをインクリメント
                silent_frames += 1

                # 開始済みの場合で、フレームカウンタが最大に達したら、会話の切れ目と認識して終了する処理
                if (recording) and (silent_frames >= max_silent_frames):
                    self.log("microphone_record", "録音終了 / Rec level: {0}～{1}".format(maxpp_data_min, maxpp_data_max))
                    # 録音停止
                    break

            # 無音しきい値以上
            else:
                # 音の入力があったので、無音期間フレームカウンタをクリア
                silent_frames = 0

                # まだ開始できていなかったら、ここから録音開始
                if not recording:
                    # 底面 LED を緑に
                    global_led_ill.set_all(global_led_ill.RGB_GREEN)

                    # 録音開始
                    self.log("microphone_record", "録音開始")
                    recording = True

                # 録音中のフレームを取得
                rec_frames.append(data)

            # 割り込み音声がある時はキャンセルして抜ける
            if (len(global_speech_queue) != 0):
                self.log("microphone_record", "割り込み音声により録音キャンセル")
                # rec_frames = []
                rec_frames.append(data)
                break

        # 録音停止
        rec_stream.stop_stream()
        rec_stream.close()

        # PyAudioオブジェクトを終了
        pyaud.terminate()

        return b"".join(rec_frames)

    # 音声からテキストに変換
    def speech_to_text(self, audio: bytes) -> Optional[str]:
        # 底面 LED をオレンジに
        global_led_ill.set_all(global_led_ill.RGB_ORANGE)

        if len(audio) == 0:
            return None

        assert isinstance(self._stt_kwargs, dict)

        return self.stt.stt(audio, **self._stt_kwargs)

    # テキストから音声に変換

    def text_to_speech(self, text: str) -> Optional[bytes]:
        # 底面 LED を青に
        global_led_ill.set_all(global_led_ill.RGB_BLUE)

        assert isinstance(self._tts_kwargs, dict)

        return self.tts.tts(text, **self._tts_kwargs)

    def _get_wav_info(self, wav_bytes: bytes) -> Tuple[int, int, int]:
        # Read the required fields from the header
        channels = int.from_bytes(wav_bytes[22:24], 'little')
        sample_rate = int.from_bytes(wav_bytes[24:28], 'little')
        width = int.from_bytes(wav_bytes[34:36], 'little')

        return channels, sample_rate, width

    def _launch_ffmpeg_cache(self) -> Popen[bytes]:
        input_stream = ffmpeg.input("pipe:", format="wav")
        output_stream = ffmpeg.output(
            input_stream.audio,
            "pipe:",
            format="s16le",
            ar=44100,
            ac=1,
            # loglevel='error'
        )

        self._wav_conversion_ffmpeg_waiting = output_stream.run_async(pipe_stdin=True, pipe_stdout=True)
        return self._wav_conversion_ffmpeg_waiting  # type: ignore[return-value]

    def _handle_ffmpeg_output(self, pyaud: pyaudio.PyAudio, channels: int, stdout: IO[bytes]) -> None:
        # 再生開始
        play_stream = None

        # 再生処理
        while True:
            data = stdout.read(PCM_PLAY_SIZEOF_CHUNK)
            if not data:
                break

            if play_stream is None:  # openしたときからwriteするまで結構大きめのノイズがするためデータが取得できてからopenする
                play_stream = pyaud.open(format=SPEECH_FORMAT, channels=channels, rate=44100, output=True, output_device_index=self.speaker_device_index)
                play_stream.start_stream()

            nd = (np.frombuffer(data, dtype=np.int16) * global_vol.vol_value).astype(np.int16)  # ボリューム倍率を更新
            play_stream.write(nd.tobytes())

        # 再生終了処理
        if play_stream is not None:
            play_stream.stop_stream()
            while play_stream.is_active():
                time.sleep(0.1)
            play_stream.close()
        self.log("_handle_ffmpeg_output", "Play done!")

    # 音声ファイルの再生
    def play_audio(self, audio: bytes) -> None:
        # 底面 LED を水に
        global_led_ill.set_all(global_led_ill.RGB_CYAN)

        # with open("./test.wav", "wb") as f:
        #     f.write(audio)

        channels, _, _ = self._get_wav_info(audio)

        self.log("play_audio", "オーディオ再生 ({}チャンネル)".format(channels))

        if channels != 1:
            # 変換
            input_stream = ffmpeg.input("pipe:", format="wav")
            output_stream = ffmpeg.output(
                input_stream.audio,
                "pipe:",
                format="s16le",
                ar=44100,
                ac=channels,
                # loglevel='error'
            )

            ffmpeg_proc = output_stream.run_async(pipe_stdin=True, pipe_stdout=True)
        else:
            ffmpeg_proc = self._wav_conversion_ffmpeg_waiting or self._launch_ffmpeg_cache()
            self._wav_conversion_ffmpeg_waiting = None

        # PyAudioのオブジェクトを作成
        pyaud = pyaudio.PyAudio()

        ffmpeg_handler = threading.Thread(target=self._handle_ffmpeg_output, args=[pyaud, channels, ffmpeg_proc.stdout])
        ffmpeg_handler.start()

        ffmpeg_proc.stdin.write(audio)
        ffmpeg_proc.stdin.close()

        ffmpeg_handler.join()
        pyaud.terminate()

        threading.Thread(target=self._launch_ffmpeg_cache).start()  # 次回から待機状態のffmpegを使用する

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
    module_test()
