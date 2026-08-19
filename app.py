"""
Samantah — chatbot pessoal com Gemini (Google AI).

Backend Flask que serve a interface de chat e encaminha as mensagens para a
API do Gemini (gratuita). O histórico da conversa e o perfil da pessoa ficam
salvos em SQLite (db.py), então sobrevivem a reinícios do servidor.
"""

import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from google import genai
from google.genai import types

import db

load_dotenv()

APP_SECRET = os.environ.get("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("SAMANTAH_MODEL", "gemini-2.5-flash")

app = Flask(__name__)
app.secret_key = APP_SECRET

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

db.init_db()

BASE_SYSTEM_PROMPT = """Você é Samantah, uma assistente pessoal de conversa, calorosa, \
curiosa e atenciosa. Você fala em português do Brasil por padrão (a menos que a \
pessoa escreva em outro idioma, aí você responde no mesmo idioma dela). Seu tom é \
natural e humano, como uma boa amiga inteligente: você faz perguntas genuínas, \
lembra do contexto da conversa, tem opiniões próprias quando fizer sentido, e evita \
respostas robóticas ou excessivamente formais.

Você tem memória de longo prazo: informações que a pessoa contar sobre si mesma \
podem ser guardadas no "perfil" dela (mostrado abaixo, se houver) e você deve \
lembrar e usar isso naturalmente nas conversas futuras, sem precisar que ela repita \
tudo de novo. Se a pessoa contar algo pessoal importante (nome, preferências, \
rotina, coisas que gosta ou não gosta, contexto de vida), você pode sugerir, de forma \
natural e não insistente, que ela salve isso no perfil para você não esquecer.

Você é honesta sobre ser uma IA quando perguntada, mas isso não impede uma conversa \
próxima e agradável. Mantenha as respostas concisas na maior parte do tempo — \
parágrafos curtos, sem listas longas ou formatação pesada, a não ser que a pessoa \
peça algo estruturado. Como suas respostas também podem ser lidas em voz alta, evite \
usar markdown, emojis em excesso ou símbolos que soem estranho quando falados."""


def build_system_prompt(profile_notes: str) -> str:
    if not profile_notes.strip():
        return BASE_SYSTEM_PROMPT
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"--- Perfil salvo pela pessoa sobre si mesma ---\n"
        f"{profile_notes.strip()}\n"
        f"--- Fim do perfil ---"
    )


def to_gemini_contents(history):
    """Converte o histórico salvo (role user/assistant) para o formato
    esperado pela API do Gemini (role user/model)."""
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    return contents


def get_conversation_id() -> str:
    session.permanent = True
    if "conversation_id" not in session:
        session["conversation_id"] = os.urandom(8).hex()
    return session["conversation_id"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/history", methods=["GET"])
def history():
    conv_id = get_conversation_id()
    return jsonify({"history": db.get_history(conv_id)})


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "error": "A chave GEMINI_API_KEY não está configurada. Copie "
                     ".env.example para .env e adicione sua chave gratuita "
                     "do Google AI Studio (aistudio.google.com/apikey)."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Mensagem vazia."}), 400

    conv_id = get_conversation_id()

    db.add_message(conv_id, "user", user_message)
    trimmed_history = db.get_history(conv_id, limit=60)

    profile_notes = db.get_profile(conv_id)
    system_prompt = build_system_prompt(profile_notes)
    contents = to_gemini_contents(trimmed_history)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
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
def reset():
    conv_id = session.get("conversation_id")
    if conv_id:
        db.clear_history(conv_id)
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/profile", methods=["GET"])
def get_profile():
    conv_id = get_conversation_id()
    return jsonify({"notes": db.get_profile(conv_id)})


@app.route("/api/profile", methods=["POST"])
def save_profile():
    conv_id = get_conversation_id()
    data = request.get_json(silent=True) or {}
    notes = (data.get("notes") or "").strip()
    db.set_profile(conv_id, notes)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
