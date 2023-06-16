import speech_recognition  # type: ignore[import]

from typing import Optional

from clova.processor.stt.base_stt import BaseSTTProvider

from clova.general.logger import BaseLogger

GOOGLE_SPEECH_RATE = 16000


class SpeechRecognitionGoogleSTTProvider(BaseSTTProvider, BaseLogger):
    def __init__(self) -> None:
        super().__init__()

    def __del__(self) -> None:
        super().__del__()

    def stt(self, audio: bytes, **kwargs: str) -> Optional[str]:
        self.log("stt", "音声からテキストに変換中(Speech Recognition)")

        # 録音した音声データをGoogle Speech Recognitionでテキストに変換する
        recognizer = speech_recognition.Recognizer()
        audio_data = speech_recognition.AudioData(audio, sample_rate=GOOGLE_SPEECH_RATE, sample_width=2)

        try:
            result: str = recognizer.recognize_google(audio_data, language=kwargs["language"])
        except Exception:
            return None

        return result
