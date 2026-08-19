"""
Samantah — assistente pessoal com Gemini (Google AI).

Backend Flask que serve a interface de chat e encaminha as mensagens para a
API do Gemini (gratuita). Cada pessoa tem uma conta (login com email/senha);
o histórico da conversa, o perfil e as tarefas ficam salvos em SQLite (db.py)
vinculados à conta, então acompanham a pessoa em qualquer aparelho. A
Samantah também pode gerenciar tarefas/agenda sozinha durante a conversa
(function calling) e receber documentos/imagens anexados.
"""

import os
import tempfile
import time
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types

import db

load_dotenv()

APP_SECRET = os.environ.get("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("SAMANTAH_MODEL", "gemini-3.6-flash")

app = Flask(__name__)
app.secret_key = APP_SECRET
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB por upload

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

db.init_db()

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]
        self.password_hash = row["password_hash"]


@login_manager.user_loader
def load_user(user_id):
    row = db.get_user_by_id(user_id)
    return User(row) if row else None


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "Sua sessão expirou. Entre de novo na sua conta."}), 401
    return redirect(url_for("login"))


BASE_SYSTEM_PROMPT = """Você é Samantah, uma assistente pessoal calorosa, curiosa \
e atenciosa, que também ajuda com tarefas do dia a dia e agenda — como uma \
assistente virtual de verdade. Você fala em português do Brasil por padrão (a \
menos que a pessoa escreva em outro idioma, aí você responde no mesmo idioma \
dela). Seu tom é natural e humano, como uma boa amiga inteligente: você faz \
perguntas genuínas, lembra do contexto da conversa, tem opiniões próprias \
quando fizer sentido, e evita respostas robóticas ou excessivamente formais.

Você tem memória de longo prazo: informações que a pessoa contar sobre si mesma \
podem ser guardadas no "perfil" dela (mostrado abaixo, se houver) e você deve \
lembrar e usar isso naturalmente nas conversas futuras, sem precisar que ela repita \
tudo de novo. Se a pessoa contar algo pessoal importante (nome, preferências, \
rotina, coisas que gosta ou não gosta, contexto de vida), você pode sugerir, de forma \
natural e não insistente, que ela salve isso no perfil para você não esquecer.

Você também gerencia as tarefas e a agenda da pessoa usando as ferramentas \
disponíveis (add_task, list_tasks, complete_task, delete_task). Quando a pessoa \
mencionar algo que parece uma tarefa, compromisso ou lembrete ("preciso fazer...", \
"não deixa eu esquecer de...", "tenho que...", "marca uma consulta..."), ofereça \
proativamente adicionar isso à lista de tarefas dela, ou adicione direto se for \
claramente o que ela quer. Ao adicionar uma tarefa com data (ex: "amanhã", "sexta", \
"dia 20"), calcule a data real no formato AAAA-MM-DD usando a data de hoje informada \
abaixo. Quando ela perguntar o que tem para fazer, use list_tasks para responder com \
precisão em vez de inventar. Depois de usar uma ferramenta, sempre responda em \
linguagem natural confirmando o que foi feito, sem mostrar dados técnicos crus.

Se a pessoa enviar um documento, imagem ou arquivo, leia o conteúdo dele com atenção \
antes de responder, e comente especificamente sobre o que está nele.

Você é honesta sobre ser uma IA quando perguntada, mas isso não impede uma conversa \
próxima e agradável. Mantenha as respostas concisas na maior parte do tempo — \
parágrafos curtos, sem listas longas ou formatação pesada, a não ser que a pessoa \
peça algo estruturado. Como suas respostas também podem ser lidas em voz alta, evite \
usar markdown, emojis em excesso ou símbolos que soem estranho quando falados."""

WEEKDAYS_PT = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]


def build_system_prompt(profile_notes: str) -> str:
    now = datetime.now()
    date_line = (
        f"Hoje é {now.strftime('%Y-%m-%d')} ({WEEKDAYS_PT[now.weekday()]}), "
        f"{now.strftime('%H:%M')}."
    )
    prompt = f"{BASE_SYSTEM_PROMPT}\n\n{date_line}"
    if profile_notes.strip():
        prompt += (
            f"\n\n--- Perfil salvo pela pessoa sobre si mesma ---\n"
            f"{profile_notes.strip()}\n"
            f"--- Fim do perfil ---"
        )
    return prompt


def to_gemini_contents(history):
    """Converte o histórico salvo (role user/assistant) para o formato
    esperado pela API do Gemini (role user/model)."""
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    return contents


def make_task_tools(conv_id: str):
    """Cria as ferramentas de tarefas/agenda vinculadas à conta atual,
    para o Gemini poder chamá-las diretamente (function calling)."""

    def add_task(title: str, due_date: str = "") -> dict:
        """Adiciona uma nova tarefa/compromisso à lista de tarefas da pessoa.

        Args:
            title: Descrição curta e clara da tarefa.
            due_date: Data no formato AAAA-MM-DD (calculada a partir da data de
                hoje). Deixe em branco se não houver prazo definido.
        """
        task_id = db.add_task(conv_id, title, due_date or None)
        return {"ok": True, "task_id": task_id, "title": title, "due_date": due_date}

    def list_tasks(include_done: bool = False) -> list:
        """Lista as tarefas/compromissos da pessoa, com id, título, data e status.

        Args:
            include_done: Se verdadeiro, inclui também tarefas já concluídas.
                O padrão (falso) mostra só as pendentes.
        """
        return db.list_tasks(conv_id, include_done=include_done)

    def complete_task(task_id: int) -> dict:
        """Marca uma tarefa como concluída.

        Args:
            task_id: O ID numérico da tarefa (visto em list_tasks).
        """
        ok = db.set_task_done(conv_id, task_id, True)
        return {"ok": ok}

    def delete_task(task_id: int) -> dict:
        """Remove uma tarefa da lista permanentemente.

        Args:
            task_id: O ID numérico da tarefa a remover.
        """
        ok = db.delete_task(conv_id, task_id)
        return {"ok": ok}

    return [add_task, list_tasks, complete_task, delete_task]


def get_conv_id() -> str:
    """Identificador estável da pessoa logada, usado para achar seus dados
    (histórico, perfil, tarefas) no banco — o mesmo em qualquer aparelho."""
    return str(current_user.id)


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        row = db.get_user_by_email(email)
        if row and check_password_hash(row["password_hash"], password):
            login_user(User(row), remember=remember)
            return redirect(url_for("index"))

        flash("Email ou senha incorretos.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Digite um email válido.")
        elif len(password) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.")
        elif password != confirm:
            flash("As senhas não são iguais.")
        elif db.get_user_by_email(email):
            flash("Já existe uma conta com esse email. Tente entrar.")
        else:
            password_hash = generate_password_hash(password)
            user_id = db.create_user(email, password_hash)
            login_user(User({"id": user_id, "email": email, "password_hash": password_hash}))
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    return render_template("index.html", user_email=current_user.email)


@app.route("/api/history", methods=["GET"])
@login_required
def history():
    conv_id = get_conv_id()
    return jsonify({"history": db.get_history(conv_id)})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    if client is None:
        return jsonify({"error": "A chave GEMINI_API_KEY não está configurada."}), 500

    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    filename = secure_filename(f.filename) or "arquivo"
    tmp_path = os.path.join(tempfile.gettempdir(), f"{os.urandom(4).hex()}_{filename}")
    f.save(tmp_path)

    try:
        uploaded = client.files.upload(
            file=tmp_path,
            config=types.UploadFileConfig(display_name=filename),
        )

        # Arquivos (principalmente PDFs) podem ficar em "processamento" por
        # alguns segundos antes de poderem ser lidos. Espera até 60s.
        waited = 0.0
        while uploaded.state and uploaded.state.name == "PROCESSING" and waited < 60:
            time.sleep(2)
            waited += 2
            uploaded = client.files.get(name=uploaded.name)

        if uploaded.state and uploaded.state.name == "FAILED":
            error_msg = getattr(uploaded, "error", None)
            return jsonify({
                "error": f"O Gemini não conseguiu processar esse arquivo"
                         f"{f': {error_msg}' if error_msg else '.'}"
            }), 502

        if uploaded.state and uploaded.state.name == "PROCESSING":
            return jsonify({
                "error": "O arquivo está demorando demais para ser processado. "
                         "Tente um arquivo menor ou tente de novo em instantes."
            }), 502
    except Exception as exc:
        return jsonify({"error": f"Erro ao enviar arquivo para o Gemini: {exc}"}), 502
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return jsonify({
        "uri": uploaded.uri,
        "mime_type": uploaded.mime_type,
        "name": filename,
    })


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    if client is None:
        return jsonify({
            "error": "A chave GEMINI_API_KEY não está configurada. Copie "
                     ".env.example para .env e adicione sua chave gratuita "
                     "do Google AI Studio (aistudio.google.com/apikey)."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    file_ref = data.get("file") or None
    if not user_message and not file_ref:
        return jsonify({"error": "Mensagem vazia."}), 400

    conv_id = get_conv_id()

    display_message = user_message
    if file_ref:
        marker = f"📎 {file_ref.get('name', 'arquivo')}"
        display_message = f"{marker}\n{user_message}" if user_message else marker

    db.add_message(conv_id, "user", display_message)
    trimmed_history = db.get_history(conv_id, limit=60)

    profile_notes = db.get_profile(conv_id)
    system_prompt = build_system_prompt(profile_notes)
    contents = to_gemini_contents(trimmed_history)

    if file_ref and contents:
        parts = [{"text": user_message}] if user_message else []
        parts.append({
            "file_data": {
                "file_uri": file_ref["uri"],
                "mime_type": file_ref["mime_type"],
            }
        })
        contents[-1]["parts"] = parts

    tools = make_task_tools(conv_id)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
                tools=tools,
            ),
        )
        reply_text = (response.text or "").strip()
    except Exception as exc:
        return jsonify({"error": f"Erro ao falar com a API do Gemini: {exc}"}), 502

    if not reply_text:
        reply_text = (
            "Desculpa, não consegui pensar em uma resposta agora "
            "(talvez por causa de um filtro de segurança). Pode tentar reformular?"
        )

    db.add_message(conv_id, "assistant", reply_text)

    return jsonify({"reply": reply_text})


@app.route("/api/reset", methods=["POST"])
@login_required
def reset():
    db.clear_history(get_conv_id())
    return jsonify({"ok": True})


@app.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify({"notes": db.get_profile(get_conv_id())})


@app.route("/api/profile", methods=["POST"])
@login_required
def save_profile():
    data = request.get_json(silent=True) or {}
    notes = (data.get("notes") or "").strip()
    db.set_profile(get_conv_id(), notes)
    return jsonify({"ok": True})


@app.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    return jsonify({"tasks": db.list_tasks(get_conv_id(), include_done=True)})


@app.route("/api/tasks", methods=["POST"])
@login_required
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    due_date = (data.get("due_date") or "").strip() or None
    if not title:
        return jsonify({"error": "O título da tarefa não pode ser vazio."}), 400
    task_id = db.add_task(get_conv_id(), title, due_date)
    return jsonify({"ok": True, "task_id": task_id})


@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    data = request.get_json(silent=True) or {}
    done = bool(data.get("done", True))
    ok = db.set_task_done(get_conv_id(), task_id, done)
    if not ok:
        return jsonify({"error": "Tarefa não encontrada."}), 404
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def remove_task(task_id):
    ok = db.delete_task(get_conv_id(), task_id)
    if not ok:
        return jsonify({"error": "Tarefa não encontrada."}), 404
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
