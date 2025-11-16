// contentScript.js – MindSafe stats card in YouTube / YouTube Kids right column
// NO chrome.runtime usage – just DOM + random score

console.log("[MindSafe SIMPLE] content script loaded on", location.href);

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

// ====================== SCORING HELPER (1–10) ======================

function labelForScore(score) {
  if (score >= 8) {
    return {
      label: "Highly suitable",
      reasons: [
        "Calm content",
        "Low risk themes",
        "Generally supportive tone"
      ]
    };
  } else if (score >= 5) {
    return {
      label: "Moderately suitable",
      reasons: [
        "Mostly okay overall",
        "Some mildly concerning elements",
        "Context matters for younger kids"
      ]
    };
  } else {
    return {
      label: "Not recommended",
      reasons: [
        "Potentially stressful or negative themes",
        "May not be appropriate for young children"
      ]
    };
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

// ====================== PANEL CREATION + RENDER ======================

function insertOrUpdatePanel() {
  const container = findRightColumn();
  if (!container) {
    console.log("[MindSafe SIMPLE] right column not found yet");
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

  // Random score 1–10 each time panel is created (for now)
  const score = Math.floor(Math.random() * 10) + 1;
  const { label, reasons } = labelForScore(score);

  panel.innerHTML = `
    <div style="font-size:11px; font-weight:600; opacity:0.8; margin-bottom:4px;">
      MindSafe Content Score
    </div>

    <div style="display:flex; align-items:baseline; gap:6px; margin-bottom:4px;">
      <span style="font-size:26px; font-weight:700;">${score}</span>
      <span style="font-size:12px; opacity:0.8;">/ 10</span>
    </div>

    <div style="font-size:12px; font-weight:500; margin-bottom:4px;">
      ${label}
    </div>

    <ul style="padding-left:18px; margin:0; font-size:11px;">
      ${reasons.map((r) => `<li>${r}</li>`).join("")}
    </ul>
  `;

  container.insertBefore(panel, container.firstChild);

  if (isNew) {
    console.log("[MindSafe SIMPLE] stats panel inserted into right column");
  } else {
    console.log("[MindSafe SIMPLE] stats panel updated");
  }

  return true;
}

// ====================== INIT (MATCHES TEST SCRIPT BEHAVIOR) ======================

if (isWatchPage(location.href)) {
  console.log("[MindSafe SIMPLE] watch page detected, starting injection poll");

  // Poll until the right column exists, just like the test script
  const interval = setInterval(() => {
    if (insertOrUpdatePanel()) {
      clearInterval(interval);
    }
  }, 500);

  // Stop polling after 10 seconds just in case
  setTimeout(() => clearInterval(interval), 10000);
} else {
  console.log("[MindSafe SIMPLE] not a /watch page, doing nothing");
}
