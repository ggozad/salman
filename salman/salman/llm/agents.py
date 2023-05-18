import googlesearch
import trafilatura
from trafilatura.settings import DEFAULT_CONFIG

from salman.graph.triples import get_facts_for_subject
from salman.llm.anthropic import SalmanAI

DEFAULT_CONFIG["DEFAULT"]["DOWNLOAD_TIMEOUT"] = "2"


def search_kb(subjects: list[str]):
    memories = set([])
    for subject in subjects:
        memories.update(get_facts_for_subject(subject))
    # Convert to list to make it JSON serializable
    memories = list(memories)
    return memories


async def search_internet(subjects: list[str]):
    assistant = SalmanAI()
    for subject in subjects:
        for result in googlesearch.search(subject, advanced=True, num_results=3):
            title = result.title
            url = result.url
            html = trafilatura.fetch_url(url)
            text = trafilatura.extract(html)
            if not text:
                continue
            response = await assistant.search(
                subject, pages=[dict(url=url, text=text, title=title)]
            )
            return response
