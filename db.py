"""
Camada de banco de dados da Samantah — SQLite.

Guarda as contas de usuário, o histórico de mensagens, o "perfil" (notas que
a pessoa escreve sobre si mesma) e as tarefas, tudo vinculado à conta da
pessoa (não mais ao navegador) — assim ela pode entrar de qualquer aparelho
e encontrar tudo como deixou.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id)"
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


# ---------------------------------------------------------------------------
# Tarefas / agenda
# ---------------------------------------------------------------------------

def add_task(session_id: str, title: str, due_date: Optional[str] = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (session_id, title, due_date) VALUES (?, ?, ?)",
            (session_id, title.strip(), (due_date or "").strip() or None),
        )
        return cur.lastrowid


def list_tasks(session_id: str, include_done: bool = True):
    query = "SELECT id, title, due_date, done FROM tasks WHERE session_id = ?"
    params = [session_id]
    if not include_done:
        query += " AND done = 0"
    query += " ORDER BY (due_date IS NULL), due_date ASC, id ASC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "due_date": r["due_date"],
            "done": bool(r["done"]),
        }
        for r in rows
    ]


def set_task_done(session_id: str, task_id: int, done: bool) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE tasks SET done = ? WHERE id = ? AND session_id = ?",
            (1 if done else 0, task_id, session_id),
        )
        return cur.rowcount > 0


def delete_task(session_id: str, task_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND session_id = ?",
            (task_id, session_id),
        )
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Contas de usuário
# ---------------------------------------------------------------------------

def create_user(email: str, password_hash: str) -> int:
    """Cria uma conta nova. Lança sqlite3.IntegrityError se o email já existir."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.strip().lower(), password_hash),
        )
        return cur.lastrowid


def get_user_by_email(email: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None
