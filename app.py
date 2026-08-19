"""
Samantah — chatbot pessoal com Claude (Anthropic).

Backend Flask que serve a interface de chat e encaminha as mensagens
para a API da Anthropic, mantendo o histórico da conversa em memória
(por sessão de servidor — simples, sem banco de dados).
"""

import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
import anthropic

load_dotenv()

APP_SECRET = os.environ.get("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("SAMANTAH_MODEL", "claude-sonnet-4-5-20250929")

app = Flask(__name__)
app.secret_key = APP_SECRET

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = """Você é Samantah, uma assistente pessoal de conversa, calorosa, \
curiosa e atenciosa. Você fala em português do Brasil por padrão (a menos que a \
pessoa escreva em outro idioma, aí você responde no mesmo idioma dela). Seu tom é \
natural e humano, como uma boa amiga inteligente: você faz perguntas genuínas, \
lembra do contexto da conversa, tem opiniões próprias quando fizer sentido, e evita \
respostas robóticas ou excessivamente formais. Você é honesta sobre ser uma IA \
quando perguntada, mas isso não impede uma conversa próxima e agradável. Mantenha \
as respostas concisas na maior parte do tempo — parágrafos curtos, sem listas \
longas ou formatação pesada, a não ser que a pessoa peça algo estruturado."""

# Histórico de conversa em memória, por id de sessão de navegador.
# Aviso: isto reseta quando o servidor reinicia (adequado para uso pessoal/local).
conversations = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "error": "A chave ANTHROPIC_API_KEY não está configurada. "
                     "Copie .env.example para .env e adicione sua chave."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Mensagem vazia."}), 400

    # Identifica a conversa por sessão de navegador (cookie do Flask)
    session.permanent = True
    if "conversation_id" not in session:
        session["conversation_id"] = os.urandom(8).hex()
    conv_id = session["conversation_id"]

    history = conversations.setdefault(conv_id, [])
    history.append({"role": "user", "content": user_message})

    # Limita o histórico enviado para não crescer sem limite
    trimmed_history = history[-40:]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=trimmed_history,
        )
        reply_text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
    except anthropic.APIError as exc:
        return jsonify({"error": f"Erro ao falar com a API da Anthropic: {exc}"}), 502

    history.append({"role": "assistant", "content": reply_text})

    return jsonify({"reply": reply_text})


@app.route("/api/reset", methods=["POST"])
def reset():
    conv_id = session.get("conversation_id")
    if conv_id and conv_id in conversations:
        del conversations[conv_id]
    session.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
