document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("question");
    const quickQuestions = document.querySelectorAll("#quickQuestions .chip");

    if (input) {
        input.addEventListener("keydown", async (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                await askAssistant();
            }
        });
    }

    quickQuestions.forEach((button) => {
        button.addEventListener("click", () => {
            const text = button.getAttribute("data-question") || "";
            input.value = text;
            input.focus();
        });
    });
});

async function askAssistant() {
    const input = document.getElementById("question");
    const chatBox = document.getElementById("chat-box");
    const sendBtn = document.getElementById("sendBtn");

    const question = input.value.trim();
    if (!question) return;

    sendBtn.disabled = true;

    chatBox.innerHTML += `
        <div class="message user-message">
            ${escapeHtml(question)}
        </div>
    `;

    input.value = "";

    const typingDiv = document.createElement("div");
    typingDiv.className = "message ai-message typing";
    typingDiv.innerText = "Analyzing threat intelligence...";
    chatBox.appendChild(typingDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`${API_BASE}/assistant`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        let payload = null;
        const rawText = await response.text();
        try {
            payload = rawText ? JSON.parse(rawText) : null;
        } catch {
            payload = null;
        }

        if (!response.ok) {
            const fallback = payload?.detail || "Assistant request failed.";
            throw new Error(fallback);
        }

        typingDiv.remove();

        const answer = payload?.response || "No response received from assistant.";

        chatBox.innerHTML += `
            <div class="message ai-message">
                ${escapeHtml(answer)}
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        typingDiv.innerText = error?.message || "Error connecting to AI engine.";
    } finally {
        sendBtn.disabled = false;
    }
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}