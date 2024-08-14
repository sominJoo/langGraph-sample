from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition

from step1.agent.agent import Assistant, SimpleAgent
from step1.agent.state import State
from step1.tools.utils.utillities import create_tool_node_with_fallback


def run_graph(local_db_file):
    # 상태 관리 LangGraph 생성
    builder = StateGraph(State)
    simple_agent = SimpleAgent(local_db_file)
    part_1_assistant_runnable = simple_agent.setting()

    # Node 추가: Agent 연결
    builder.add_node("assistant", Assistant(part_1_assistant_runnable))
    # Node 추가: Tool 연결
    builder.add_node("tools", create_tool_node_with_fallback(simple_agent.tools()))
    # Edge 추가 : 시작 -> agent 정의
    builder.add_edge(START, "assistant")
    # 조건부 Edge 추가 : agent를 호출 후 다음 호출할 함수(tools_condition)전달
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    # Edge 추가 : tools(action) 진행 후 agent로 다시 연결
    builder.add_edge("tools", "assistant")

    # 그래프 상태 유지를 위한 체크포인터 설정 -> 전체 그래프에 대한 메모리
    memory = MemorySaver()
    part_1_graph = builder.compile(checkpointer=memory)
