import os

from langchain_core.tools import tool
from typing import Annotated
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt.tool_executor import ToolExecutor, ToolInvocation
import json
from langchain_core.messages import FunctionMessage

from step2.settings import TAVILY_API_KEY

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

tavily_tool = TavilySearchResults(max_results=5)
repl = PythonREPL()


@tool
def python_repl(code: Annotated[str, "The python code to execute to generate your chart."]):
    """
    파이썬 코드 실행 TOOL
    """
    print("python_repl")
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Succesfully executed:\n```python\n{code}\n```\nStdout: {result}"


tools = [tavily_tool, python_repl]
tool_executor = ToolExecutor(tools)


def tool_node(state):
    """
    그래프에서 도구를 실행하는 함수
    agent의 액션을 입력 받아 해당 도구를 호출하고 결과 반환
    :param state:
    :return:
    """

    messages = state["messages"]
    last_message = messages[-1]
    print("tool_node", last_message)

    # ToolInvocation을 함수 호출로부터 구성합니다.
    tool_input = json.loads(
        last_message.additional_kwargs["function_call"]["arguments"]
    )

    # 단일 인자 입력은 값으로 직접 전달할 수 있습니다.
    if len(tool_input) == 1 and "__arg1" in tool_input:
        tool_input = next(iter(tool_input.values()))
    tool_name = last_message.additional_kwargs["function_call"]["name"]
    action = ToolInvocation(
        tool=tool_name,
        tool_input=tool_input,
    )

    # 도구 실행자를 호출하고 응답을 받습니다.
    response = tool_executor.invoke(action)

    # 응답을 사용하여 FunctionMessage를 생성합니다.
    function_message = FunctionMessage(
        content=f"{tool_name} response: {str(response)}", name=action.tool
    )
    # 기존 리스트에 추가될 리스트를 반환합니다.
    return {"messages": [function_message]}
