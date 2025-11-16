// popup.js
//
// Shows the latest MindSafe evaluation for the last analyzed video.

function renderResult(r) {
  const resultDiv = document.getElementById("result");
  if (!r) {
    resultDiv.innerText =
      "No video analyzed yet. Open a YouTube / YouTube Kids video, wait for MindSafe to finish, then reopen this popup.";
    return;
  }

  if (r.status === "pending") {
    resultDiv.innerHTML = `
      <div><b>Status:</b> Analysis in progress…</div>
      <div><b>Title:</b> ${r.title || "Video"}</div>
      <div><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>
    `;
    return;
  }

  if (r.status === "error") {
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
    const prettyNames = {
      pacing: "Pacing",
      story: "Story",
      language: "Language",
      sel: "Social-Emotional Learning",
      fantasy: "Fantasy",
      interactivity: "Interactivity",
    };
    dimHtml =
      "<ul>" +
      Object.keys(prettyNames)
        .map((key) => {
          const v = dim[key];
          const score =
            typeof v === "number" ? `${v.toFixed(1)}/100` : "N/A";
          return `<li><b>${prettyNames[key]}:</b> ${score}</li>`;
        })
        .join("") +
      "</ul>";
  }

  resultDiv.innerHTML = `
    <div><b>Overall rating:</b> <span class="score">${tenPoint}</span></div>
    <div><b>Label:</b> ${r.label || "N/A"}</div>
    <div><b>Developmental score:</b> ${devScore}</div>
    <div><b>Brainrot index:</b> ${brainrot}</div>
    <div><b>Title:</b> ${r.title || "Video"}</div>
    <div><b>Link:</b> <a href="${r.videoUrl}" target="_blank">${r.videoUrl}</a></div>
    <div><b>Reasons:</b> ${reasonsText}</div>
    ${
      dimHtml
        ? `<div><b>Dimension scores:</b>${dimHtml}</div>`
        : ""
    }
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


