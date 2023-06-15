from abc import ABC, abstractmethod
from typing import Union


class BaseSkillProvider(ABC):
    @abstractmethod
    def get_prompt_addition(self) -> str:
        pass

    @abstractmethod
    def try_get_answer(self, prompt: str, use_stub: bool, **kwargs: str) -> Union[str, None]:
        pass

    @abstractmethod
    def try_get_answer_post_process(self, response: str) -> Union[str, None]:
        pass
