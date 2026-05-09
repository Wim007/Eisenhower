"""
SamenOntzorgen Agents API
HTTP wrapper om Eisenhower — zodat het admin panel de echte agents kan aansturen.

Starten:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from main import vraag_eisenhower

load_dotenv()

app = FastAPI(title="SamenOntzorgen Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Bericht mag niet leeg zijn.")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY ontbreekt.")

    # Voeg gesprekshistorie toe als context voor Eisenhower
    if req.history:
        regels = []
        for m in req.history[-6:]:
            rol = "Wim" if m.get("role") == "user" else "Eisenhower"
            regels.append(f"{rol}: {m.get('content', '')}")
        prompt = "Gesprekshistorie:\n" + "\n".join(regels) + f"\n\nWim: {req.message.strip()}"
    else:
        prompt = req.message.strip()

    try:
        antwoord = await vraag_eisenhower(prompt)
        return {"reply": antwoord}
    except Exception as fout:
        raise HTTPException(status_code=500, detail=str(fout))
