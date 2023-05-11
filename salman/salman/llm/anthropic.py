import anthropic

from salman.config import Config
from salman.llm import prompts


class SalmanAI:
    def __init__(self):
        self.client = anthropic.Client(api_key=Config.ANTHROPIC_API_KEY)

    async def completion(
        self,
        prompt: str,
        max_tokens_to_sample=256,
        temperature=0.0,
        stream=True,
    ) -> str:
        kwargs = dict(
            prompt=prompt,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            max_tokens_to_sample=max_tokens_to_sample,
            model="claude-v1.3",
            temperature=temperature,
        )
        if stream:
            return await self.client.acompletion_stream(**kwargs, stream=stream)
        else:
            return await self.client.acompletion(**kwargs)

    async def chat(self, question: str) -> str:
        prompt = prompts.CHAT_TEMPLATE.format(
            human=Config.HUMAN,
            question=question,
            HUMAN_PROMPT=anthropic.HUMAN_PROMPT,
            AI_PROMPT=anthropic.AI_PROMPT,
        )
        return await self.completion(prompt=prompt, stream=False)
