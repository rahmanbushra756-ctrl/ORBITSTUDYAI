const form = document.getElementById("chat-form");
const questionInput = document.getElementById("question");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send");
const clearButton = document.getElementById("clear-chat");

const HISTORY_KEY = "orbit-chat-history";

let conversation = loadHistory();

function loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];

    return saved
      .map((item) => ({
        role: item.role || (item.className === "user-message" ? "user" : "assistant"),
        content: item.content || item.text || ""
      }))
      .filter((item) => item.content);
  } catch {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(conversation));
}

function addMessage(text, className) {
  const message = document.createElement("div");
  message.className = `message ${className}`;

  if (className === "orbit-message" && window.marked && window.DOMPurify) {
    message.innerHTML = DOMPurify.sanitize(marked.parse(text));
  } else {
    message.textContent = text;
  }

  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
  return message;
}

function renderHistory() {
  messages.innerHTML = "";

  conversation.forEach((item) => {
    addMessage(
      item.content,
      item.role === "user" ? "user-message" : "orbit-message"
    );
  });
}

function addToConversation(role, content) {
  conversation.push({ role, content });
  saveHistory();
  addMessage(content, role === "user" ? "user-message" : "orbit-message");
}

renderHistory();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();
  if (!question) return;

  const previousMessages = [...conversation];

  addToConversation("user", question);
  questionInput.value = "";

  sendButton.disabled = true;
  sendButton.textContent = "Thinking...";

  const waitingMessage = addMessage("ORBIT is thinking...", "orbit-message");

  try {
    const response = await fetch("https://orbitstudyai.onrender.com/chat", {, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question,
        history: previousMessages
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.answer || `Server error (${response.status})`);
    }

    const answer = data.answer || "I didn't receive an answer.";

    waitingMessage.remove();
    addToConversation("assistant", answer);
  } catch (error) {
    waitingMessage.textContent =
      "Couldn't reach ORBIT. Check that server.py is running.\n" +
      error.message;
  } finally {
    sendButton.disabled = false;
    sendButton.textContent = "Ask ORBIT";
    questionInput.focus();
    messages.scrollTop = messages.scrollHeight;
  }
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton?.addEventListener("click", () => {
  conversation = [];
  saveHistory();
  renderHistory();
});
