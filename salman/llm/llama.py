from llama_cpp import Llama

from salman.config import Config
from salman.logging import salman as logger


class LlamaLLM:
    human_prompt = "USER:"
    ai_prompt = "ASSISTANT:"
    _client = None

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super(LlamaLLM, cls).__new__(cls)
            cls._client = Llama(Config.LLAMA_MODEL)
        return cls._instance

    def completion(
        self,
        prompt: str,
        max_tokens_to_sample=256,
        temperature=0.0,
    ) -> str:
        kwargs = dict(
            stop=[LlamaLLM.human_prompt],
            max_tokens=max_tokens_to_sample,
            # temperature=temperature,
        )
        logger.debug(f"Sending prompt:{prompt}")
        response = self._client(prompt, **kwargs)
        logger.debug(f"Received response:{response}")
        return response
