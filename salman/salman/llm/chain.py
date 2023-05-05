from langchain import LLMChain, PromptTemplate
from langchain.llms import Anthropic
from langchain.memory import ConversationBufferWindowMemory

from salman.config import Config


def get_chain() -> LLMChain:
    llm = Anthropic(anthropic_api_key=Config.ANTHROPIC_API_KEY)
    template = """
    Your name is Salman. You are a personal assistant AI to a computer geek.
    When you are asked a question, you should answer it. If you don't know the answer, you should say so.
    You should also be able to ask questions to clarify the question.

    When you need to think step by step, you should say so and describe the steps you take.

    Assistant: Can I think step-by-step?

    Human: Yes, please do if you think you should. If you don't think you should, then answer simply.


    {chat_history}

    Human: {question}

    Assistant:"""

    prompt = PromptTemplate(
        template=template, input_variables=["question", "chat_history"]
    )
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=3)

    return LLMChain(prompt=prompt, llm=llm, memory=memory)
