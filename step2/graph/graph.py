from langgraph.constants import START

from langgraph.graph import StateGraph

from step2.agent.db_agent.db_agent import first_tool_call, list_tables_tool, get_schema_tool, model_check_query, \
    query_gen_node, should_continue
from step2.agent.db_agent.tool.db_tool import db_query_tool

from step2.graph.state import AgentState
from step2.settings import LLM
from step2.utils.utillities import create_tool_node_with_fallback


def get_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("first_tool_call", first_tool_call)

    # Add nodes for the first two tools
    workflow.add_node(
        "list_tables_tool", create_tool_node_with_fallback([list_tables_tool()])
    )
    workflow.add_node("get_schema_tool", create_tool_node_with_fallback([get_schema_tool()]))
    # Add a node for a model to choose the relevant tables based on the question and available tables
    model_get_schema = LLM.bind_tools([get_schema_tool])
    workflow.add_node(
        "model_get_schema",
        lambda state: {
            "messages": [model_get_schema.invoke(state["messages"])],
        },
    )

    workflow.add_node("query_gen", query_gen_node)

    # Add a node for the model to check the query before executing it
    workflow.add_node("correct_query", model_check_query)

    # Add node for executing the query
    workflow.add_node("execute_query", create_tool_node_with_fallback([db_query_tool]))

    # Specify the edges between the nodes
    workflow.add_edge(START, "first_tool_call")
    workflow.add_edge("first_tool_call", "list_tables_tool")
    workflow.add_edge("list_tables_tool", "model_get_schema")
    workflow.add_edge("model_get_schema", "get_schema_tool")
    workflow.add_edge("get_schema_tool", "query_gen")
    workflow.add_conditional_edges(
        "query_gen",
        should_continue,
    )
    workflow.add_edge("correct_query", "execute_query")
    workflow.add_edge("execute_query", "query_gen")

    graph = workflow.compile()
    return graph
