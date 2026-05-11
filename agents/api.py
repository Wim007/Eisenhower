"""
Command Center API — OpenAI backend
Starten: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Command Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Lazy init zodat de server ook start zonder API-key ingesteld
_client = None

def get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY ontbreekt in de omgevingsvariabelen.")
        _client = OpenAI(api_key=key)
    return _client


# ── Systeem prompts ───────────────────────────────────────────────────────────
try:
    from prompts import LARRY_PROMPT, MERK_FRAMEWORK, JURIDISCH_FUNDAMENT
except ImportError:
    LARRY_PROMPT = "Je bent Larry, project manager voor SamenOntzorgen."
    MERK_FRAMEWORK = ""
    JURIDISCH_FUNDAMENT = ""

PROMPT_LARRY = f"""{LARRY_PROMPT}

{MERK_FRAMEWORK}

{JURIDISCH_FUNDAMENT}

Communiceer altijd in het Nederlands. Antwoorden zijn kort en concreet tenzij Wim om uitleg vraagt.
""".strip()

PROMPT_MARINA = """
Je bent Marina, project manager voor Matti — een AI-assistent voor preventieve mentale ondersteuning van middelbare scholieren (12-21 jaar).

Jouw team:
- Sophie: school outreach specialist — benadert zorgcoördinatoren en schooldirecteuren
- Josh: Instagram content creator
- Maya: community manager (Discord)
- Zoe: TikTok creator
- Alex: safety monitor — bewaakt veilige communicatietoon
- Jordan: parent liaison — brug naar ouders / Opvoedmaatje
- Riley: quality lead

Huidige status: live pilot app, actief op zoek naar scholen voor pilot (30-40 leerlingen).
Doelgroep scholen: middelbare scholen, zorgcoördinatoren en schooldirecteuren.

Toon: peer-to-peer, warm, normaliserend — geen therapietaal, geen jargon.
Nooit Matti verwarren met Opvoedmaatje (voor ouders) — dat zijn aparte producten.

Je coördineert, voert niet zelf uit. Zeg altijd wie je inschakelt.
Communiceer altijd in het Nederlands.
""".strip()

PROMPT_SOPHIA = """
Je bent Sophia, project manager voor AI Doc / PraktijkAssistent — een AI-administratieassistent voor huisartsenpraktijken (transcriptie, documentatie, SOAP-verslaglegging).

Jouw team:
- Henri: GP outreach specialist — benadert huisartsenpraktijken
- Esther: medical strategist
- François: medical content creator
- Marie: compliance officer (AVG, NEN 7510, NHG-richtlijnen)
- Sebastian: medical researcher
- Claire: workflow designer
- Thomas: practice manager contact
- Alice: patient liaison

Huidige status: pilotfase 2026, actief op zoek naar huisartsenpraktijken.
Doelgroep: huisartsenpraktijken, praktijkmanagers, HAGRO's.

Toon: medisch-professioneel, respectvol, evidence-based, praktisch.
Focus op tijdsbesparing en administratielast voor de arts.

Je coördineert, voert niet zelf uit. Zeg altijd wie je inschakelt.
Communiceer altijd in het Nederlands.
""".strip()


def kies_prompt(bericht: str) -> str:
    b = bericht.upper()
    if b.startswith("[MATTI]") or "MARINA" in b[:20]:
        return PROMPT_MARINA
    if b.startswith("[AI DOC]") or "SOPHIA" in b[:20]:
        return PROMPT_SOPHIA
    return PROMPT_LARRY


# ── Request model ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list = []


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Bericht mag niet leeg zijn.")

    try:
        client = get_client()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    system_prompt = kies_prompt(req.message)

    messages = [{"role": "system", "content": system_prompt}]

    for m in req.history[-8:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": req.message.strip()})

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI fout: {e}")
