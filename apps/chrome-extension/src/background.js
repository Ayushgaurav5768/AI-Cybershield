importScripts("api.js");

const DEFAULT_SETTINGS = {
  autoScanOnLoad: true,
  warnOnFormSubmit: true,
  blockDangerous: true
};

chrome.runtime.onInstalled.addListener(async () => {
  const current = await chrome.storage.local.get(["settings"]);
  if (!current.settings) {
    await chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url) return;
  if (!tab.url.startsWith("http")) return;

  const { settings = DEFAULT_SETTINGS, allowlist = [] } = await chrome.storage.local.get(["settings", "allowlist"]);
  if (!settings.autoScanOnLoad) return;

  const hostname = new URL(tab.url).hostname;
  if (allowlist.includes(hostname)) {
    setBadge("SAFE", "#22c55e", tabId);
    return;
  }

  try {
    const result = await scanUrl(tab.url);
    await chrome.storage.local.set({ latestScan: result, latestScanUrl: tab.url });

    if (result.risk_level === "dangerous") {
      setBadge("DNG", "#ef4444", tabId);
      await postEvent("auto_scan_dangerous", tab.url, result.risk_level, { score: result.risk_score });

      if (settings.blockDangerous) {
        const warningUrl = chrome.runtime.getURL("src/warning.html") + `?target=${encodeURIComponent(tab.url)}`;
        chrome.tabs.update(tabId, { url: warningUrl });
      }
    } else if (result.risk_level === "suspicious") {
      setBadge("WARN", "#f59e0b", tabId);
      await postEvent("auto_scan_suspicious", tab.url, result.risk_level, { score: result.risk_score });
    } else {
      setBadge("SAFE", "#22c55e", tabId);
    }
  } catch {
    setBadge("ERR", "#64748b", tabId);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    if (message.type === "scan-current-tab") {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url || !tab.url.startsWith("http")) {
        sendResponse({ ok: false, error: "No scannable tab" });
        return;
      }

      const result = await scanUrl(tab.url);
      await chrome.storage.local.set({ latestScan: result, latestScanUrl: tab.url });
      await postEvent("manual_scan", tab.url, result.risk_level, { score: result.risk_score });
      sendResponse({ ok: true, result, url: tab.url });
      return;
    }

    if (message.type === "report-site") {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) {
        sendResponse({ ok: false, error: "No active tab" });
        return;
      }

      await submitReport(tab.url, message.reportType, message.reason || "Reported from extension");
      await postEvent("user_report", tab.url, "n/a", { reportType: message.reportType });
      sendResponse({ ok: true });
      return;
    }

    if (message.type === "trust-site") {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) {
        sendResponse({ ok: false, error: "No active tab" });
        return;
      }

      const hostname = new URL(tab.url).hostname;
      const current = await chrome.storage.local.get(["allowlist"]);
      const allowlist = current.allowlist || [];
      if (!allowlist.includes(hostname)) {
        allowlist.push(hostname);
        await chrome.storage.local.set({ allowlist });
      }

      await allowlistDomain(hostname);
      await postEvent("site_trusted", tab.url, "safe", {});
      sendResponse({ ok: true, domain: hostname });
      return;
    }

    if (message.type === "credential-form-detected") {
      const tabUrl = sender?.tab?.url || null;
      const payload = message.payload || {};
      await postEvent("credential_form_detected", tabUrl, payload.riskLevel || "unknown", payload);
      sendResponse({ ok: true });
      return;
    }

    sendResponse({ ok: false, error: "Unhandled message" });
  })().catch((err) => {
    sendResponse({ ok: false, error: String(err) });
  });

  return true;
});

function setBadge(text, color, tabId) {
  chrome.action.setBadgeText({ text, tabId });
  chrome.action.setBadgeBackgroundColor({ color, tabId });
}
