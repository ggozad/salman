import xml.etree.ElementTree as ET
from datetime import datetime

from salman.config import Config
from salman.llm import prompts
from salman.llm.anthropic import ClaudeLLM
from salman.logging import salman as logger


class SalmanAI:
    def __init__(self):
        self.llm = ClaudeLLM()

    async def chat(self, question: str, history: list[str] = []) -> str:
        prompt = prompts.CHAT_TEMPLATE.format(
            human=Config.HUMAN,
            question=question,
            history="".join(history),
            HUMAN_PROMPT=self.llm.human_prompt,
            AI_PROMPT=self.llm.ai_prompt,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        response = await self.llm.completion(prompt=prompt)
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
            HUMAN_PROMPT=self.llm.human_prompt,
            AI_PROMPT=self.llm.ai_prompt,
        )
        response = await self.llm.completion(prompt)
        root = ET.fromstring(response.get("completion"))
        result = root.find("result")
        if result is not None:
            url = result.find("url").text
            title = result.find("title").text
            answer = result.find("answer").text
            return dict(url=url, title=title, answer=answer)
