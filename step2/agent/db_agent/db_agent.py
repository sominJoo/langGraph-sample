from typing import Literal

from langgraph.graph import END
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

from step2.agent.db_agent.tool.db_tool import db_query_tool
from step2.graph.state import AgentState
from step2.settings import LLM


# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


def db_check_agent():
    query_check_system = """You are a SQL expert with a strong attention to detail.
    Double check the Postgres query for common mistakes, including:
    - Using NOT IN with NULL values
    - Using UNION when UNION ALL should have been used
    - Using BETWEEN for exclusive ranges
    - Data type mismatch in predicates
    - Properly quoting identifiers
    - Using the correct number of arguments for functions
    - Casting to the correct data type
    - Using the proper columns for joins
    
    If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.
    
    You will call the appropriate tool to execute the query after running this check."""

    query_check_prompt = ChatPromptTemplate.from_messages(
        [("system", query_check_system), ("placeholder", "{messages}")]
    )
    query_check = query_check_prompt | LLM.bind_tools(
        [db_query_tool], tool_choice="required"
    )

    return query_check


def model_check_query(state: AgentState) -> dict[str, list[BaseMessage]]:
    """
    Use this tool to double-check if your query is correct before executing it.
    """
    query_check = db_check_agent()
    return {"messages": [query_check.invoke({"messages": [state["messages"][-1]]})]}


# Describe a tool to represent the end state
class SubmitFinalAnswer(BaseModel):
    """Submit the final answer to the user based on the query results."""
    final_answer: str = Field(..., description="The final answer to the user")


def generate_query():
    query_gen_system = """세부 사항에 주의를 기울이는 SQL 전문가입니다.
                입력 질문이 주어지면, 먼저 DB의 스키마 정보와, 테이블 목록을 조회합니다 데이터베이스의 스키마 정보와 테이블 목록, 그리고 테이블의 DDL을 조회합니다.
                그 후 구문적으로 올바른 Postgresl 쿼리를 출력하여 실행한 다음 쿼리 결과를 보고 답을 반환합니다.
                스키마 설명에서 볼 수 있는 컬럼 이름만 사용하도록 주의합니다. 존재하지 않는 컬럼은 쿼리하지 않도록 주의합니다. 또한 어느 컬럼이 어느 테이블에 있는지도 주의해야 합니다.

                SubmitFinalAnswer 이외의 도구를 호출하여 최종 답변을 제출하지 마십시오.
                
                쿼리를 생성할 때:
                도구 호출 없이 입력된 질문에 응답하는 SQL 쿼리를 출력합니다.
                사용자가 얻을 특정 수의 예제를 지정하지 않는 한 쿼리를 항상 최대 5개의 결과로 제한합니다.
                데이터베이스에서 가장 흥미로운 예제를 반환하기 위해 관련 열로 결과를 주문할 수 있습니다.
                특정 테이블의 모든 열에 대해 쿼리하지 말고 해당 열에 대해서만 질문하십시오.
                쿼리를 실행하는 중에 오류가 발생하면 쿼리를 다시 작성하고 다시 시도하십시오.
                빈 결과 집합이 있으면 쿼리를 다시 작성하여 비어 있지 않은 결과 집합을 가져오도록 해야 합니다.
                질문에 답하기에 충분한 정보가 없다면 절대 지어내지 마세요... 단지 당신이 충분한 정보가 없다고 말하세요.
                입력된 질문에 답하기에 충분한 정보가 있는 경우 SubmitFinalAnswer 해당 도구를 호출하여 최종 답변을 사용자에게 제출하기만 하면 됩니다.
                데이터베이스에 DML 문(Insert, UPDATE, DELETE, Drop 등)을 작성하지 마십시오."""
    query_gen_prompt = ChatPromptTemplate.from_messages(
        [("system", query_gen_system), ("placeholder", "{messages}")]
    )
    query_gen = query_gen_prompt | LLM.bind_tools([SubmitFinalAnswer])
    return query_gen


def query_gen_node(state: AgentState):
    query_gen = generate_query()
    message = query_gen.invoke(state)
    # Sometimes, the LLM will hallucinate and call the wrong tool. We need to catch this and return an error message.
    tool_messages = []
    if message.tool_calls:
        for tc in message.tool_calls:
            if tc["name"] != "SubmitFinalAnswer":
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: The wrong tool was called: {tc['name']}. "
                                f"Please fix your mistakes. "
                                f"Remember to only call SubmitFinalAnswer to submit the final answer."
                                f"Generated queries should be outputted WITHOUT a tool call.",
                        tool_call_id=tc["id"],
                    )
                )
            else:
                # 최종 답변을 콘솔에 출력
                final_answer_message = tc["args"]["final_answer"]
                print(f" >>>>  Final Answer:\n{final_answer_message}")
    else:
        tool_messages = []
    return {"messages": [message] + tool_messages}


# Define a conditional edge to decide whether to continue or end the workflow
def should_continue(state: AgentState) -> Literal[END, "correct_query", "query_gen"]:
    messages = state["messages"]
    last_message = messages[-1]
    # If there is a tool call, then we finish
    if getattr(last_message, "tool_calls", None):
        return END
    if last_message.content.startswith("Error:"):
        return "query_gen"
    else:
        return "correct_query"
