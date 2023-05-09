from langchain.chains import ConversationChain
from langchain.llms import Anthropic

from salman.config import Config
from salman.llm.graph.memory import ConversationKGMemory
from salman.llm.graph.prompts import CONVERSATION_PROMPT

llm = Anthropic(temperature=0, anthropic_api_key=Config.ANTHROPIC_API_KEY)

memory = ConversationKGMemory(llm=llm)
chain = ConversationChain(
    llm=llm,
    verbose=True,
    prompt=CONVERSATION_PROMPT,
    memory=ConversationKGMemory(llm=llm),
)
