import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    각 Agent와 도구에 대한 다른 노드 생성
    그래프의 각 노드 사이에 전달되는 상태 객체 정의
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
