import yt_dlp  # type: ignore[import]
import ffmpeg  # type: ignore[import]
import pyaudio
import numpy as np
import os
import threading
import time

from typing import IO, Optional

from clova.general.globals import global_vol, global_speech_queue, global_config_prov

from clova.general.voice import PCM_PLAY_SIZEOF_CHUNK, SPEECH_FORMAT

from clova.io.local.switch import SwitchInput

from clova.processor.skill.base_skill import BaseSkillProvider
from clova.general.logger import BaseLogger

# ==================================
#             音楽クラス
# ==================================


class MusicSkillProvider(BaseSkillProvider, BaseLogger):
    YT_DLP_PIPE = "/tmp/yt_dlp_out.pipe"

    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()
        self.speaker_device_index = global_config_prov.get_user_config()["hardware"]["audio"]["speaker"]["index"]
        self.stop_btn = SwitchInput.init(SwitchInput.PIN_BACK_SW_MUTE, lambda _: self._stop())
        self._stop_flg = False

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def get_prompt_addition(self) -> str:
        return "MusicSkillProvider: これは音楽を再生するスキルです。このスキルを使用すると音楽が再生できます。  フォーマット: `CALL_MUSIC [search_query_multilang]`"

    def _stop(self) -> None:
        self._stop_flg = True

    def _handle_ffmpeg_output(self, pyaud: pyaudio.PyAudio, stdout: IO[bytes]) -> None:
        play_stream = None

        # 再生処理
        while True:
            data = stdout.read(PCM_PLAY_SIZEOF_CHUNK)
            if not data:
                break

            if play_stream is None:  # openしたときからwriteするまで結構大きめのノイズがするためデータが取得できてからopenする
                play_stream = pyaud.open(format=SPEECH_FORMAT, channels=1, rate=44100, output=True, output_device_index=self.speaker_device_index)
                play_stream.start_stream()

            nd = (np.frombuffer(data, dtype=np.int16) * 0.25 * global_vol.vol_value).astype(np.int16)  # ボリューム倍率を更新; かなりうるさいため0.25 * 音量
            play_stream.write(nd.tobytes())

        # 再生終了処理
        if play_stream is not None:
            play_stream.stop_stream()
            while play_stream.is_active():
                time.sleep(0.1)
            play_stream.close()
        self.log("_handle_ffmpeg_output", "Play done!")

    def _handle_yt_dlp_output(self, pyaud: pyaudio.PyAudio) -> None:
        fd = os.open(self.YT_DLP_PIPE, os.O_RDONLY)

        # 変換
        input_stream = ffmpeg.input("pipe:", format="m4a")
        output_stream = ffmpeg.output(
            input_stream.audio,
            "pipe:",
            format="s16le",
            ar=44100,
            ac=1,
            # loglevel='error'
        )

        ffmpeg_proc = output_stream.run_async(pipe_stdin=True, pipe_stdout=True)

        ffmpeg_handler = threading.Thread(target=self._handle_ffmpeg_output, args=[pyaud, ffmpeg_proc.stdout])
        ffmpeg_handler.start()

        # パイプ
        while True:
            chunk = os.read(fd, PCM_PLAY_SIZEOF_CHUNK)

            if chunk == b"" or self._stop_flg:
                self._stop_flg = False
                break

            ffmpeg_proc.stdin.write(chunk)

        os.close(fd)
        ffmpeg_proc.stdin.close()

        ffmpeg_handler.join()

    # try_play_music()
    #   -> yt-dlp (YouTube -> m4a)
    #   -> _handle_yt_dlp_output()
    #        -> ffmpeg (m4a -> PCM S16_LE)
    #        -> _handle_ffmpeg_output()
    #             -> pyaudio (PCM S16_LE -> Speaker)
    def try_play_music(self, search_query: str) -> None:
        try:
            os.mkfifo(self.YT_DLP_PIPE)  # type: ignore[attr-defined]
        except Exception:
            pass

        pyaud = pyaudio.PyAudio()

        yt_dlp_handler = threading.Thread(target=self._handle_yt_dlp_output, args=[pyaud])
        yt_dlp_handler.start()

        with yt_dlp.YoutubeDL({
            "format": "m4a/bestaudio/best",
            "playlistend": 1,
            "extractor_args": {
                "youtube": {
                    "lang": ["ja"]
                }
            },
            "outtmpl": self.YT_DLP_PIPE
        }) as ydl:
            try:
                ydl.download("ytsearch:" + search_query.replace(" ", "+"))
            except Exception:
                pass

        yt_dlp_handler.join()

        try:
            os.remove(self.YT_DLP_PIPE)
        except Exception:
            pass

    # 日時 質問に答える。日時の問い合わせではなければ None を返す
    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Optional[str]:
        if not use_stub:
            # 新スキルコードをサポートしている場合、前処理しない
            # Bardはかなり頭が悪いので新スキルコードを使えない
            return None

        self.log("try_get_answer", "stub! expect unreliable response from skill")

        if ("音楽" in prompt) and (("かけて" in prompt) or ("再生" in prompt)):
            global_speech_queue.add("曲 {} を再生します。 ミュートボタンを押して停止します。".format(" ".join(prompt)))
            global_speech_queue.add(lambda: self.try_play_music(prompt))
            return ""  # 意図的

        # 該当がない場合は空で返信
        return None

    def try_get_answer_post_process(self, response: str) -> Optional[str]:
        if not response.startswith("CALL_MUSIC"):
            return None

        args = response.split("\n")[0].split(" ")
        global_speech_queue.add("曲 {} を再生します。 ミュートボタンを押して停止します。".format(" ".join(args[1:])))
        global_speech_queue.add(lambda: self.try_play_music(" ".join(args[1:])))
        return ""  # 意図的

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
