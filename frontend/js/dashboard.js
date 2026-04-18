const API_BASE = "http://127.0.0.1:8000";

let threatChartInstance = null;
let trendChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    const refreshBtn = document.getElementById("refreshDashboard");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            loadDashboard();
        });
    }

    loadDashboard();
});

async function loadDashboard() {
    try {
        const [metricsRes, trendsRes, domainsRes, eventsRes, recentRes] = await Promise.all([
            fetch(`${API_BASE}/dashboard/metrics`),
            fetch(`${API_BASE}/dashboard/trends?limit_days=7`),
            fetch(`${API_BASE}/dashboard/top-domains?limit=10`),
            fetch(`${API_BASE}/dashboard/extension-events?limit=20`),
            fetch(`${API_BASE}/recent-scans`)
        ]);

        const metrics = await metricsRes.json();
        const trends = await trendsRes.json();
        const domains = await domainsRes.json();
        const events = await eventsRes.json();
        const recentScans = await recentRes.json();

        updateMetrics(metrics);
        createThreatChart(metrics.phishing_count || 0, metrics.safe_count || 0);
        createTrendChart(trends || []);
        renderTopDomains(domains || []);
        renderRecentScans(recentScans || []);
        renderEventFeed(events || []);
    } catch (error) {
        console.error("Error loading dashboard:", error);
    }
}

function updateMetrics(metrics) {
    setText("totalScans", metrics.total_scans || 0);
    setText("phishingCount", metrics.phishing_count || 0);
    setText("safeCount", metrics.safe_count || 0);
    setText("reportsPending", metrics.reports_pending || 0);
    setText("extensionEventsCount", metrics.extension_events || 0);
}

function createThreatChart(phishing, safe) {
    const canvas = document.getElementById("threatChart");
    if (!canvas) {
        return;
    }

    if (threatChartInstance) {
        threatChartInstance.destroy();
    }

    threatChartInstance = new Chart(canvas.getContext("2d"), {
        type: "doughnut",
        data: {
            labels: ["Phishing", "Safe"],
            datasets: [{
                data: [phishing, safe],
                backgroundColor: ["#ff4d6d", "#41d98e"],
                borderWidth: 0
            }]
        },
        options: {
            cutout: "72%",
            plugins: {
                legend: {
                    labels: { color: "#f5f7fb" }
                }
            }
        }
    });
}

function createTrendChart(trends) {
    const canvas = document.getElementById("trendChart");
    if (!canvas) {
        return;
    }

    if (trendChartInstance) {
        trendChartInstance.destroy();
    }

    const labels = trends.map((item) => item.day);
    const phishingData = trends.map((item) => item.phishing || 0);
    const safeData = trends.map((item) => item.safe || 0);

    trendChartInstance = new Chart(canvas.getContext("2d"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Phishing",
                    data: phishingData,
                    borderColor: "#ff4d6d",
                    backgroundColor: "rgba(255,77,109,0.2)",
                    tension: 0.35,
                    fill: true
                },
                {
                    label: "Safe",
                    data: safeData,
                    borderColor: "#41d98e",
                    backgroundColor: "rgba(65,217,142,0.2)",
                    tension: 0.35,
                    fill: true
                }
            ]
        },
        options: {
            plugins: {
                legend: { labels: { color: "#f5f7fb" } }
            },
            scales: {
                x: {
                    ticks: { color: "#a8b0bf" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                },
                y: {
                    ticks: { color: "#a8b0bf" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                }
            }
        }
    });
}

function renderTopDomains(domains) {
    const body = document.querySelector("#domainTable tbody");
    if (!body) {
        return;
    }

    body.innerHTML = "";
    domains.forEach((domain) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(domain.domain || "unknown")}</td>
            <td>${domain.count || 0}</td>
            <td>${domain.avg_risk || 0}%</td>
            <td>${domain.phishing_hits || 0}</td>
        `;
        body.appendChild(row);
    });
}

function renderRecentScans(scans) {
    const body = document.querySelector("#scanTable tbody");
    if (!body) {
        return;
    }

    body.innerHTML = "";
    scans.forEach((scan) => {
        const row = document.createElement("tr");
        const labelColor = scan.prediction === "Phishing" ? "#ff4d6d" : "#41d98e";
        row.innerHTML = `
            <td>${escapeHtml(scan.url)}</td>
            <td style="color:${labelColor}; font-weight:700;">${escapeHtml(scan.prediction)}</td>
            <td>${scan.risk_score || 0}%</td>
            <td>${new Date(scan.created_at).toLocaleString()}</td>
        `;
        body.appendChild(row);
    });
}

function renderEventFeed(events) {
    const list = document.getElementById("eventFeed");
    if (!list) {
        return;
    }

    list.innerHTML = "";
    if (events.length === 0) {
        list.innerHTML = `<li class="muted">No extension events yet.</li>`;
        return;
    }

    events.forEach((event) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHtml(event.event_type || "event")}</strong> | ${escapeHtml(event.url || "n/a")} | ${escapeHtml(event.risk_level || "unknown")} | ${new Date(event.created_at).toLocaleString()}`;
        list.appendChild(li);
    });
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = String(value);
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
