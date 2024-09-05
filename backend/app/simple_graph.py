from typing import List, TypedDict, Annotated, cast
import os
import operator

from pydantic import BaseModel, Field
from tavily import TavilyClient
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction
from langchain_core.tools import tool
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from langgraph.graph.message import AnyMessage
from langgraph.graph import StateGraph, END

from app.types import ChatMessage
from app.joke_store import JokeVectorStore

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
vectorstore = JokeVectorStore()

# vectorstore.create_index()


class AgentState(TypedDict):
    input: str
    chat_history: list[AnyMessage]
    intermediate_steps: Annotated[list[AgentAction], operator.add]


@tool("web_search")
def web_search(query: str) -> str:
    """Finds general knowledge using web search."""
    search = tavily.search(query=query, max_results=5)
    results = search["results"]
    contexts = "\n---\n".join(
        [
            "\n".join(
                [
                    f'Title: {x["title"]}',
                    f'Content: {x["content"]}',
                    f'Source: {x["url"]}',
                ]
            )
            for x in results
        ]
    )
    return contexts


@tool("joke_database")
def joke_database(query: str) -> str:
    """Finds kids jokes from the database."""
    results = vectorstore.search(query)
    contexts = "\n---\n".join(
        [
            "\n".join(
                [
                    f"Content: {x.page_content}",
                    "Source: joke database",
                ]
            )
            for x in results
        ]
    )
    return contexts


class FinalAnswerInputSchema(BaseModel):
    simple_reply: str = Field(
        description="""if the question didn't require any research, populate this field with a simple reply.
for instance, if the user just says 'hello', respond with a friendly greeting. otherwise, leave this blank."""
    )
    research_reply: str = Field(
        description="""if the question required research, populate this field with the final answer to the user.
    otherwise, leave this blank."""
    )
    sources: str = Field(
        description="""a bulletpoint list provided detailed sources for all information
    referenced during the research process."""
    )


@tool("final_answer", args_schema=FinalAnswerInputSchema)
def final_answer(
    simple_reply: str,
    research_reply: str,
    sources: str,
):
    """Returns the final answer to the user with the following parts to the response:"""
    return ""


tools = [web_search, final_answer, joke_database]


system_prompt = """You are a supervisor of an information gathering workflow.
Given the user's query you must decide what to do with it based on the
list of tools provided to you.

If you see that a tool has been used (in the scratchpad) with a particular
query, do NOT use that same tool with the same query again. Also, do NOT use
any tool more than twice (ie, if the tool appears in the scratchpad twice, do
not use it again).

You should aim to collect information from a diverse range of sources before
providing the answer to the user. Once you have collected plenty of information
to answer the user's question (stored in the scratchpad) use the final_answer
tool."""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("assistant", "scratchpad: {scratchpad}"),
    ]
)


# define a function to transform intermediate_steps from list
# of AgentAction to scratchpad string
def create_scratchpad(intermediate_steps: list[AgentAction]):
    research_steps = []
    for i, action in enumerate(intermediate_steps):
        if action.log != "TBD":
            # this was the ToolExecution
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\n"
                f"Output: {action.log}"
            )
    return "\n---\n".join(research_steps)


supervisor: RunnableSerializable = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "scratchpad": lambda x: create_scratchpad(
            intermediate_steps=x["intermediate_steps"]
        ),
    }
    | prompt
    | llm.bind_tools(tools, tool_choice="any")
)


def run_supervisor(state: AgentState):
    print("run_supervisor")
    print(f"intermediate_steps: {state['intermediate_steps']}")
    out = supervisor.invoke(state)
    tool_name = out.tool_calls[0]["name"]
    tool_args = out.tool_calls[0]["args"]
    action_out = AgentAction(tool=tool_name, tool_input=tool_args, log="TBD")
    return {"intermediate_steps": [action_out]}


def router(state: AgentState):
    # return the tool name to use
    if isinstance(state["intermediate_steps"], list):
        return state["intermediate_steps"][-1].tool
    else:
        # if we output bad format go to final answer
        print("Router invalid format")
        return "final_answer"


tool_str_to_func = {
    "web_search": web_search,
    "final_answer": final_answer,
    "joke_database": joke_database,
}


def run_tool(state: AgentState):
    # use this as helper function so we repeat less code
    tool_name = state["intermediate_steps"][-1].tool
    tool_args = state["intermediate_steps"][-1].tool_input
    print(f"{tool_name}.invoke(input={tool_args})")
    # run tool
    out = tool_str_to_func[tool_name].invoke(input=tool_args)
    action_out = AgentAction(tool=tool_name, tool_input=tool_args, log=str(out))
    return {"intermediate_steps": [action_out]}


graph = StateGraph(AgentState)

graph.add_node("supervisor", run_supervisor)
graph.add_node("web_search", run_tool)
graph.add_node("joke_database", run_tool)
graph.add_node("final_answer", run_tool)

graph.set_entry_point("supervisor")

graph.add_conditional_edges(
    source="supervisor",  # where in graph to start
    path=router,  # function to determine which node is called
)

# create edges from each tool back to the supervisor
for tool_obj in tools:
    if tool_obj.name != "final_answer":
        graph.add_edge(tool_obj.name, "supervisor")

# if anything goes to final answer, it must then move to END
graph.add_edge("final_answer", END)


def get_agent():
    return graph.compile()


async def stream_graph_chat(messages: List[ChatMessage]):
    agent = get_agent()

    llm_messages = [(message.role, message.content) for message in messages]
    human_input = llm_messages[-1][1]

    async for state in agent.astream(
        {"chat_history": llm_messages[:-1], "input": human_input}
    ):
        if "supervisor" not in state:
            continue

        state = cast(AgentState, state["supervisor"])
        tool_name = state["intermediate_steps"][-1].tool
        tool_args = state["intermediate_steps"][-1].tool_input

        yield f"Running {tool_name} with input: {tool_args}\n"


# agent = get_agent()

# agent.invoke(
#     {
#         "input": "I'm a softeware developer trying to learn about web streaming. Please introduce the concept to me.",
#         "chat_history": [],
#     }
# )

# agent.invoke(
#     {
#         "input": "Will you please find me a few kids' jokes?",
#         "chat_history": [],
#     }
# )
