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
const attachBtn = document.getElementById("attach-btn");
const fileInput = document.getElementById("file-input");
const fileChip = document.getElementById("file-chip");
const fileChipName = document.getElementById("file-chip-name");
const fileChipRemove = document.getElementById("file-chip-remove");
const tasksBtn = document.getElementById("tasks-btn");
const tasksModal = document.getElementById("tasks-modal");
const tasksClose = document.getElementById("tasks-close");
const taskForm = document.getElementById("task-form");
const taskTitleInput = document.getElementById("task-title");
const taskDateInput = document.getElementById("task-date");
const taskListEl = document.getElementById("task-list");

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

// ---------- Anexar documentos / imagens ----------
let pendingFile = null; // { uri, mime_type, name }

attachBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  fileInput.value = "";
  if (!file) return;

  statusEl.textContent = "enviando arquivo...";
  attachBtn.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) {
      addMessage("error", data.error || "Não consegui enviar o arquivo.");
      return;
    }
    pendingFile = { uri: data.uri, mime_type: data.mime_type, name: data.name };
    fileChipName.textContent = data.name;
    fileChip.classList.remove("hidden");
  } catch (err) {
    addMessage("error", "Não consegui enviar o arquivo.");
  } finally {
    statusEl.textContent = "online";
    attachBtn.disabled = false;
  }
});

fileChipRemove.addEventListener("click", () => {
  pendingFile = null;
  fileChip.classList.add("hidden");
});

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

async function sendMessage(text, file) {
  const displayText = file ? `📎 ${file.name}${text ? "\n" + text : ""}` : text;
  addMessage("user", displayText);
  const typingEl = addTyping();
  sendBtn.disabled = true;
  statusEl.textContent = "digitando...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, file: file || undefined }),
    });
    const data = await res.json();
    typingEl.remove();

    if (!res.ok) {
      addMessage("error", data.error || "Algo deu errado.");
    } else {
      addMessage("assistant", data.reply, { speakIt: true });
      if (!tasksModal.classList.contains("hidden")) loadTasks();
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
  if (!text && !pendingFile) return;
  inputEl.value = "";
  const file = pendingFile;
  pendingFile = null;
  fileChip.classList.add("hidden");
  sendMessage(text, file);
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

// ---------- Tarefas / agenda ----------
function formatTaskDate(isoDate) {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

function renderTasks(tasks) {
  taskListEl.innerHTML = "";
  if (!tasks || tasks.length === 0) {
    taskListEl.innerHTML = '<li class="task-empty">Nenhuma tarefa por aqui ainda.</li>';
    return;
  }
  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = `task-item${task.done ? " done" : ""}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = task.done;
    checkbox.addEventListener("change", () => toggleTask(task.id, checkbox.checked));

    const info = document.createElement("div");
    info.className = "task-info";
    const titleEl = document.createElement("span");
    titleEl.className = "task-title";
    titleEl.textContent = task.title;
    info.appendChild(titleEl);
    if (task.due_date) {
      const dateEl = document.createElement("span");
      dateEl.className = "task-date";
      dateEl.textContent = formatTaskDate(task.due_date);
      info.appendChild(dateEl);
    }

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "task-delete";
    deleteBtn.textContent = "✕";
    deleteBtn.title = "Remover tarefa";
    deleteBtn.addEventListener("click", () => deleteTask(task.id));

    li.appendChild(checkbox);
    li.appendChild(info);
    li.appendChild(deleteBtn);
    taskListEl.appendChild(li);
  }
}

async function loadTasks() {
  try {
    const res = await fetch("/api/tasks");
    const data = await res.json();
    renderTasks(data.tasks || []);
  } catch (err) {
    taskListEl.innerHTML = '<li class="task-empty">Não consegui carregar as tarefas.</li>';
  }
}

async function toggleTask(id, done) {
  await fetch(`/api/tasks/${id}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ done }),
  });
  loadTasks();
}

async function deleteTask(id) {
  await fetch(`/api/tasks/${id}`, { method: "DELETE" });
  loadTasks();
}

function openTasksModal() {
  tasksModal.classList.remove("hidden");
  tasksModal.setAttribute("aria-hidden", "false");
  loadTasks();
}

function closeTasksModal() {
  tasksModal.classList.add("hidden");
  tasksModal.setAttribute("aria-hidden", "true");
}

tasksBtn.addEventListener("click", openTasksModal);
tasksClose.addEventListener("click", closeTasksModal);
tasksModal.addEventListener("click", (e) => {
  if (e.target === tasksModal) closeTasksModal();
});

taskForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = taskTitleInput.value.trim();
  if (!title) return;
  const due_date = taskDateInput.value || "";
  await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, due_date }),
  });
  taskTitleInput.value = "";
  taskDateInput.value = "";
  loadTasks();
});

// ---------- Inicialização ----------
loadHistory();
inputEl.focus();

// Registra o service worker (permite "adicionar à tela inicial" no celular)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}
