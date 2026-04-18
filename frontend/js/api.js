const API_BASE = "http://127.0.0.1:8000";
let gaugeChart = null;

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("scanBtn");
    const input = document.getElementById("urlInput");
    const chips = document.querySelectorAll("#sampleUrls .chip");

    if (!button || !input) {
        return;
    }

    button.addEventListener("click", async (event) => {
        event.preventDefault();
        await runScan();
    });

    input.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            await runScan();
        }
    });

    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const suggested = chip.getAttribute("data-url") || "";
            input.value = suggested;
            input.focus();
        });
    });

    loadHistory();
});

async function runScan() {
    const input = document.getElementById("urlInput");
    const status = document.getElementById("scanStatus");
    const button = document.getElementById("scanBtn");

    const url = input.value.trim();
    if (!url) {
        status.textContent = "Please enter a URL before scanning.";
        return;
    }

    status.textContent = "Analyzing URL fingerprint and risk signals...";
    button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/scan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            throw new Error("Scan failed");
        }

        const data = await response.json();
        renderScanResult(data);
        saveHistory({
            url,
            prediction: data.prediction,
            risk: data.risk_score,
            level: data.risk_level,
            at: new Date().toISOString()
        });
        status.textContent = "Scan complete.";
    } catch (err) {
        status.textContent = "Unable to complete scan. Confirm backend service is running.";
        console.error(err);
    } finally {
        button.disabled = false;
    }
}

function renderScanResult(data) {
    const prediction = document.getElementById("result");
    const confidence = document.getElementById("confidence");
    const riskLevel = document.getElementById("riskLevel");
    const reasonsList = document.getElementById("reasonsList");
    const action = document.getElementById("recommendedAction");
    const signalsGrid = document.getElementById("signalsGrid");

    prediction.textContent = `Prediction: ${data.prediction}`;
    confidence.textContent = `confidence: ${data.confidence_score}%`;
    action.textContent = data.recommended_action || "No recommended action.";

    const level = (data.risk_level || "safe").toLowerCase();
    riskLevel.className = `pill ${riskClass(level)}`;
    riskLevel.textContent = `risk level: ${level}`;

    reasonsList.innerHTML = "";
    (data.reasons || ["No reasons returned."]).forEach((reason) => {
        const li = document.createElement("li");
        li.textContent = reason;
        reasonsList.appendChild(li);
    });

    signalsGrid.innerHTML = "";
    const signals = data.signals || [];
    if (signals.length === 0) {
        const p = document.createElement("p");
        p.className = "muted";
        p.textContent = "No signals returned.";
        signalsGrid.appendChild(p);
    }

    signals.forEach((signal) => {
        const card = document.createElement("div");
        card.className = "signal-item";
        card.innerHTML = `
            <span class="code">${escapeHtml(signal.code || "unknown")}</span>
            <div>${escapeHtml(signal.message || "No message")}</div>
            <span class="score">severity: ${escapeHtml(signal.severity || "n/a")} | +${signal.points || 0} pts</span>
        `;
        signalsGrid.appendChild(card);
    });

    createGauge(data.risk_score || 0);
}

function createGauge(score) {
    const canvas = document.getElementById("riskGauge");
    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");
    if (gaugeChart) {
        gaugeChart.destroy();
    }

    const color = score > 65 ? "#ff4d6d" : score > 35 ? "#f7b500" : "#41d98e";

    gaugeChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [color, "#222937"],
                borderWidth: 0
            }]
        },
        options: {
            cutout: "82%",
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });

    animateCounter(score);
}

function animateCounter(target) {
    const el = document.getElementById("riskPercent");
    if (!el) {
        return;
    }

    let count = Number.parseInt(el.textContent.replace("%", ""), 10) || 0;
    const direction = count < target ? 1 : -1;

    const interval = setInterval(() => {
        if (count === target) {
            clearInterval(interval);
            return;
        }
        count += direction;
        el.textContent = `${count}%`;
    }, 8);
}

function riskClass(level) {
    if (level === "critical" || level === "high") {
        return "danger";
    }
    if (level === "medium") {
        return "warn";
    }
    return "safe";
}

function saveHistory(entry) {
    const key = "scanHistory";
    const current = JSON.parse(localStorage.getItem(key) || "[]");
    current.unshift(entry);
    localStorage.setItem(key, JSON.stringify(current.slice(0, 7)));
    loadHistory();
}

function loadHistory() {
    const list = document.getElementById("historyList");
    if (!list) {
        return;
    }

    const history = JSON.parse(localStorage.getItem("scanHistory") || "[]");
    list.innerHTML = "";

    if (history.length === 0) {
        list.innerHTML = `<li class="muted">No local history yet.</li>`;
        return;
    }

    history.forEach((item) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHtml(item.prediction)}</strong> | ${escapeHtml(item.url)} | risk ${item.risk}%`;
        list.appendChild(li);
    });
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
