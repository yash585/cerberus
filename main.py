from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import run_agent


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CERBERUS",
    description="AI-powered Security Operations Center assistant",
    version="1.0.0"
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: list = []


# ============================================================
# JSON DATA LOADER
# ============================================================

def load_json(filename: str):

    file_path = DATA_DIR / filename

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        raise HTTPException(
            status_code=500,
            detail=f"Data file not found: {filename}"
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in: {filename}"
        )


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
def serve_frontend():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "agent": "CERBERUS",
        "status": "healthy",
        "model": "online",
        "tools": 5
    }


# ============================================================
# UPTIME ROBOT MONITOR
# ============================================================

@app.api_route(
    "/uptimemonitor",
    methods=["GET", "HEAD"]
)
def uptime_monitor():

    return {
        "status": "online"
    }


# ============================================================
# AI CHAT ENDPOINT
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:

        result = run_agent(
            request.message
        )

        return {
            "response": result.get(
                "response",
                ""
            ),
            "tool_calls": result.get(
                "tool_calls",
                []
            )
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# INCIDENT API
# ============================================================

@app.get("/api/incidents")
def get_incidents():

    return load_json(
        "incidents.json"
    )


@app.get("/api/incidents/search")
def search_incident_records(
    q: str = Query(...)
):

    incidents = load_json(
        "incidents.json"
    )

    query = q.lower()

    results = []

    for incident in incidents:

        searchable_text = " ".join(
            str(value).lower()
            for value in incident.values()
        )

        if query in searchable_text:

            results.append(
                incident
            )

    return results


# ============================================================
# ASSET API
# ============================================================

@app.get("/api/assets")
def get_assets():

    return load_json(
        "assets.json"
    )


@app.get("/api/assets/search")
def search_asset_records(
    q: str = Query(...)
):

    assets = load_json(
        "assets.json"
    )

    query = q.lower()

    results = []

    for asset in assets:

        searchable_text = " ".join(
            str(value).lower()
            for value in asset.values()
        )

        if query in searchable_text:

            results.append(
                asset
            )

    return results


# ============================================================
# KNOWLEDGE BASE API
# ============================================================

@app.get("/api/knowledge-base")
def get_knowledge_base(
    q: str = Query(default="")
):

    articles = load_json(
        "knowledge_base.json"
    )

    if not q:

        return articles


    query_words = q.lower().split()

    results = []

    for article in articles:

        searchable_text = (
            article["title"]
            + " "
            + article["content"]
        ).lower()


        if any(
            word in searchable_text
            for word in query_words
        ):

            results.append(
                article
            )


    return results