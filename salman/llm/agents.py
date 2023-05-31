import googlesearch
import trafilatura
from trafilatura.settings import DEFAULT_CONFIG

from salman.graph.triples import search_facts
from salman.llm.anthropic import SalmanAI
from salman.logging import salman as logger

DEFAULT_CONFIG["DEFAULT"]["DOWNLOAD_TIMEOUT"] = "5"


async def search_kb(subjects: list[str]):
    memories = set([])
    for subject in subjects:
        search_results = await search_facts(subject)
        memories.update([result for result, _ in search_results])
    # Convert to list to make it JSON serializable
    memories = list(memories)
    logger.debug(f"KB search on {subjects} results: {memories}")
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
