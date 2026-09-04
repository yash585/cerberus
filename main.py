from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import run_agent


app = FastAPI(
    title="CERBERUS",
    description="AI-powered Security Operations Center assistant",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {
        "agent": "CERBERUS",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:
        response = run_agent(request.message)

        return {
            "response": response
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )