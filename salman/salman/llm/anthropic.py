import xml.etree.ElementTree as ET
from datetime import datetime

import anthropic

from salman.config import Config
from salman.llm import prompts
from salman.logging import salman as logger


class SalmanAI:
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
        if stream:
            return await self.client.acompletion_stream(**kwargs, stream=stream)
        else:
            return await self.client.acompletion(**kwargs)

    async def chat(self, question: str, history: list[str] = []) -> str:
        prompt = prompts.CHAT_TEMPLATE.format(
            human=Config.HUMAN,
            question=question,
            history="".join(history),
            HUMAN_PROMPT=anthropic.HUMAN_PROMPT,
            AI_PROMPT=anthropic.AI_PROMPT,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        logger.debug(f"Chat Prompt:{prompt}")
        response = await self.completion(prompt=prompt)
        logger.debug(f"Chat Response:{response.get('completion')})")

        return await self.parse_response(question, response.get("completion"))

    async def parse_response(self, question, response: str) -> dict:
        root = ET.fromstring(f"{response}")
        text_response = root.find("response")
        if text_response is not None:
            text_response = "".join([t for t in text_response.itertext()])

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
            text_response=text_response.strip() or "",
            facts=facts,
            response=response,
            agent_steps=agent_steps,
        )

    async def search(self, subject: str, pages: list[dict]):
        prompt_text = ""
        for page in pages:
            xml = ET.Element("page")
            ET.SubElement(xml, "title").text = page["title"]
            ET.SubElement(xml, "url").text = page["url"]
            ET.SubElement(xml, "text").text = page["text"]
            prompt_text += ET.tostring(xml).decode("utf-8")
        prompt = prompts.SEARCH_TEMPLATE.format(
            subject=subject,
            pages=prompt_text,
            HUMAN_PROMPT=anthropic.HUMAN_PROMPT,
            AI_PROMPT=anthropic.AI_PROMPT,
        )
        logger.debug(f"Search Prompt:{prompt}")
        response = await self.completion(prompt)
        logger.debug(f"Search Response:{response.get('completion')})")
        root = ET.fromstring(response.get("completion"))
        result = root.find("result")
        if result is not None:
            url = result.find("url").text
            title = result.find("title").text
            answer = result.find("answer").text
            return dict(url=url, title=title, answer=answer)
