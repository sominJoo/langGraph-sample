from typing import Literal

from langgraph.graph import END
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

from step2.agent.db_agent.tool.db_tool import db_query_tool, db_connection
from step2.graph.state import AgentState
from step2.settings import LLM

db = db_connection()
toolkit = SQLDatabaseToolkit(db=db, llm=LLM)
tools = toolkit.get_tools()


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
    Double check the SQLite query for common mistakes, including:
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


# Add a node for the first tool call
def first_tool_call(state: AgentState) -> dict[str, list[AIMessage]]:
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "sql_db_list_tables",
                        "args": {},
                        "id": "tool_abcd123",
                    }
                ],
            )
        ]
    }


def model_check_query(state: AgentState) -> dict[str, list[BaseMessage]]:
    """
    Use this tool to double-check if your query is correct before executing it.
    """
    query_check = db_check_agent()
    return {"messages": [query_check.invoke({"messages": [state["messages"][-1]]})]}


def list_tables_tool():
    return next(tool for tool in tools if tool.name == "sql_db_list_tables")


def get_schema_tool():
    return next(tool for tool in tools if tool.name == "sql_db_schema")


# Describe a tool to represent the end state
class SubmitFinalAnswer(BaseModel):
    """Submit the final answer to the user based on the query results."""

    final_answer: str = Field(..., description="The final answer to the user")


def generate_query():
    # Add a node for a model to generate a query based on the question and schema
    query_gen_system = """You are a SQL expert with a strong attention to detail.
    Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
    DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.
    When generating the query:
    Output the SQL query that answers the input question without a tool call.
    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    If you get an error while executing a query, rewrite the query and try again.
    If you get an empty result set, you should try to rewrite the query to get a non-empty result set. 
    NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.
    If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.
    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""
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
                        content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
                        tool_call_id=tc["id"],
                    )
                )
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
