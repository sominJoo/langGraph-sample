from langgraph.constants import START, END

from langgraph.graph import StateGraph

from step2.agent.db_agent.db_agent import model_check_query, query_gen_node, should_continue
from step2.agent.db_agent.tool.db_tool import db_query_tool

from step2.graph.state import AgentState
from step2.utils.utillities import create_tool_node_with_fallback


def get_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("query_gen", query_gen_node)

    # Add a node for the model to check the query before executing it
    workflow.add_node("correct_query", model_check_query)

    # 쿼리 실행 노드................
    workflow.add_node("execute_query", create_tool_node_with_fallback([db_query_tool]))

    # Specify the edges between the nodes
    workflow.add_edge(START, "query_gen")
    workflow.add_conditional_edges(
        "query_gen",
        should_continue,
    )
    workflow.add_edge("correct_query", "execute_query")
    workflow.add_edge("execute_query", "query_gen")

    graph = workflow.compile()
    return graph
