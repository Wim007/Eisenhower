"""
Eisenhower taakbeheer — SQLite CRUD module.
Kwadranten: 1=Urgent+Belangrijk, 2=NietUrgent+Belangrijk,
            3=Urgent+NietBelangrijk, 4=NietUrgent+NietBelangrijk
"""

import os
import sqlite3

TASKS_DB_PATH = os.getenv("TASKS_DB_PATH", "tasks.db")


def _conn():
    conn = sqlite3.connect(TASKS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                quadrant    INTEGER NOT NULL CHECK (quadrant IN (1,2,3,4)),
                completed   INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        c.commit()


def _row(r):
    if r is None:
        return None
    d = dict(r)
    d["completed"] = bool(d["completed"])
    return d


def get_all(quadrant: int = None) -> list:
    with _conn() as c:
        if quadrant:
            rows = c.execute(
                "SELECT * FROM tasks WHERE quadrant = ? ORDER BY completed, created_at DESC",
                (quadrant,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM tasks ORDER BY quadrant, completed, created_at DESC"
            ).fetchall()
    return [_row(r) for r in rows]


def create(title: str, quadrant: int) -> dict:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO tasks (title, quadrant) VALUES (?, ?)", (title, quadrant)
        )
        c.commit()
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _row(row)


def get_one(task_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row(row)


def update(task_id: int, **kwargs) -> dict | None:
    allowed = {"title", "quadrant", "completed"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return get_one(task_id)
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [task_id]
    with _conn() as c:
        c.execute(f"UPDATE tasks SET {sets} WHERE id = ?", vals)
        c.commit()
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row(row)


def delete(task_id: int) -> bool:
    with _conn() as c:
        cur = c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        c.commit()
    return cur.rowcount > 0


def stats() -> dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done  = c.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1").fetchone()[0]
        per_q = {}
        for q in range(1, 5):
            per_q[str(q)] = c.execute(
                "SELECT COUNT(*) FROM tasks WHERE quadrant = ?", (q,)
            ).fetchone()[0]
    return {"total": total, "completed": done, "open": total - done, "per_quadrant": per_q}
