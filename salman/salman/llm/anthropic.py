import xml.etree.ElementTree as ET
from datetime import datetime

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

    async def parse_response(self, question, answer: str, memories=[]) -> dict:
        root = ET.fromstring(f"{answer}")
        response = root.find("response")
        if response is not None:
            response = "".join([t for t in response.itertext()])

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

        agent_steps = root.find("agents")
        if agent_steps:
            kb_search = agent_steps.findall("kb_search")
            kb_subjects = [search.text for search in kb_search]
            internet_search = agent_steps.findall("internet_search")
            internet_subjects = [search.text for search in internet_search]
            agent_steps = {
                "kb_search": kb_subjects,
                "internet_search": internet_subjects,
            }

        return dict(
            response=response or "",
            facts=facts,
            memories=memories,
            answer=answer,
            agent_steps=agent_steps,
        )
