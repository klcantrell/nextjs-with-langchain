from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from app.simple_chat import ChatRequestBody, stream_llm_chat


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


@app.post("/simple-chat")
async def chat(request: ChatRequestBody):
    return StreamingResponse(
        stream_llm_chat(request.messages),
        media_type="text/event-stream",  # this does not seem necessary for the next.js app to get the stream but see https://stackoverflow.com/questions/75825362/attributeerror-encode-when-returning-streamingresponse-in-fastapi/75837557#75837557 for the recommendation to use it
    )
