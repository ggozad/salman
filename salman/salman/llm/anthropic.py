import xml.etree.ElementTree as ET
from datetime import datetime

import anthropic

from salman.config import Config
from salman.graph.triples import Node, create_semantic_triple
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
            question, response.get("completion"), terminal=bool(memories)
        )

    async def parse_response(self, question, response: str, terminal=False) -> dict:
        root = ET.fromstring(f"<root>{response}</root>")
        response = root.find("response")
        if response is not None:
            response = response.text
        if terminal:
            return dict(
                response=response or "",
                facts=[],
                request_info=[],
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
        # Persist the facts in the database
        for fact in facts:
            create_semantic_triple(
                Node(name=fact.get("subject")),
                fact.get("predicate"),
                Node(name=fact.get("object")),
            )

        # Find all requests for knowledge
        request_info = [n.text for n in root.findall("request_info")]

        memories = []
        for info in request_info:
            subject = Node(name=info)
            triples = subject.get_triples()
            for triple in triples:
                memories.append(" ".join([subject.name, *triple]))

        if memories:
            return await self.chat(question, memories=memories)

        return dict(
            response=response or "",
            facts=facts,
            request_info=request_info,
        )
