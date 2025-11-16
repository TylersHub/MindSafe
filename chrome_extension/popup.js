// popup.js
//
// Shows the latest MindSafe evaluation for the last analyzed video.

function renderResult(r) {
  const resultDiv = document.getElementById("result");
  const statusPill = document.getElementById("status-pill");
  if (!r) {
    if (statusPill) statusPill.textContent = "Idle";
    resultDiv.innerText =
      "No video analyzed yet. Open a YouTube / YouTube Kids video, wait for MindSafe to finish, then reopen this popup.";
    return;
  }

  if (r.status === "pending") {
    if (statusPill) statusPill.textContent = "Analyzing…";
    resultDiv.innerHTML = `
      <div><b>Status:</b> Analysis in progress…</div>
      <div><b>Title:</b> ${r.title || "Video"}</div>
      <div><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>
    `;
    return;
  }

  if (r.status === "error") {
    if (statusPill) statusPill.textContent = "Error";
    resultDiv.innerHTML = `
      <div style="color:red"><b>Status:</b> Analysis failed</div>
      <div><b>Title:</b> ${r.title || "Video"}</div>
      <div><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>
      <div><b>Error:</b> ${r.error || "Unknown error"}</div>
    `;
    return;
  }

  const devScore =
    typeof r.devScore === "number" ? `${r.devScore.toFixed(1)}/100` : "N/A";
  const brainrot =
    typeof r.brainrotIndex === "number" ? `${r.brainrotIndex.toFixed(1)}/100` : "N/A";
  const tenPoint =
    typeof r.tenPointScore === "number" ? `${r.tenPointScore}/10` : "N/A";

  const reasonsText = Array.isArray(r.reasons) ? r.reasons.join(", ") : "";

  const dim =
    r.rawApiResult && r.rawApiResult.dimension_scores
      ? r.rawApiResult.dimension_scores
      : null;

  let dimHtml = "";
  if (dim) {
    // Map backend JSON keys to human labels
    const dimMap = {
      Pacing: "Pacing",
      Story: "Story",
      Language: "Language",
      SEL: "Social-Emotional Learning",
      Fantasy: "Fantasy",
      Interactivity: "Interactivity",
    };
    dimHtml =
      "<ul>" +
      Object.entries(dimMap)
        .map(([apiKey, labelText]) => {
          const v = dim[apiKey];
          const score = typeof v === "number" ? `${v.toFixed(1)}/100` : "N/A";
          return `<li><b>${labelText}:</b> ${score}</li>`;
        })
        .join("") +
      "</ul>";
  }

  resultDiv.innerHTML = `
    <div style="margin-bottom:6px;">
      <div style="font-size:12px; color:#6b7280;">Overall rating</div>
      <div class="score">${tenPoint}</div>
      <div style="font-size:12px; color:#374151; margin-top:2px;">${r.label || "N/A"}</div>
    </div>
    <hr style="border:none; border-top:1px solid #e5e7eb; margin:6px 0;" />
    <div style="margin-bottom:4px;"><b>Developmental score:</b> ${devScore}</div>
    <div style="margin-bottom:6px;"><b>Brainrot index:</b> ${brainrot}</div>
    <div style="margin-bottom:4px;"><b>Title:</b> ${r.title || "Video"}</div>
    <div style="margin-bottom:6px;"><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>
    <div style="margin-bottom:4px;"><b>Reasons:</b> ${reasonsText}</div>
    ${dimHtml ? `<div><b>Dimension scores:</b>${dimHtml}</div>` : ""}
  `;

  if (statusPill) statusPill.textContent = "Complete";
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
      resultDiv.innerHTML = `<div style="color:red"><b>Storage exception:</b> ${
        e && e.message
      }</div>`;
    }
    return;
  }

  if (resp && resp.error) {
    resultDiv.innerHTML = `<div style="color:red"><b>Storage error:</b> ${resp.error}</div>`;
    return;
  }

  renderResult(resp && resp.lastScore);
});


