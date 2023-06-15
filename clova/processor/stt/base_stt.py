from abc import ABC, abstractmethod
from typing import Union


class BaseSTTProvider(ABC):
    @abstractmethod
    # audio: S16_LE? PCM audio
    def stt(self, audio: bytes, **kwargs: str) -> Union[str, None]:
        pass
