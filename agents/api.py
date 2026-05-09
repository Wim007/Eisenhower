"""
SamenOntzorgen Agents API
HTTP wrapper om Eisenhower — zodat het admin panel de echte agents kan aansturen.

Starten:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from main import vraag_eisenhower
import crm

load_dotenv()
crm.init_db()

app = FastAPI(title="SamenOntzorgen Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ── Pydantic modellen ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list = []


class LeadAanmaken(BaseModel):
    organisatie: str
    sector: str = ""
    locatie: str = ""
    website: str = ""
    contactpersoon: str = ""
    functie: str = ""
    email: str = ""
    telefoon: str = ""
    linkedin_url: str = ""
    medewerkers: Optional[int] = None
    pijnpunten: list = []
    notities: str = ""


class LeadUpdate(BaseModel):
    organisatie: Optional[str] = None
    sector: Optional[str] = None
    locatie: Optional[str] = None
    website: Optional[str] = None
    contactpersoon: Optional[str] = None
    functie: Optional[str] = None
    email: Optional[str] = None
    telefoon: Optional[str] = None
    linkedin_url: Optional[str] = None
    medewerkers: Optional[int] = None
    pijnpunten: Optional[list] = None
    notities: Optional[str] = None
    bezwaren: Optional[list] = None
    gespreksnotities: Optional[str] = None
    pilot_inhoud: Optional[str] = None
    pilot_prijs: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str


class BerichtRequest(BaseModel):
    type: str = "eerste_benadering"


# ── Bestaande endpoints ──────────────────────────────────────────────────────

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

@app.get("/crm/stats")
async def get_stats():
    return crm.statistieken()


@app.get("/crm/pipeline")
async def get_pipeline():
    return crm.alle_leads_per_status()


@app.get("/crm/followups")
async def get_followups():
    return crm.leads_voor_followup()


@app.get("/crm/leads")
async def list_leads(
    status: str = Query(default=""),
    zoek: str = Query(default=""),
    sector: str = Query(default=""),
):
    return crm.zoek_leads(status=status, sector=sector, zoekterm=zoek)


@app.post("/crm/leads", status_code=201)
async def create_lead(body: LeadAanmaken):
    return crm.voeg_lead_toe(**body.model_dump())


@app.get("/crm/leads/{lead_id}")
async def get_lead(lead_id: int):
    lead = crm.haal_lead_op(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return lead


@app.put("/crm/leads/{lead_id}")
async def update_lead(lead_id: int, body: LeadUpdate):
    lead = crm.update_lead(lead_id, **{k: v for k, v in body.model_dump().items() if v is not None})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return lead


@app.put("/crm/leads/{lead_id}/status")
async def set_status(lead_id: int, body: StatusUpdate):
    try:
        lead = crm.update_status(lead_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return lead


@app.delete("/crm/leads/{lead_id}", status_code=204)
async def delete_lead(lead_id: int):
    if not crm.verwijder_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")


@app.get("/crm/leads/{lead_id}/berichten")
async def get_berichten(lead_id: int):
    if not crm.haal_lead_op(lead_id):
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    return crm.haal_berichten_op(lead_id)


@app.post("/crm/leads/{lead_id}/bericht")
async def genereer_bericht(lead_id: int, body: BerichtRequest):
    lead = crm.haal_lead_op(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead niet gevonden.")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY ontbreekt.")

    type_labels = {
        "eerste_benadering": "een eerste professionele LinkedIn outreach",
        "followup_1":        "een vriendelijke eerste follow-up (3 dagen later)",
        "followup_2":        "een tweede follow-up met extra waarde-propositie (7 dagen later)",
        "followup_3":        "een laatste follow-up met laagdrempelig aanbod (14 dagen later)",
        "reactie_positief":  "een warme reactie op positieve interesse",
        "no_show":           "een beleefd bericht na een no-show voor een gesprek",
        "pilotvoorstel":     "een concreet pilotvoorstel op maat",
    }
    omschrijving = type_labels.get(body.type, "een outreach-bericht")
    pijnpunten_str = ", ".join(lead["pijnpunten"]) if lead.get("pijnpunten") else "niet gespecificeerd"

    prompt = (
        f"Sam, schrijf {omschrijving} voor:\n"
        f"Organisatie: {lead['organisatie']}\n"
        f"Contactpersoon: {lead.get('contactpersoon') or 'onbekend'} "
        f"({lead.get('functie') or 'onbekende functie'})\n"
        f"Sector: {lead.get('sector') or 'zorg'}\n"
        f"Locatie: {lead.get('locatie') or 'Nederland'}\n"
        f"Medewerkers: {lead.get('medewerkers') or 'onbekend'}\n"
        f"Pijnpunten: {pijnpunten_str}\n"
        f"Notities: {lead.get('notities') or 'geen'}\n"
        f"Outreach-teller: {lead.get('outreach_teller', 0)}\n"
        f"Houd het persoonlijk, specifiek voor de zorgsector en max. 200 woorden."
    )

    try:
        bericht = await vraag_eisenhower(prompt)
    except Exception as fout:
        raise HTTPException(status_code=500, detail=str(fout))

    crm.sla_bericht_op(lead_id, body.type, bericht)
    crm.verhoog_outreach_teller(lead_id, bericht[:200])
    if lead.get("status") == "nieuw":
        crm.update_status(lead_id, "benaderd")

    return {"bericht": bericht, "type": body.type}
