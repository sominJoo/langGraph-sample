from langchain_core.messages import (
    FunctionMessage,
    HumanMessage,
)

from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import functools

from step2.agent.db_agent.tool.db_tool import tavily_tool, python_repl
from step2.settings import LLM

BASIC_PROMPT = (
    "system",
    "You are a helpful AI assistant, collaborating with other assistants."
    " Use the provided tools to progress towards answering the question."
    " If you are unable to fully answer, that's OK, another assistant with different tools "
    " will help where you left off. Execute what you can to make progress."
    " If you or any of the other assistants have the final answer or deliverable,"
    " prefix your response with FINAL ANSWER so the team knows to stop."
    " You have access to the following tools: {tool_names}.\n"
    "{system_message}"
)


def create_agent(tools, system_message: str):
    """
    제공된 LLM을 통해 Agent를 생성
    :param tools:
    :param system_message:
    :return:
    """
    # 도구를 OpenAI 함수 형식으로 변환
    functions = [convert_to_openai_function(t) for t in tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            BASIC_PROMPT,
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | LLM.bind_functions(functions)


def agent_node(state, agent, name):
    """
    agent 상태 처리 및 메세지/발신자 정보 반환
    :param state:
    :param agent:
    :param name:
    :return:
    """
    print(state)
    result = agent.invoke(state)
    if isinstance(result, FunctionMessage):
        pass
    else:
        result = HumanMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "sender": name,
    }


# agent 노드 생성
# LLM + 도구 + 시스템 메시지 설정
research_agent = create_agent(
    [tavily_tool],
    system_message="You should provide accurate data for the chart generator to use.",
)
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

# Chart Generator
chart_agent = create_agent(
    [python_repl],
    system_message="Any charts you display will be visible by the user.",
)
chart_node = functools.partial(agent_node, agent=chart_agent, name="Chart Generator")
