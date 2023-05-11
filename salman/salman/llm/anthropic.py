import xml.etree.ElementTree as ET

import anthropic

from salman.config import Config
from salman.graph.triples import Object, Subject, create_semantic_triple
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

        response = await self.completion(prompt=prompt, stream=False)
        return self.parse_response(response.get("completion"))

    def parse_response(self, response: str) -> dict:
        root = ET.fromstring(f"<root>{response}</root>")
        response = root.find("response")
        if response is not None:
            response = response.text

        # Find all knowledge triplets
        triplets = root.findall("triplet")
        facts = [
            dict(
                subject=triplet.find("subject").text,
                predicate=triplet.find("predicate").text,
                object=triplet.find("object").text,
            )
            for triplet in triplets
        ]
        # Persist the facts in the database
        for fact in facts:
            create_semantic_triple(
                Subject(name=fact.get("subject")),
                fact.get("predicate"),
                Object(name=fact.get("object")),
            )
        return dict(response=response or "", facts=facts)
