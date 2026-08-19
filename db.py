"""
Camada de banco de dados da Samantah — SQLite.

Guarda o histórico de mensagens e o "perfil" (notas que a pessoa escreve
sobre si mesma) por sessão de navegador, para que a conversa e o que a
Samantah sabe sobre você sobrevivam a reinícios do servidor.
"""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get(
    "SAMANTAH_DB_PATH", os.path.join(os.path.dirname(__file__), "samantah.db")
)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                session_id TEXT PRIMARY KEY,
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )


def add_message(session_id: str, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_history(session_id: str, limit: int = 60):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    trimmed = rows[-limit:]
    return [{"role": r["role"], "content": r["content"]} for r in trimmed]


def clear_history(session_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


def get_profile(session_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT notes FROM profiles WHERE session_id = ?", (session_id,)
        ).fetchone()
    return row["notes"] if row else ""


def set_profile(session_id: str, notes: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO profiles (session_id, notes) VALUES (?, ?)
            ON CONFLICT(session_id) DO UPDATE SET notes = excluded.notes
            """,
            (session_id, notes),
        )
