from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import AIMessageChunk, ToolMessage, HumanMessage
from pydantic import BaseModel
from typing_extensions import List, cast
from dotenv import load_dotenv

# from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()


app = FastAPI()

# to enable CORS

# from fastapi.middleware.cors import CORSMiddleware

# origins = [
#     "http://localhost:3000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@tool
def answer_to_life() -> str:
    """provides the answer to life"""
    return "Everything is awesome"


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant.",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# llm = ChatOllama(
#     model="llama3.1:8b", temperature=0.4, base_url="http://host.docker.internal:11434"
# )

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

llm_with_tools = llm.bind_tools([answer_to_life])

chain = prompt | llm_with_tools


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequestBody(BaseModel):
    messages: List[ChatMessage]


async def stream_llm_chat(messages: List[ChatMessage]):
    llm_messages = [(message.role, message.content) for message in messages]
    tool_call_message: AIMessageChunk | None = None
    human_input = llm_messages[-1][1]

    async for messageChunk in chain.astream(
        {"chat_history": llm_messages[:-1], "input": human_input}
    ):
        if (
            isinstance(messageChunk, AIMessageChunk)
            and messageChunk.tool_call_chunks is not None
            and len(messageChunk.tool_call_chunks) > 0
        ):
            tool_call_chunk = cast(AIMessageChunk, messageChunk)
            if tool_call_message is None:
                tool_call_message = tool_call_chunk
            else:
                tool_call_message = cast(
                    AIMessageChunk,
                    cast(AIMessageChunk, tool_call_message) + tool_call_chunk,
                )
            print(messageChunk)
            if (
                "done" not in messageChunk.response_metadata
                or "done_reason" not in messageChunk.response_metadata
            ):
                continue

        if (
            tool_call_message is not None
            and len(cast(AIMessageChunk, tool_call_message).tool_calls) > 0
        ):
            for tool_call in cast(AIMessageChunk, tool_call_message).tool_calls:
                selected_tool = {"answer_to_life": answer_to_life}[
                    tool_call["name"].lower()
                ]
                tool_msg: ToolMessage = cast(StructuredTool, selected_tool).invoke(
                    tool_call
                )

                async for toolMessageChunk in llm_with_tools.astream(
                    [
                        HumanMessage(content=human_input),
                        tool_call_message,
                        tool_msg,
                    ]
                ):
                    yield toolMessageChunk.content
        else:
            yield messageChunk.content


@app.post("/")
async def chat(request: ChatRequestBody):
    return StreamingResponse(
        stream_llm_chat(request.messages),
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )
