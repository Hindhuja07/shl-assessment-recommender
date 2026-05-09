from fastapi import FastAPI
from app.models import ChatRequest, ChatResponse
from app.conversation import chat

app = FastAPI(title="SHL Assessment Recommender", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    return chat(request.messages)
