from abc import ABC, abstractmethod
from typing import Union


class BaseConversationProvider(ABC):
    @abstractmethod
    def set_persona(self, prompt: str, **kwargs: str) -> None:
        pass

    @abstractmethod
    def supports_prompt_skill(self) -> bool:
        pass

    @abstractmethod
    def get_answer(self, prompt: str, **kwargs: str) -> Union[str, None]:
        pass
