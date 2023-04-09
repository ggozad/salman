from langchain import LLMChain, PromptTemplate
from langchain.llms import Anthropic
from langchain.memory import ConversationBufferWindowMemory

from salman.config import Config


def get_chain() -> LLMChain:
    llm = Anthropic(anthropic_api_key=Config.ANTHROPIC_API_KEY)
    template = """
    {chat_history}

    Human: {question}

    Assistant: Can I think step-by-step?

    Human: Yes, please do.

    Assistant:"""

    prompt = PromptTemplate(
        template=template, input_variables=["question", "chat_history"]
    )
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=3)

    return LLMChain(prompt=prompt, llm=llm, memory=memory)
