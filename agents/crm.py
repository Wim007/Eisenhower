"""
CRM-module voor SamenOntzorgen — SQLite-gebaseerde pipeline.
Geen extra dependencies: alleen stdlib (sqlite3, json, datetime).
"""

import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.getenv("CRM_DB_PATH", os.path.join(os.path.dirname(__file__), "samenontzorgen_crm.db"))

STAGES = ["nieuw", "contact", "gesprek", "voorstel", "gewonnen", "verloren"]


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                naam        TEXT NOT NULL,
                bedrijf     TEXT,
                functie     TEXT,
                email       TEXT,
                telefoon    TEXT,
                stage       TEXT NOT NULL DEFAULT 'nieuw',
                notities    TEXT,
                aangemaakt  TEXT NOT NULL,
                bijgewerkt  TEXT NOT NULL
            )
        """)


def _now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def get_all_leads() -> list[dict]:
    init_db()
    with _conn() as con:
        rows = con.execute("SELECT * FROM leads ORDER BY bijgewerkt DESC").fetchall()
    return [dict(r) for r in rows]


def get_lead(lead_id: int) -> dict | None:
    init_db()
    with _conn() as con:
        row = con.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


def create_lead(naam: str, bedrijf: str = "", functie: str = "",
                email: str = "", telefoon: str = "", notities: str = "") -> dict:
    init_db()
    now = _now()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO leads (naam, bedrijf, functie, email, telefoon, stage, notities, aangemaakt, bijgewerkt) "
            "VALUES (?, ?, ?, ?, ?, 'nieuw', ?, ?, ?)",
            (naam, bedrijf, functie, email, telefoon, notities, now, now)
        )
        return get_lead(cur.lastrowid)


def update_lead(lead_id: int, **kwargs) -> dict | None:
    init_db()
    allowed = {"naam", "bedrijf", "functie", "email", "telefoon", "stage", "notities"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_lead(lead_id)
    if "stage" in updates and updates["stage"] not in STAGES:
        raise ValueError(f"Ongeldige stage: {updates['stage']}")
    updates["bijgewerkt"] = _now()
    cols = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [lead_id]
    with _conn() as con:
        con.execute(f"UPDATE leads SET {cols} WHERE id = ?", vals)
    return get_lead(lead_id)


def delete_lead(lead_id: int) -> bool:
    init_db()
    with _conn() as con:
        cur = con.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    return cur.rowcount > 0


def pipeline_stats() -> dict:
    init_db()
    with _conn() as con:
        rows = con.execute("SELECT stage, COUNT(*) as n FROM leads GROUP BY stage").fetchall()
    counts = {s: 0 for s in STAGES}
    for r in rows:
        counts[r["stage"]] = r["n"]
    return counts
