"""
Camada de banco de dados da Samantah.

Guarda as contas de usuário, o histórico de mensagens, o "perfil" (notas que
a pessoa escreve sobre si mesma) e as tarefas, tudo vinculado à conta da
pessoa (não mais ao navegador) — assim ela pode entrar de qualquer aparelho
e encontrar tudo como deixou.

Funciona em dois modos:

- **Turso** (recomendado em produção): se as variáveis de ambiente
  ``TURSO_DATABASE_URL`` e ``TURSO_AUTH_TOKEN`` estiverem configuradas, os
  dados ficam guardados num banco SQLite hospedado no Turso (serviço
  gratuito, fora do disco do servidor). Isso é o que garante que login e
  memória sobrevivam a deploys e aos períodos em que o servidor "dorme" por
  inatividade em hospedagens gratuitas como o Render.
- **SQLite local** (padrão, útil para rodar no seu computador): se as
  variáveis do Turso não estiverem definidas, usa um arquivo
  ``samantah.db`` local, como antes.
"""

import os
import concurrent.futures
from typing import Optional

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()

USE_TURSO = bool(TURSO_URL)

if USE_TURSO:
    import libsql_client
else:
    import sqlite3

    DB_PATH = os.environ.get(
        "SAMANTAH_DB_PATH", os.path.join(os.path.dirname(__file__), "samantah.db")
    )


class IntegrityError(Exception):
    """Erro de violação de restrição do banco (ex: email duplicado)."""


class DatabaseError(Exception):
    """Erro ao falar com o banco de dados (ex: timeout ou queda de conexão)."""


# O Turso costuma fornecer a URL no formato "libsql://...", que usa uma
# conexão via WebSocket. Usamos HTTP puro aqui (uma requisição por comando).
_TURSO_HTTP_URL = TURSO_URL.replace("libsql://", "https://", 1) if TURSO_URL else ""

# Tempo máximo de espera por uma resposta do Turso. Isso é essencial: sem um
# limite, uma conexão "travada" (ex: uma conexão HTTP reaproveitada que
# ficou inativa por um tempo e morreu silenciosamente no meio do caminho)
# ficaria esperando para sempre — e como o servidor roda com apenas um
# worker, isso trava o site inteiro até o gunicorn matar o processo à força
# (o que já aconteceu). Com o limite, qualquer travamento vira um erro
# rápido e claro em vez de deixar o site inacessível por minutos.
_TURSO_TIMEOUT_SECONDS = 20
_turso_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="turso"
)


def _turso_call(sql: str, params):
    # Abre uma conexão nova a cada chamada e fecha em seguida, em vez de
    # reaproveitar uma conexão de longa duração — evita justamente o tipo de
    # conexão "morta" que causou o travamento acima.
    turso_client = libsql_client.create_client_sync(
        url=_TURSO_HTTP_URL, auth_token=TURSO_AUTH_TOKEN
    )
    try:
        return turso_client.execute(sql, params)
    finally:
        try:
            turso_client.close()
        except Exception:
            pass


def _turso_execute(sql: str, params):
    try:
        future = _turso_pool.submit(_turso_call, sql, params)
        return future.result(timeout=_TURSO_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        raise DatabaseError(
            "O banco de dados demorou demais para responder. Tente de novo "
            "em instantes."
        )
    except libsql_client.LibsqlError as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise IntegrityError(str(exc)) from exc
        raise DatabaseError(str(exc)) from exc
    except IntegrityError:
        raise
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


def _execute(sql: str, params=None):
    """Executa um comando de escrita (INSERT/UPDATE/DELETE/CREATE/INDEX).

    Retorna (lastrowid, rowcount).
    """
    params = tuple(params) if params else ()
    if USE_TURSO:
        rs = _turso_execute(sql, params)
        return rs.last_insert_rowid, rs.rows_affected
    else:
        conn = sqlite3.connect(DB_PATH)
        try:
            try:
                cur = conn.execute(sql, params)
            except sqlite3.IntegrityError as exc:
                raise IntegrityError(str(exc)) from exc
            conn.commit()
            return cur.lastrowid, cur.rowcount
        finally:
            conn.close()


def _query(sql: str, params=None):
    """Executa um SELECT. Retorna uma lista de dicts (uma por linha)."""
    params = tuple(params) if params else ()
    if USE_TURSO:
        rs = _turso_execute(sql, params)
        return [row.asdict() for row in rs.rows]
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def _query_one(sql: str, params=None):
    rows = _query(sql, params)
    return rows[0] if rows else None


def init_db():
    _execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    _execute(
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
    _execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    _execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            session_id TEXT PRIMARY KEY,
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    _execute(
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
    _execute("CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id)")


def add_message(session_id: str, role: str, content: str):
    _execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )


def get_history(session_id: str, limit: int = 60):
    rows = _query(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    )
    trimmed = rows[-limit:]
    return [{"role": r["role"], "content": r["content"]} for r in trimmed]


def clear_history(session_id: str):
    _execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


def get_profile(session_id: str) -> str:
    row = _query_one("SELECT notes FROM profiles WHERE session_id = ?", (session_id,))
    return row["notes"] if row else ""


def set_profile(session_id: str, notes: str):
    _execute(
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
    lastrowid, _ = _execute(
        "INSERT INTO tasks (session_id, title, due_date) VALUES (?, ?, ?)",
        (session_id, title.strip(), (due_date or "").strip() or None),
    )
    return lastrowid


def list_tasks(session_id: str, include_done: bool = True):
    query = "SELECT id, title, due_date, done FROM tasks WHERE session_id = ?"
    params = [session_id]
    if not include_done:
        query += " AND done = 0"
    query += " ORDER BY (due_date IS NULL), due_date ASC, id ASC"
    rows = _query(query, params)
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
    _, rowcount = _execute(
        "UPDATE tasks SET done = ? WHERE id = ? AND session_id = ?",
        (1 if done else 0, task_id, session_id),
    )
    return rowcount > 0


def delete_task(session_id: str, task_id: int) -> bool:
    _, rowcount = _execute(
        "DELETE FROM tasks WHERE id = ? AND session_id = ?",
        (task_id, session_id),
    )
    return rowcount > 0


# ---------------------------------------------------------------------------
# Contas de usuário
# ---------------------------------------------------------------------------

def create_user(email: str, password_hash: str) -> int:
    """Cria uma conta nova. Lança IntegrityError se o email já existir."""
    lastrowid, _ = _execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email.strip().lower(), password_hash),
    )
    return lastrowid


def get_user_by_email(email: str):
    return _query_one(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (email.strip().lower(),),
    )


def get_user_by_id(user_id):
    return _query_one(
        "SELECT id, email, password_hash FROM users WHERE id = ?",
        (user_id,),
    )
