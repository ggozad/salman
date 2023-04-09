from langchain.llms import Anthropic
from langchain import PromptTemplate, LLMChain

from salman.config import Config

llm = Anthropic(anthropic_api_key=Config.ANTHROPIC_API_KEY)
template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])
llm_chain = LLMChain(prompt=prompt, llm=llm)

template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])
bot = LLMChain(prompt=prompt, llm=llm)
