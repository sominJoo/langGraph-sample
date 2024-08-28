from step2.agent.agent_setting import research_node, chart_node
from step2.agent.db_agent.tool.db_tool import tool_node
from step2.graph.query_route import query_route
from langgraph.graph import END, StateGraph
from step2.graph.state import AgentState


def get_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("Researcher", research_node)
    workflow.add_node("Chart Generator", chart_node)
    workflow.add_node("call_tool", tool_node)

    workflow.add_conditional_edges(
        "Researcher",
        query_route,
        {"continue": "Chart Generator", "call_tool": "call_tool", "end": END},
    )
    workflow.add_conditional_edges(
        "Chart Generator",
        query_route,
        {"continue": "Researcher", "call_tool": "call_tool", "end": END},
    )

    workflow.add_conditional_edges(
        "call_tool",
        lambda x: x["sender"],
        {
            "Researcher": "Researcher",
            "Chart Generator": "Chart Generator",
        },
    )
    workflow.set_entry_point("Researcher")
    graph = workflow.compile()
    return graph
