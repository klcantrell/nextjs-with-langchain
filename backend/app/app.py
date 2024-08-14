from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel
from typing import List


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

llm = ChatOllama(
    model="llama3.1:8b", temperature=0.4, base_url="http://host.docker.internal:11434"
)

chain = prompt | llm


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequestBody(BaseModel):
    messages: List[ChatMessage]


async def stream_llm_chat(messages: List[ChatMessage]):
    llm_messages = [(message.role, message.content) for message in messages]
    async for i in chain.astream(
        {"chat_history": llm_messages[:-1], "input": llm_messages[-1][1]}
    ):
        yield i.content


@app.post("/")
async def chat(request: ChatRequestBody):
    return StreamingResponse(
        stream_llm_chat(request.messages),
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )
