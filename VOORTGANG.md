# Voortgang — Eisenhower / SamenOntzorgen

> Branch: `claude/copy-eisenhower-file-Nu34z` | PR: [#1](https://github.com/Wim007/Eisenhower/pull/1)
> Laatste sessie: 10 mei 2026

---

## Wat is dit project?

Multi-agent AI-omgeving met Eisenhower als centrale orchestrator.  
37 agents verdeeld over 3 projecten (SamenOntzorgen / Matti / AI Doc).  
Beheerdashboard via Node.js (`admin/`) + FastAPI agents-backend (`agents/`).

---

## Wat is er in deze sessie gebouwd?

### 1. `agents/crm.py` — SQLite CRM-module (nieuw)

Volledige CRM-database zonder externe dependencies (alleen stdlib).

**Tabellen:**
- `leads` — 26 velden: organisatie, sector, locatie, website, contactpersoon, functie, email, telefoon, linkedin_url, medewerkers, pijnpunten (JSON), notities, status, datum_toegevoegd, datum_benaderd, datum_laatste_actie, datum_afspraak, datum_voorstel, datum_close, outreach_teller, laatste_bericht, bezwaren (JSON), gespreksnotities, pilot_inhoud, pilot_prijs, extra_data (JSON)
- `activiteiten` — activiteitenlog per lead (cascade-delete)
- `berichten` — Sam-berichten per lead (cascade-delete)

**Statussen:** nieuw → benaderd → reactie → afspraak → voorstel → gewonnen / verloren / geparkeerd

**Follow-up logica:** `FOLLOWUP_DAGEN = [3, 7, 14]` — drempel stijgt met elke outreach-poging

**Key-functies:**
| Functie | Beschrijving |
|---|---|
| `voeg_lead_toe()` | Nieuwe lead aanmaken |
| `update_status()` | Status + bijbehorend datumveld automatisch bijwerken |
| `update_lead()` | Vrije veld-updates (JSON-velden worden geserialiseerd) |
| `verwijder_lead()` | Cascade-delete incl. berichten + activiteiten |
| `zoek_leads()` | Filters: status / sector / zoekterm |
| `alle_leads_per_status()` | Kanban-structuur voor dashboard |
| `leads_voor_followup()` | Leads die te lang inactief zijn |
| `verhoog_outreach_teller()` | +1 na elk Sam-bericht |
| `sla_bericht_op()` | Bericht opslaan in `berichten`-tabel |
| `haal_berichten_op()` | Berichtengeschiedenis per lead |
| `statistieken()` | Totaal, per_status, conversie_pct, followups_nodig |

**Configuratie:** `CRM_DB_PATH` env-var (standaard: `agents/samenontzorgen_crm.db`)

---

### 2. `agents/api.py` — FastAPI CRM-endpoints (uitgebreid)

`crm.init_db()` wordt aangeroepen bij startup.

**Nieuwe endpoints:**

| Methode | Pad | Actie |
|---|---|---|
| GET | `/crm/stats` | Statistieken (totaal, per status, conversie, followups) |
| GET | `/crm/pipeline` | Kanban-structuur (leads per status) |
| GET | `/crm/followups` | Leads die follow-up nodig hebben |
| GET | `/crm/leads?status=&zoek=&sector=` | Gefilterde lijst |
| POST | `/crm/leads` | Nieuwe lead aanmaken (status 201) |
| GET | `/crm/leads/{id}` | Één lead ophalen |
| PUT | `/crm/leads/{id}` | Lead bewerken |
| PUT | `/crm/leads/{id}/status` | Status wijzigen |
| DELETE | `/crm/leads/{id}` | Lead verwijderen (status 204) |
| GET | `/crm/leads/{id}/berichten` | Berichtengeschiedenis |
| POST | `/crm/leads/{id}/bericht` | Sam-bericht genereren + opslaan |

**Sam-bericht types:** `eerste_benadering`, `followup_1`, `followup_2`, `followup_3`, `reactie_positief`, `no_show`, `pilotvoorstel`

Bij het genereren van een bericht:
1. Sam-prompt wordt opgebouwd met alle lead-context
2. `vraag_eisenhower()` roept de agent aan
3. Bericht wordt opgeslagen via `crm.sla_bericht_op()`
4. `outreach_teller` wordt verhoogd
5. Status gaat automatisch van "nieuw" → "benaderd"

---

### 3. `admin/routes/admin.js` — CRM proxy-routes (uitgebreid)

Hulpfunctie `proxyNaarCrm(req, res, methode, pad, body)` handelt alle CRM-calls af.  
Query-parameters (status, zoek, sector) worden correct doorgestuurd.  
204-responses worden correct afgehandeld (geen JSON-body).

Alle 11 CRM-routes zijn aanwezig + bestaande auth-routes (/login, /check, /logout, /larry) zijn bewaard.

---

### 4. `admin/public/dashboard.html` — Pipeline-tab (nieuw)

Volledig nieuwe tab in de stijl van het bestaande dashboard.

**Stats-balk (5 kaarten):**
- Totaal leads, Benaderd, Afspraken, Gewonnen
- ⚡ Follow-ups nodig (oranje kleur)

**Kanban-bord (6 kolommen):**
- Nieuw / Benaderd / Reactie / Afspraak / Voorstel / Gewonnen
- Oranje stip op lead-card als follow-up nodig is
- Sector-badge + datum zichtbaar op card
- Zoekfilter filtert real-time over alle kolommen

**Modal: Lead toevoegen**
- Velden: organisatie*, sector, locatie, contactpersoon, functie, email, telefoon, website, medewerkers, pijnpunten (komma-gescheiden), notities

**Modal: Lead detail**
- Avatar, organisatienaam, contactpersoon + functie
- Status-dropdown met directe opslaan-knop
- 10 detailvelden (sector, locatie, email, telefoon, website, medewerkers, outreach-teller, datum afspraak/voorstel/actie)
- Pijnpunten als tags
- Notities + gespreksnotities (bewerkbaar)
- Sam-bericht generator (7 types) met resultaatweergave
- Volledige berichtengeschiedenis
- Lead verwijderen (met bevestiging)

**JS-functies:** `laadPipeline()`, `renderKanban()`, `renderPipeStats()`, `openDetailModal()`, `renderBerichten()`, `escHtml()`, `fmtDatum()`

---

## Bestandsstructuur (huidig)

```
Eisenhower/
├── agents/
│   ├── main.py          — CLI + Eisenhower orchestrator
│   ├── prompts.py       — Systeemprompts alle agents (~1900 regels)
│   ├── api.py           — FastAPI backend (chat + CRM)
│   ├── crm.py           — SQLite CRM-module  ← NIEUW
│   ├── requirements.txt
│   └── .env.example
├── admin/
│   ├── server.js        — Express server
│   ├── routes/admin.js  — Auth + Larry + CRM proxy-routes
│   └── public/
│       ├── dashboard.html  — Beheerinterface met Pipeline-tab  ← UITGEBREID
│       └── login.html
└── VOORTGANG.md         — Dit bestand
```

---

## Nog te doen / mogelijke vervolgstappen

- [ ] Drag-and-drop tussen Kanban-kolommen (status verslepen)
- [ ] LinkedIn-URL klikbaar maken in detail-modal
- [ ] Bulk-import van leads via CSV
- [ ] E-mailnotificatie bij follow-up deadline
- [ ] Pilot-tab: leads met status "voorstel" + pilot_inhoud/pilot_prijs invullen
- [ ] Activiteitenlog per lead tonen in detail-modal
- [ ] Exportfunctie (CSV/PDF) van pipeline
- [ ] Filterbalk op sector in Kanban-bord
- [ ] Dashboard-statistieken: grafiek van conversie over tijd

---

## Deployment

```bash
# Agents API (Railway)
cd agents
uvicorn api:app --host 0.0.0.0 --port 8000

# Admin dashboard (Railway, apart)
cd admin
node server.js
```

**Env-variabelen nodig:**
- `ANTHROPIC_API_KEY` — voor agents
- `ADMIN_PASSWORD` — voor dashboard login
- `AGENTS_API_URL` — URL van de agents API (vanuit admin)
- `CRM_DB_PATH` — optioneel, pad naar SQLite database
