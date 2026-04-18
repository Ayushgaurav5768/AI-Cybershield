const riskLevel = document.getElementById("riskLevel");
const scoreLabel = document.getElementById("scoreLabel");
const summary = document.getElementById("summary");
const urlLabel = document.getElementById("urlLabel");

const scanBtn = document.getElementById("scanBtn");
const reportBtn = document.getElementById("reportBtn");
const trustBtn = document.getElementById("trustBtn");

hydrate();

scanBtn.addEventListener("click", async () => {
  const response = await sendRuntime({ type: "scan-current-tab" });
  if (!response.ok) {
    summary.textContent = response.error || "Scan failed";
    return;
  }

  renderResult(response.result, response.url);
});

reportBtn.addEventListener("click", async () => {
  const reason = prompt("Why are you reporting this site?") || "Reported as phishing by user";
  const response = await sendRuntime({ type: "report-site", reportType: "phishing", reason });
  summary.textContent = response.ok ? "Report submitted" : (response.error || "Report failed");
});

trustBtn.addEventListener("click", async () => {
  const response = await sendRuntime({ type: "trust-site" });
  summary.textContent = response.ok ? `Trusted: ${response.domain}` : (response.error || "Trust action failed");
});

function hydrate() {
  chrome.storage.local.get(["latestScan", "latestScanUrl"], (data) => {
    if (data.latestScan) {
      renderResult(data.latestScan, data.latestScanUrl || "");
    }
  });
}

function renderResult(result, scannedUrl) {
  riskLevel.textContent = (result.risk_level || "unknown").toUpperCase();
  riskLevel.className = `status ${result.risk_level || ""}`;

  scoreLabel.textContent = `Risk: ${result.risk_score} / 100 | Confidence: ${result.confidence_score || "--"}%`;
  urlLabel.textContent = scannedUrl;
  summary.textContent = result.user_explanation || (result.reasons || []).join("; ");
}

function sendRuntime(payload) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(payload, (response) => {
      resolve(response || { ok: false, error: "No response" });
    });
  });
}
