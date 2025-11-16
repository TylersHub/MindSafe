// background.js (MV3 service worker)

// In-memory fallback so popup or content script can read
// the latest value even if storage fails.
let inMemoryLastScore = null;

// Helper: turn 1–10 score into a label + reasons
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
        "Mostly okay",
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

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // 1) NEW_VIDEO: content script detected a video
  if (msg.type === "NEW_VIDEO") {
    console.log("Background: NEW_VIDEO received", msg, "from", sender);

    // Random score 1–10 for now (placeholder)
    const score = Math.floor(Math.random() * 10) + 1;
    const { label, reasons } = labelForScore(score);

    const data = {
      videoId: msg.videoId || null,
      videoUrl: msg.videoUrl || null,
      title: msg.title || "Video",
      score,      // 1–10
      label,      // "Highly suitable", etc.
      reasons,    // array of strings
      copied: !!msg.copied,
      copiedAt: msg.copied ? Date.now() : null,
      receivedAt: Date.now()
    };

    // Keep in-memory fallback
    inMemoryLastScore = data;

    // Persist in chrome.storage.local (nice for popup / reloads)
    chrome.storage.local.set({ lastScore: data }, () => {
      if (chrome.runtime.lastError) {
        console.error(
          "Background: chrome.storage.local.set failed",
          chrome.runtime.lastError
        );
      } else {
        console.log("Background: lastScore stored");
      }
    });

    // Send the score back so the content script can render immediately
    sendResponse({ ok: true, lastScore: data });
    return true; // async response allowed
  }

  // 2) GET_LAST_SCORE: popup or content script asking for whatever we last stored
  if (msg.type === "GET_LAST_SCORE") {
    console.log("Background: GET_LAST_SCORE");

    if (inMemoryLastScore) {
      sendResponse({ lastScore: inMemoryLastScore });
      return true;
    }

    chrome.storage.local.get("lastScore", (data) => {
      if (chrome.runtime.lastError) {
        console.error(
          "Background: chrome.storage.local.get failed",
          chrome.runtime.lastError
        );
        sendResponse({
          lastScore: null,
          error: chrome.runtime.lastError.message
        });
      } else {
        sendResponse({
          lastScore: data.lastScore || null
        });
      }
    });

    return true; // indicate async response
  }
});
