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
import crm

load_dotenv()

app = FastAPI(title="SamenOntzorgen Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "PUT", "DELETE"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list = []


class LeadCreate(BaseModel):
    naam: str
    bedrijf: str = ""
    functie: str = ""
    email: str = ""
    telefoon: str = ""
    notities: str = ""


class LeadUpdate(BaseModel):
    naam: str | None = None
    bedrijf: str | None = None
    functie: str | None = None
    email: str | None = None
    telefoon: str | None = None
    stage: str | None = None
    notities: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Bericht mag niet leeg zijn.")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY ontbreekt.")

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


# ── CRM endpoints ────────────────────────────────────────────────────────────

@app.get("/crm/leads")
async def list_leads():
    return crm.get_all_leads()


@app.post("/crm/leads", status_code=201)
async def create_lead(body: LeadCreate):
    return crm.create_lead(**body.model_dump())


@app.get("/crm/leads/{lead_id}")
async def get_lead(lead_id: int):
    lead = crm.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return lead


@app.put("/crm/leads/{lead_id}")
async def update_lead(lead_id: int, body: LeadUpdate):
    try:
        lead = crm.update_lead(lead_id, **{k: v for k, v in body.model_dump().items() if v is not None})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return lead


@app.delete("/crm/leads/{lead_id}")
async def delete_lead(lead_id: int):
    if not crm.delete_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return {"ok": True}


@app.get("/crm/stats")
async def pipeline_stats():
    return crm.pipeline_stats()


@app.post("/crm/leads/{lead_id}/sam")
async def genereer_sam(lead_id: int):
    lead = crm.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY ontbreekt.")
    prompt = (
        f"Sam, stuur een professioneel en persoonlijk LinkedIn outreach-bericht naar "
        f"{lead['naam']} ({lead['functie'] or 'onbekende functie'} bij {lead['bedrijf'] or 'onbekend bedrijf'}). "
        f"Extra context: {lead['notities'] or 'geen'}. Houd het kort, warm en gericht op kennismaking."
    )
    try:
        bericht = await vraag_eisenhower(prompt)
        return {"bericht": bericht}
    except Exception as fout:
        raise HTTPException(status_code=500, detail=str(fout))
