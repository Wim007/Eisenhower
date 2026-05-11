"""
CRM-module voor SamenOntzorgen — SQLite-gebaseerde pipeline.
Geen extra dependencies: alleen stdlib (sqlite3, json, datetime).
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = os.getenv("CRM_DB_PATH", os.path.join(os.path.dirname(__file__), "samenontzorgen_crm.db"))

FOLLOWUP_DAGEN = [3, 7, 14]

STATUSSEN = {"nieuw", "benaderd", "reactie", "afspraak", "voorstel", "gewonnen", "verloren", "geparkeerd"}


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                organisatie         TEXT NOT NULL,
                sector              TEXT,
                locatie             TEXT,
                website             TEXT,
                contactpersoon      TEXT,
                functie             TEXT,
                email               TEXT,
                telefoon            TEXT,
                linkedin_url        TEXT,
                medewerkers         INTEGER,
                pijnpunten          TEXT DEFAULT '[]',
                notities            TEXT,
                status              TEXT NOT NULL DEFAULT 'nieuw',
                datum_toegevoegd    TEXT NOT NULL,
                datum_benaderd      TEXT,
                datum_laatste_actie TEXT NOT NULL,
                datum_afspraak      TEXT,
                datum_voorstel      TEXT,
                datum_close         TEXT,
                outreach_teller     INTEGER NOT NULL DEFAULT 0,
                laatste_bericht     TEXT,
                bezwaren            TEXT DEFAULT '[]',
                gespreksnotities    TEXT,
                pilot_inhoud        TEXT,
                pilot_prijs         REAL,
                extra_data          TEXT DEFAULT '{}'
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS activiteiten (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id     INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                type        TEXT NOT NULL,
                omschrijving TEXT,
                datum       TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS berichten (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id     INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                type        TEXT NOT NULL,
                inhoud      TEXT NOT NULL,
                datum       TEXT NOT NULL
            )
        """)


def _now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def _parse_json(val, default):
    if val is None:
        return default
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return default


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["pijnpunten"] = _parse_json(d.get("pijnpunten"), [])
    d["bezwaren"]   = _parse_json(d.get("bezwaren"), [])
    d["extra_data"] = _parse_json(d.get("extra_data"), {})
    return d


def voeg_lead_toe(
    organisatie: str,
    sector: str = "",
    locatie: str = "",
    website: str = "",
    contactpersoon: str = "",
    functie: str = "",
    email: str = "",
    telefoon: str = "",
    linkedin_url: str = "",
    medewerkers: int | None = None,
    pijnpunten: list | None = None,
    notities: str = "",
) -> dict:
    init_db()
    now = _now()
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO leads
               (organisatie, sector, locatie, website, contactpersoon, functie,
                email, telefoon, linkedin_url, medewerkers, pijnpunten, notities,
                status, datum_toegevoegd, datum_laatste_actie)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'nieuw',?,?)""",
            (
                organisatie, sector or "", locatie or "", website or "",
                contactpersoon or "", functie or "", email or "", telefoon or "",
                linkedin_url or "", medewerkers,
                json.dumps(pijnpunten or []), notities or "", now, now,
            ),
        )
        return haal_lead_op(cur.lastrowid)


def update_status(lead_id: int, nieuwe_status: str) -> dict | None:
    if nieuwe_status not in STATUSSEN:
        raise ValueError(f"Ongeldige status: {nieuwe_status}")
    init_db()
    now = _now()
    datum_veld = {
        "benaderd": "datum_benaderd",
        "afspraak":  "datum_afspraak",
        "voorstel":  "datum_voorstel",
        "gewonnen":  "datum_close",
        "verloren":  "datum_close",
    }.get(nieuwe_status)
    extra = f", {datum_veld} = ?" if datum_veld else ""
    params = [nieuwe_status, now]
    if datum_veld:
        params.append(now)
    params.append(lead_id)
    with _conn() as con:
        con.execute(
            f"UPDATE leads SET status = ?, datum_laatste_actie = ?{extra} WHERE id = ?",
            params,
        )
    return haal_lead_op(lead_id)


def update_lead(lead_id: int, **kwargs) -> dict | None:
    init_db()
    allowed = {
        "organisatie", "sector", "locatie", "website", "contactpersoon", "functie",
        "email", "telefoon", "linkedin_url", "medewerkers", "pijnpunten", "notities",
        "bezwaren", "gespreksnotities", "pilot_inhoud", "pilot_prijs", "extra_data",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return haal_lead_op(lead_id)
    for json_veld in ("pijnpunten", "bezwaren", "extra_data"):
        if json_veld in updates and isinstance(updates[json_veld], (list, dict)):
            updates[json_veld] = json.dumps(updates[json_veld])
    updates["datum_laatste_actie"] = _now()
    cols = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [lead_id]
    with _conn() as con:
        con.execute(f"UPDATE leads SET {cols} WHERE id = ?", vals)
    return haal_lead_op(lead_id)


def verwijder_lead(lead_id: int) -> bool:
    init_db()
    with _conn() as con:
        cur = con.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    return cur.rowcount > 0


def haal_lead_op(lead_id: int) -> dict | None:
    init_db()
    with _conn() as con:
        row = con.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return _row_to_dict(row) if row else None


def zoek_leads(status: str = "", sector: str = "", zoekterm: str = "") -> list[dict]:
    init_db()
    sql = "SELECT * FROM leads WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if sector:
        sql += " AND sector = ?"
        params.append(sector)
    if zoekterm:
        sql += " AND (organisatie LIKE ? OR contactpersoon LIKE ? OR email LIKE ?)"
        like = f"%{zoekterm}%"
        params.extend([like, like, like])
    sql += " ORDER BY datum_laatste_actie DESC"
    with _conn() as con:
        rows = con.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def alle_leads_per_status() -> dict[str, list[dict]]:
    init_db()
    pipeline_statussen = ["nieuw", "benaderd", "reactie", "afspraak", "voorstel", "gewonnen"]
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM leads WHERE status != 'geparkeerd' ORDER BY datum_laatste_actie DESC"
        ).fetchall()
    result: dict[str, list[dict]] = {s: [] for s in pipeline_statussen}
    result["verloren"] = []
    for r in rows:
        d = _row_to_dict(r)
        bucket = d["status"] if d["status"] in result else "verloren"
        result[bucket].append(d)
    return result


def leads_voor_followup() -> list[dict]:
    init_db()
    actief = {"benaderd", "reactie", "afspraak"}
    now = datetime.utcnow()
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM leads WHERE status IN ('benaderd','reactie','afspraak') "
            "ORDER BY datum_laatste_actie ASC"
        ).fetchall()
    resultaat = []
    for r in rows:
        lead = _row_to_dict(r)
        teller = lead["outreach_teller"]
        drempel = FOLLOWUP_DAGEN[min(teller, len(FOLLOWUP_DAGEN) - 1)]
        if lead["datum_laatste_actie"]:
            laatste = datetime.fromisoformat(lead["datum_laatste_actie"])
            if (now - laatste).days >= drempel:
                lead["followup_over_dagen"] = 0
                lead["dagen_inactief"] = (now - laatste).days
                resultaat.append(lead)
    return resultaat


def verhoog_outreach_teller(lead_id: int, laatste_bericht: str = "") -> dict | None:
    init_db()
    now = _now()
    with _conn() as con:
        con.execute(
            "UPDATE leads SET outreach_teller = outreach_teller + 1, "
            "datum_laatste_actie = ?, laatste_bericht = ? WHERE id = ?",
            (now, laatste_bericht[:200] if laatste_bericht else "", lead_id),
        )
    return haal_lead_op(lead_id)


def sla_bericht_op(lead_id: int, type_bericht: str, inhoud: str) -> dict:
    init_db()
    now = _now()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO berichten (lead_id, type, inhoud, datum) VALUES (?,?,?,?)",
            (lead_id, type_bericht, inhoud, now),
        )
        row = con.execute("SELECT * FROM berichten WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def haal_berichten_op(lead_id: int) -> list[dict]:
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM berichten WHERE lead_id = ? ORDER BY datum DESC", (lead_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def statistieken() -> dict:
    init_db()
    with _conn() as con:
        totaal = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        per_status_rows = con.execute(
            "SELECT status, COUNT(*) as n FROM leads GROUP BY status"
        ).fetchall()
    per_status = {s: 0 for s in STATUSSEN}
    for r in per_status_rows:
        per_status[r["status"]] = r["n"]
    gewonnen = per_status.get("gewonnen", 0)
    benaderd = sum(per_status.get(s, 0) for s in ("benaderd", "reactie", "afspraak", "voorstel", "gewonnen", "verloren"))
    conversie_pct = round((gewonnen / benaderd * 100) if benaderd else 0, 1)
    followups_nodig = len(leads_voor_followup())
    return {
        "totaal": totaal,
        "per_status": per_status,
        "conversie_pct": conversie_pct,
        "followups_nodig": followups_nodig,
    }
