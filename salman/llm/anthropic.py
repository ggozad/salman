import anthropic

from salman.config import Config
from salman.logging import salman as logger


class ClaudeLLM:
    human_prompt = anthropic.HUMAN_PROMPT
    ai_prompt = anthropic.AI_PROMPT

    def __init__(self):
        self.client = anthropic.Client(api_key=Config.ANTHROPIC_API_KEY)

    async def completion(
        self,
        prompt: str,
        max_tokens_to_sample=512,
        temperature=0.0,
        stream=False,
    ) -> str:
        kwargs = dict(
            prompt=prompt,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            max_tokens_to_sample=max_tokens_to_sample,
            model="claude-v1",
            temperature=temperature,
        )
        logger.debug(f"Sending prompt:{prompt}")
        if stream:
            response = await self.client.acompletion_stream(**kwargs, stream=stream)
        else:
            response = await self.client.acompletion(**kwargs)
        logger.debug(f"Received response:{response}")
        return response
