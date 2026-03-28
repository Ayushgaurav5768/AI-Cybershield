async function askAssistant() {
    const input = document.getElementById("question");
    const chatBox = document.getElementById("chat-box");

    const question = input.value.trim();
    if (!question) return;

    // Add user message
    chatBox.innerHTML += `
        <div class="message user-message">
            ${question}
        </div>
    `;

    input.value = "";

    // Typing indicator
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

        const data = await response.json();

        typingDiv.remove();

        chatBox.innerHTML += `
            <div class="message ai-message">
                ${data.response}
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        typingDiv.innerText = "Error connecting to AI engine.";
    }
}