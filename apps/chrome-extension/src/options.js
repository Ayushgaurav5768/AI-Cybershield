const autoScan = document.getElementById("autoScan");
const warnForms = document.getElementById("warnForms");
const blockDangerous = document.getElementById("blockDangerous");
const saveBtn = document.getElementById("saveBtn");
const msg = document.getElementById("msg");

chrome.storage.local.get(["settings"], (data) => {
  const settings = data.settings || {};
  autoScan.checked = settings.autoScanOnLoad !== false;
  warnForms.checked = settings.warnOnFormSubmit !== false;
  blockDangerous.checked = settings.blockDangerous !== false;
});

saveBtn.addEventListener("click", async () => {
  const settings = {
    autoScanOnLoad: autoScan.checked,
    warnOnFormSubmit: warnForms.checked,
    blockDangerous: blockDangerous.checked
  };

  await chrome.storage.local.set({ settings });
  msg.textContent = "Saved";
});
