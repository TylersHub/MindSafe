// content_script.js – MindSafe stats card in YouTube / YouTube Kids right column
// Talks to the background service worker, which calls the MindSafe API
// to get REAL evaluation data for the current video.

console.log("[MindSafe] content script loaded on", location.href);

// ====================== URL HELPERS ======================

function isWatchPage(urlString) {
  try {
    const url = new URL(urlString);
    return (
      url.pathname === "/watch" &&
      (url.hostname.includes("youtube.com") ||
        url.hostname.includes("youtubekids.com") ||
        url.hostname.includes("kids.youtube.com"))
    );
  } catch (e) {
    return false;
  }
}

// ====================== RIGHT COLUMN LOOKUP ======================

// Kids:   #secondary-results #related
// Normal: #secondary-inner / #secondary
function findRightColumn() {
  const kids =
    document.querySelector("#secondary-results #related") ||
    document.querySelector("#related");
  if (kids) return kids;

  const regular =
    document.querySelector("#secondary-inner") ||
    document.querySelector("#secondary");
  if (regular) return regular;

  return null;
}

// ====================== PANEL RENDERING ======================

function renderPanel(data) {
  const container = findRightColumn();
  if (!container) {
    console.log("[MindSafe] right column not found yet");
  return false;
  }

  let panel = document.getElementById("mindsafe-stats-panel");
  const isNew = !panel;

  if (!panel) {
    panel = document.createElement("div");
    panel.id = "mindsafe-stats-panel";

    panel.style.marginBottom = "8px";
    panel.style.padding = "10px 12px";
    panel.style.borderRadius = "10px";
    panel.style.boxSizing = "border-box";
    panel.style.fontFamily = "Roboto, Arial, sans-serif";
    panel.style.fontSize = "12px";

    panel.style.background = "rgba(255,255,255,0.96)";
    panel.style.color = "#111";
    panel.style.boxShadow = "0 1px 3px rgba(0,0,0,0.25)";
    panel.style.border = "1px solid rgba(0,0,0,0.08)";
  }

  const status = data && data.status;
  // Prefer tenPointScore from background; fall back to deriving from devScore if needed
  let tenPointScore =
    data && typeof data.tenPointScore === "number" ? data.tenPointScore : null;
  if (
    tenPointScore == null &&
    data &&
    typeof data.devScore === "number" &&
    !Number.isNaN(data.devScore)
  ) {
    const clamped = Math.max(0, Math.min(100, data.devScore));
    tenPointScore = Math.max(1, Math.min(10, Math.round(clamped / 10)));
  }
  const title = data && data.title ? data.title : "this video";
  const label = data && data.label ? data.label : "Analysis pending";
  const reasons = Array.isArray(data && data.reasons) ? data.reasons : [];

  let scoreHtml = "";
  if (status === "done") {
    const scoreDisplay =
      tenPointScore != null ? `${tenPointScore}` : "N/A";
    scoreHtml = `
      <div style="display:flex; align-items:baseline; gap:6px; margin-bottom:4px;">
        <span style="font-size:26px; font-weight:700;">${scoreDisplay}</span>
        <span style="font-size:12px; opacity:0.8;">/ 10</span>
      </div>
    `;
  } else if (status === "error") {
    scoreHtml = `
      <div style="font-size:12px; font-weight:500; margin-bottom:4px; color:#b91c1c;">
        MindSafe analysis failed. Make sure the MindSafe API is running.
      </div>
    `;
  } else {
    scoreHtml = `
      <div style="font-size:12px; font-weight:500; margin-bottom:4px;">
        Running full MindSafe analysis for this video…
      </div>
    `;
  }

  const reasonsHtml =
    reasons.length > 0
      ? `<ul style="padding-left:18px; margin:0; font-size:11px;">
          ${reasons.map((r) => `<li>${r}</li>`).join("")}
        </ul>`
      : "";

  panel.innerHTML = `
    <div style="font-size:11px; font-weight:600; opacity:0.8; margin-bottom:4px;">
      MindSafe Content Score
    </div>

    <div id="mindsafe-score-main" style="cursor:pointer;">
      ${scoreHtml}

      <div style="font-size:12px; font-weight:500; margin-bottom:4px;">
        ${label}
      </div>
    </div>

    <div id="mindsafe-score-details" style="display:none; margin-top:4px; font-size:11px; line-height:1.4;"></div>

    ${reasonsHtml}

    <div style="margin-top:6px; font-size:10px; opacity:0.7;">
      Click the score to see a full breakdown. Based on AI analysis of ${title}. This is informational only and not medical advice.
    </div>
  `;

  if (isNew) {
    container.insertBefore(panel, container.firstChild);
    console.log("[MindSafe] stats panel inserted into right column");
  }

  // Attach click handler to toggle detailed scores
  if (status === "done") {
    const mainEl = panel.querySelector("#mindsafe-score-main");
    const detailsEl = panel.querySelector("#mindsafe-score-details");
    if (mainEl && detailsEl) {
      mainEl.addEventListener("click", () => {
        if (detailsEl.style.display === "none") {
          // Build details view from raw results
          const devScore =
            typeof data.devScore === "number"
              ? `${data.devScore.toFixed(1)}/100`
              : "N/A";
          const brainrot =
            typeof data.brainrotIndex === "number"
              ? `${data.brainrotIndex.toFixed(1)}/100`
              : "N/A";

          const dim =
            data.rawApiResult && data.rawApiResult.dimension_scores
              ? data.rawApiResult.dimension_scores
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
              "<ul style='padding-left:16px; margin:4px 0;'> " +
              Object.keys(prettyNames)
                .map((key) => {
                  // Support both lowercase keys and capitalized keys
                  const rawKey = key;
                  const apiKey = prettyNames[key]; // e.g., "Pacing"
                  const v =
                    typeof dim[rawKey] === "number"
                      ? dim[rawKey]
                      : typeof dim[apiKey] === "number"
                      ? dim[apiKey]
                      : null;
                  const score =
                    typeof v === "number" ? `${v.toFixed(1)}/100` : "N/A";
                  return `<li><b>${prettyNames[key]}:</b> ${score}</li>`;
                })
                .join("") +
              "</ul>";
          } else {
            dimHtml =
              "<div>Detailed dimension scores are not available for this video.</div>";
          }

          detailsEl.innerHTML = `
            <div><b>Overall developmental score:</b> ${devScore}</div>
            <div><b>Brainrot index:</b> ${brainrot}</div>
            ${dimHtml}
          `;
          detailsEl.style.display = "block";
        } else {
          detailsEl.style.display = "none";
        }
      });
    }
  }

  return true;
}

// Ask the background script for whatever the last score is and render it.
// Returns nothing directly; polling logic lives in the interval callback.
function requestAndRenderLatestPanel(intervalRef) {
  const container = findRightColumn();
  if (!container) {
    console.log("[MindSafe] right column not found yet");
    return;
  }

  chrome.runtime.sendMessage({ type: "GET_LAST_SCORE" }, (resp) => {
    if (chrome.runtime.lastError) {
      console.warn(
        "[MindSafe] GET_LAST_SCORE failed:",
        chrome.runtime.lastError
      );
      renderPanel(null);
      return;
    }
    const data = resp && resp.lastScore ? resp.lastScore : null;
    renderPanel(data);

    // Stop polling once we reach a terminal state
    if (data && (data.status === "done" || data.status === "error")) {
      if (intervalRef && intervalRef.id) {
        clearInterval(intervalRef.id);
        intervalRef.id = null;
      }
    }
  });
}

// ====================== INIT ======================

if (isWatchPage(location.href)) {
  console.log("[MindSafe] watch page detected, starting injection + API call");

  // Ask background to start a fresh evaluation for this video
  chrome.runtime.sendMessage(
    {
      type: "NEW_VIDEO",
      videoUrl: location.href,
      title: document.title
    },
    (resp) => {
      if (chrome.runtime.lastError) {
        console.warn(
          "[MindSafe] NEW_VIDEO sendMessage error:",
          chrome.runtime.lastError
        );
        return;
      }
      if (resp && resp.lastScore) {
        const pendingData = resp.lastScore;
        // Render as soon as the right column is ready
        const intervalPending = setInterval(() => {
          if (renderPanel(pendingData)) {
            clearInterval(intervalPending);
          }
        }, 500);
        setTimeout(() => clearInterval(intervalPending), 10000);
      }
    }
  );

  // Poll for updates until we reach a terminal state (done/error)
  const intervalRef = { id: null };
  intervalRef.id = setInterval(() => {
    requestAndRenderLatestPanel(intervalRef);
  }, 2000);

  // Listen for updates when the background finishes analysis
  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg || msg.type !== "SCORE_UPDATED") return;
    if (!isWatchPage(location.href)) return;
    renderPanel(msg.lastScore);
  });
} else {
  console.log("[MindSafe] not a /watch page, doing nothing");
}


