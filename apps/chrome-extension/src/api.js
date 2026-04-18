const API_BASE = "http://127.0.0.1:8000";

async function scanUrl(url) {
  const response = await fetch(`${API_BASE}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });

  if (!response.ok) {
    throw new Error(`Scan failed with status ${response.status}`);
  }

  return response.json();
}

async function submitReport(url, reportType, reason, channel = "extension") {
  const response = await fetch(`${API_BASE}/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, report_type: reportType, reason, reporter_channel: channel })
  });

  return response.json();
}

async function allowlistDomain(domain) {
  const response = await fetch(`${API_BASE}/reports/allowlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain })
  });

  return response.json();
}

async function postEvent(eventType, url, riskLevel, payload = {}) {
  await fetch(`${API_BASE}/reports/extension-event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_type: eventType,
      url,
      risk_level: riskLevel,
      payload_json: JSON.stringify(payload)
    })
  });
}
