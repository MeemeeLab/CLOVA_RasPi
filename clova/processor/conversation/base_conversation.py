from abc import ABC, abstractmethod
from typing import Union


class BaseConversationProvider(ABC):
    @abstractmethod
    def set_persona(self, prompt, **kwargs) -> None:
        pass

    @abstractmethod
    def supports_prompt_skill(self) -> bool:
        pass

    @abstractmethod
    def get_answer(self, prompt, **kwargs) -> Union[str, None]:
        pass
