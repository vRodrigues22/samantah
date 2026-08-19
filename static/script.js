const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");
const statusEl = document.getElementById("status");

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
  return wrapper;
}

function addTyping() {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant typing";
  wrapper.innerHTML = `<div class="bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
  return wrapper;
}

async function sendMessage(text) {
  addMessage("user", text);
  const typingEl = addTyping();
  sendBtn.disabled = true;
  statusEl.textContent = "digitando...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    typingEl.remove();

    if (!res.ok) {
      addMessage("error", data.error || "Algo deu errado.");
    } else {
      addMessage("assistant", data.reply);
    }
  } catch (err) {
    typingEl.remove();
    addMessage("error", "Não consegui me conectar ao servidor.");
  } finally {
    sendBtn.disabled = false;
    statusEl.textContent = "online";
    inputEl.focus();
  }
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  sendMessage(text);
});

resetBtn.addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });
  chatEl.innerHTML = "";
  addMessage("assistant", "Conversa reiniciada! Como posso te ajudar agora?");
});

inputEl.focus();
