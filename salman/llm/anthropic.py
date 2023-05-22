import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime

import anthropic

from salman.config import Config
from salman.llm import prompts
from salman.logging import salman as logger


def handle_exception(loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")


class SalmanAI:
    def __init__(self):
        self.client = anthropic.Client(api_key=Config.ANTHROPIC_API_KEY)

    def on_mount(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_exception)

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

    async def chat(self, question: str, history: list[str] = []) -> str:
        prompt = prompts.CHAT_TEMPLATE.format(
            human=Config.HUMAN,
            question=question,
            history="".join(history),
            HUMAN_PROMPT=anthropic.HUMAN_PROMPT,
            AI_PROMPT=anthropic.AI_PROMPT,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        response = await self.completion(prompt=prompt)
        return await self.parse_response(question, response.get("completion"))

    async def parse_response(self, question, response: str) -> dict:
        root = ET.fromstring(f"{response}")
        text_response = root.find("response")
        if text_response is not None:
            text_response = "".join([t for t in text_response.itertext()])
            text_response = text_response.strip()
        else:
            text_response = ""
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
        print(triplets)
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

        response = dict(
            text_response=text_response,
            facts=facts,
            response=response,
            agent_steps=agent_steps,
        )
        logger.debug(f"Parsed response:{response}")
        return response

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
        response = await self.completion(prompt)
        root = ET.fromstring(response.get("completion"))
        result = root.find("result")
        if result is not None:
            url = result.find("url").text
            title = result.find("title").text
            answer = result.find("answer").text
            return dict(url=url, title=title, answer=answer)
