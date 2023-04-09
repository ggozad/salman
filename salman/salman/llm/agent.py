from langchain.agents import AgentExecutor, AgentType, initialize_agent, load_tools
from langchain.llms import Anthropic

from salman.config import Config


def get_agent() -> AgentExecutor:
    llm = Anthropic(temperature=0, anthropic_api_key=Config.ANTHROPIC_API_KEY)

    # Tools include serpapi, python_repl, wolfram-alpha and others see:
    # https://python.langchain.com/en/latest/modules/agents/tools.html
    tools = load_tools(["serpapi"], llm=llm)

    return initialize_agent(
        tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True
    )
