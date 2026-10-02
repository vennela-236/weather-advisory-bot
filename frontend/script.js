const API_URL = "http://127.0.0.1:8000/chat";

const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send-button");
const connectionStatus = document.getElementById("connection-status");

// Keep the same session ID for this browser tab.
let sessionId = sessionStorage.getItem("weather_session_id");

if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("weather_session_id", sessionId);
}

function addMessage(text, sender) {
    const message = document.createElement("div");
    message.className = `message ${sender}-message`;

    if (sender === "bot") {
        const label = document.createElement("p");
        label.className = "message-label";
        label.textContent = "Weather Advisory Bot";
        message.appendChild(label);
    }

    const content = document.createElement("p");
    content.textContent = text;
    message.appendChild(content);

    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;

    return message;
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = messageInput.value.trim();

    if (!question) {
        return;
    }

    addMessage(question, "user");
    messageInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    const loadingMessage = addMessage("Checking weather and applicable procedures...", "bot");

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: question,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "The server could not process your question.");
        }

        loadingMessage.remove();
        addMessage(data.answer || "The bot returned an empty response.", "bot");

        if (data.session_id) {
            sessionId = data.session_id;
            sessionStorage.setItem("weather_session_id", sessionId);
        }

        connectionStatus.textContent = "Connected";
    } catch (error) {
        loadingMessage.remove();
        addMessage(
            `Unable to get a response: ${error.message}. Please check that the backend is running.`,
            "bot"
        );
        connectionStatus.textContent = "Connection issue";
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        messageInput.focus();
    }
});

// Check whether the backend is reachable.
async function checkBackend() {
    try {
        const response = await fetch("http://127.0.0.1:8000/");
        if (!response.ok) {
            throw new Error("Backend unavailable");
        }
        connectionStatus.textContent = "Connected";
    } catch {
        connectionStatus.textContent = "Backend offline";
    }
}

checkBackend();