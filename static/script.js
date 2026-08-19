const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");
const statusEl = document.getElementById("status");
const micBtn = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const profileBtn = document.getElementById("profile-btn");
const profileModal = document.getElementById("profile-modal");
const profileNotes = document.getElementById("profile-notes");
const profileSave = document.getElementById("profile-save");
const profileCancel = document.getElementById("profile-cancel");

// ---------- Preferência de "ler em voz alta" (salva no navegador) ----------
let autoSpeak = localStorage.getItem("samantah_autospeak") === "true";
updateSpeakToggleUI();

speakToggle.addEventListener("click", () => {
  autoSpeak = !autoSpeak;
  localStorage.setItem("samantah_autospeak", String(autoSpeak));
  updateSpeakToggleUI();
  if (!autoSpeak) window.speechSynthesis?.cancel();
});

function updateSpeakToggleUI() {
  speakToggle.setAttribute("aria-pressed", String(autoSpeak));
  speakToggle.textContent = autoSpeak ? "🔊" : "🔇";
  speakToggle.title = autoSpeak
    ? "Leitura em voz alta ativada (clique para desativar)"
    : "Leitura em voz alta desativada (clique para ativar)";
}

function speak(text) {
  if (!autoSpeak || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "pt-BR";
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

// ---------- Reconhecimento de voz (ditar mensagem) ----------
const SpeechRecognitionImpl =
  window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let listening = false;

if (SpeechRecognitionImpl) {
  recognition = new SpeechRecognitionImpl();
  recognition.lang = "pt-BR";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    listening = true;
    micBtn.classList.add("listening");
    statusEl.textContent = "ouvindo...";
  };

  recognition.onend = () => {
    listening = false;
    micBtn.classList.remove("listening");
    statusEl.textContent = "online";
  };

  recognition.onerror = () => {
    listening = false;
    micBtn.classList.remove("listening");
    statusEl.textContent = "online";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    inputEl.value = transcript;
    formEl.requestSubmit();
  };

  micBtn.addEventListener("click", () => {
    if (listening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (err) {
        // já estava iniciando; ignora
      }
    }
  });
} else {
  micBtn.style.display = "none";
}

// ---------- Chat ----------
function addMessage(role, text, { speakIt } = {}) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
  if (speakIt && role === "assistant") speak(text);
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
      addMessage("assistant", data.reply, { speakIt: true });
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

// ---------- Carregar histórico salvo ao abrir a página ----------
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (data.history && data.history.length > 0) {
      chatEl.innerHTML = "";
      for (const msg of data.history) {
        addMessage(msg.role === "user" ? "user" : "assistant", msg.content);
      }
    }
  } catch (err) {
    // se falhar, mantém a mensagem de boas-vindas padrão
  }
}

// ---------- Perfil / memória ----------
async function openProfileModal() {
  profileModal.classList.remove("hidden");
  profileModal.setAttribute("aria-hidden", "false");
  try {
    const res = await fetch("/api/profile");
    const data = await res.json();
    profileNotes.value = data.notes || "";
  } catch (err) {
    profileNotes.value = "";
  }
  profileNotes.focus();
}

function closeProfileModal() {
  profileModal.classList.add("hidden");
  profileModal.setAttribute("aria-hidden", "true");
}

profileBtn.addEventListener("click", openProfileModal);
profileCancel.addEventListener("click", closeProfileModal);
profileModal.addEventListener("click", (e) => {
  if (e.target === profileModal) closeProfileModal();
});

profileSave.addEventListener("click", async () => {
  const notes = profileNotes.value.trim();
  profileSave.disabled = true;
  try {
    await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    });
    closeProfileModal();
  } finally {
    profileSave.disabled = false;
  }
});

// ---------- Inicialização ----------
loadHistory();
inputEl.focus();
