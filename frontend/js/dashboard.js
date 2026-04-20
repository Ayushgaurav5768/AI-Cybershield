const LOCAL_API_BASE = "http://127.0.0.1:8000";
const PROD_API_BASE = "https://ai-cybershield-backend-production.up.railway.app";
const API_TIMEOUT_MS = 12000;

function resolveApiBase() {
    const override = localStorage.getItem("apiBaseOverride");
    if (override) {
        return override;
    }

    if (window.location.protocol === "file:") {
        return LOCAL_API_BASE;
    }

    const hostname = window.location.hostname;
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "" ? LOCAL_API_BASE : PROD_API_BASE;
}

const API_BASE = resolveApiBase();

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
    const [
        metricsResult,
        trendsResult,
        domainsResult,
        eventsResult,
        recentResult
    ] = await Promise.allSettled([
        apiRequest("/dashboard/metrics"),
        apiRequest("/dashboard/trends?limit_days=7"),
        apiRequest("/dashboard/top-domains?limit=10"),
        apiRequest("/dashboard/extension-events?limit=20"),
        apiRequest("/recent-scans")
    ]);

    const metrics = readResult(metricsResult, { total_scans: 0, phishing_count: 0, safe_count: 0, reports_pending: 0, extension_events: 0 });
    const trends = readResult(trendsResult, []);
    const domains = readResult(domainsResult, []);
    const events = readResult(eventsResult, []);
    const recentScans = readResult(recentResult, []);

    const mergedRecentScans = mergeRecentScansWithLocal(recentScans);

    updateMetrics(metrics);
    createThreatChart(metrics.phishing_count || 0, metrics.safe_count || 0);
    createTrendChart(trends || []);
    renderTopDomains(domains || []);
    renderRecentScans(mergedRecentScans || []);
    renderEventFeed(events || []);
}

function readResult(result, fallback) {
    if (result.status === "fulfilled") {
        return result.value;
    }

    console.error(`Dashboard request failed at ${API_BASE}:`, result.reason);
    return fallback;
}

async function apiRequest(path, timeoutMs = API_TIMEOUT_MS) {
    const response = await fetchWithTimeout(`${API_BASE}${path}`, {}, timeoutMs);
    if (!response.ok) {
        throw new Error(`${path} failed with status ${response.status}`);
    }
    return response.json();
}

async function fetchWithTimeout(url, options = {}, timeoutMs = API_TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        return await fetch(url, {
            ...options,
            signal: controller.signal
        });
    } catch (error) {
        if (error?.name === "AbortError") {
            throw new Error(`Request timed out after ${Math.ceil(timeoutMs / 1000)}s.`);
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
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

function mergeRecentScansWithLocal(serverScans) {
    const localScans = getLocalHistoryEntries();
    const normalizedServer = (serverScans || []).map((scan) => ({
        ...scan,
        created_at: scan.created_at || new Date().toISOString()
    }));

    const merged = [...normalizedServer, ...localScans];
    merged.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    const deduped = [];
    const seen = new Set();
    for (const item of merged) {
        const key = `${item.url}|${item.created_at}|${item.prediction}`;
        if (seen.has(key)) {
            continue;
        }
        seen.add(key);
        deduped.push(item);
        if (deduped.length >= 10) {
            break;
        }
    }

    return deduped;
}

function getLocalHistoryEntries() {
    const candidates = ["scanHistory", "scan_history", "history"];
    let history = [];

    for (const key of candidates) {
        try {
            const parsed = JSON.parse(localStorage.getItem(key) || "[]");
            if (Array.isArray(parsed) && parsed.length > 0) {
                history = parsed;
                break;
            }
        } catch {
            continue;
        }
    }

    return history.map((item) => ({
        url: item.url || "unknown",
        prediction: item.prediction || (Number(item.risk || item.risk_score || 0) >= 45 ? "Phishing" : "Safe"),
        risk_score: Number(item.risk_score ?? item.risk ?? 0),
        created_at: item.created_at || item.at || new Date().toISOString()
    }));
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
