from abc import ABC, abstractmethod


class BaseLLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        pass
