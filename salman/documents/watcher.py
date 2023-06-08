from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from unstructured.partition.auto import partition
from watchfiles import Change, DefaultFilter, awatch


class Filter(DefaultFilter):
    def __init__(self, *args) -> None:
        self.extensions = ".md", ".markdown"
        super().__init__(*args)

    def __call__(self, change: Change, path: str) -> bool:
        return path.endswith(self.extensions) and super().__call__(change, path)


async def document_handler(path: str, change: Change):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    elements = partition(filename=path)
    text = "\n\n".join([str(el) for el in elements])
    chunks = splitter.split_text(text)

    return {"text": text, "chunks": chunks}


async def watch_for_documents(*paths: list[Path]):
    async for changes in awatch(*paths, watch_filter=Filter()):
        for change, path in changes:
            await document_handler(path, change)
