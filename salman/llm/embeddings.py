import asyncio

from sentence_transformers import SentenceTransformer

from salman.logging import salman as logger

model = None

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


async def load_model():
    global model
    if model is None:
        logger.debug(f"Loading {MODEL}")
        model = SentenceTransformer(MODEL)
        logger.debug(f"Loaded {MODEL}")


async def get_embeddings(text: str):
    await load_model()
    return model.encode(text)


loop = asyncio.get_event_loop()
loop.create_task(load_model())
