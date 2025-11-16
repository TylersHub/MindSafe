// popup.js

function renderResult(r) {
  const resultDiv = document.getElementById("result");
  if (!r) {
    resultDiv.innerText = "No video analyzed yet. Click a video, then reopen this popup.";
    return;
  }

  const copiedText = r.copied
    ? `<div style="color:green"><b>Copied:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>`
    : `<div><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>`;

  resultDiv.innerHTML = `
    <div><b>Score:</b> <span class="score">${r.score}/10</span></div>
    <div><b>Rating:</b> ${r.label}</div>
    <div><b>Title:</b> ${r.title}</div>
    ${copiedText}
    <div><b>Reasons:</b> ${Array.isArray(r.reasons) ? r.reasons.join(", ") : ""}</div>
  `;
}

// Ask background for lastScore (with fallback to storage)
chrome.runtime.sendMessage({ type: "GET_LAST_SCORE" }, (resp) => {
  const resultDiv = document.getElementById("result");

  if (chrome.runtime.lastError) {
    console.warn("Popup: GET_LAST_SCORE failed:", chrome.runtime.lastError);
    try {
      chrome.storage.local.get("lastScore", (data) => {
        if (chrome.runtime.lastError) {
          resultDiv.innerHTML = `<div style="color:red"><b>Storage error:</b> ${chrome.runtime.lastError.message}</div>`;
        } else {
          renderResult(data.lastScore);
        }
      });
    } catch (e) {
      resultDiv.innerHTML = `<div style="color:red"><b>Storage exception:</b> ${e && e.message}</div>`;
    }
    return;
  }

  if (resp && resp.error) {
    resultDiv.innerHTML = `<div style="color:red"><b>Storage error:</b> ${resp.error}</div>`;
    return;
  }

  renderResult(resp && resp.lastScore);
});

// Listen for storage error broadcasts (optional)
chrome.runtime.onMessage.addListener((msg) => {
  if (msg && msg.type === "STORAGE_ERROR") {
    const resultDiv = document.getElementById("result");
    if (resultDiv) {
      resultDiv.innerHTML = `<div style="color:red"><b>Storage error:</b> ${msg.error}</div>`;
    }
  }
});
