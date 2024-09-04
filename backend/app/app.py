from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.simple_chat import stream_llm_chat
from app.simple_graph import stream_graph_chat
from app.types import ChatRequestBody


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


@app.post("/simple-chat")
async def simple_chat(request: ChatRequestBody):
    return StreamingResponse(
        stream_llm_chat(request.messages),
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )


@app.post("/graph-chat")
async def graph_chat(request: ChatRequestBody):
    return StreamingResponse(
        stream_graph_chat(request.messages),
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )
