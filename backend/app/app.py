from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("human", "{input}"),
    ]
)

llm = ChatOllama(
    model="llama3.1:8b", temperature=0.4, base_url="http://host.docker.internal:11434"
)

chain = prompt | llm


async def stream_generate():
    async for i in chain.astream({"input": "Please describe HTTP streaming."}):
        yield i.content


@app.get("/")
async def hello():
    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
    )
