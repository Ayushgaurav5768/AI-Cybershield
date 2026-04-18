function detectCredentialForms() {
  const forms = Array.from(document.forms || []);
  const credentialForms = forms.filter((form) => {
    const hasPassword = !!form.querySelector('input[type="password"]');
    const hasEmailOrUser = !!form.querySelector('input[type="email"], input[name*="user" i], input[name*="login" i]');
    return hasPassword && hasEmailOrUser;
  });

  if (!credentialForms.length) return;

  chrome.storage.local.get(["latestScan", "latestScanUrl", "settings"], (data) => {
    const settings = data.settings || {};
    if (!settings.warnOnFormSubmit) return;

    const latestScan = data.latestScan;
    const sameUrl = data.latestScanUrl === window.location.href;
    const level = sameUrl && latestScan ? latestScan.risk_level : "unknown";

    credentialForms.forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (level === "dangerous" || level === "suspicious") {
          const ok = window.confirm(
            `CyberShield warning: this page was rated ${level}. Submitting credentials may be unsafe. Continue anyway?`
          );
          if (!ok) event.preventDefault();
        }

        chrome.runtime.sendMessage({
          type: "credential-form-detected",
          payload: {
            riskLevel: level,
            pageTitle: document.title,
            formAction: form.action || ""
          }
        });
      });
    });
  });
}

detectCredentialForms();
