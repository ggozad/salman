import xml.etree.ElementTree as ET
from datetime import datetime

import anthropic

from salman.config import Config
from salman.graph.triples import get_facts_for_subject
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
            model="claude-v1",
            temperature=temperature,
        )
        if stream:
            return await self.client.acompletion_stream(**kwargs, stream=stream)
        else:
            return await self.client.acompletion(**kwargs)

    async def chat(self, question: str, memories=[]) -> str:
        prompt = prompts.CHAT_TEMPLATE.format(
            human=Config.HUMAN,
            question=question,
            memories="\n".join([f"{anthropic.HUMAN_PROMPT}{m}." for m in memories]),
            HUMAN_PROMPT=anthropic.HUMAN_PROMPT,
            AI_PROMPT=anthropic.AI_PROMPT,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        response = await self.completion(prompt=prompt, stream=False)
        return await self.parse_response(
            question, response.get("completion"), memories=memories
        )

    async def parse_response(self, question, response: str, memories=[]) -> dict:
        root = ET.fromstring(f"<root>{response}</root>")
        response = root.find("response")
        if response is not None:
            response = response.text
        if memories:
            return dict(
                response=response or "",
                facts=[],
                request_info=[],
                memories=memories,
            )

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

        # Find all requests for knowledge
        request_info = [n.text for n in root.findall("request_info")]

        memories = set([])
        for info in request_info:
            memories.update(get_facts_for_subject(info))
        # Convert to list to make it JSON serializable
        memories = list(memories)

        if memories:
            return await self.chat(question, memories=memories)

        return dict(
            response=response or "",
            facts=facts,
            request_info=request_info,
            memories=memories,
        )
