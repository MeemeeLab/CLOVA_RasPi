from abc import ABC, abstractmethod
from typing import Union


class BaseTTSProvider(ABC):
    @abstractmethod
    def tts(self, text: str, **kwargs: str) -> Union[bytes, None]:
        pass
