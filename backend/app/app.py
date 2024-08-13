from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


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
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )
