from langchain.indexes import GraphIndexCreator
from langchain.llms import Anthropic

from salman.config import Config

index_creator = GraphIndexCreator(
    llm=Anthropic(temperature=0, anthropic_api_key=Config.ANTHROPIC_API_KEY)
)
