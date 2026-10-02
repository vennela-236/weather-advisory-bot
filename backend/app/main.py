from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4

from app.graph.workflow import graph

app = FastAPI(
    title="Weather Advisory Support Bot",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


@app.get("/")
def health_check():
    return {"status": "Weather Advisory Bot is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid4())

    result = graph.invoke(
        {
            "question": request.message,
            "session_id": session_id,
        },
        config={
            "configurable": {
                "thread_id": session_id
            }
        },
    )

    return ChatResponse(
        answer=result.get("answer", "I couldn't generate a response."),
        session_id=session_id,
    )