// background.js (MV3 service worker)
//
// This now calls the local MindSafe API (ai-agents/api.py) to get
// REAL evaluation scores for the current YouTube video, instead of
// generating random mock data.
//
// API assumptions:
//   - ai-agents Flask API is running on http://localhost:5001
//   - GET /evaluate?url=YOUTUBE_URL&age=AGE returns either:
//       { dev_score, brainrot_index, ... }
//     or
//       { overall_scores: { development_score, brainrot_index }, ... }
//
const API_BASE_URL = "http://localhost:5001";
const DEFAULT_CHILD_AGE = 4; // years

// In-memory fallback so popup or content script can read
// the latest value even if storage fails.
let inMemoryLastScore = null;

// Helper: map 0–100 dev score to 1–10 rating
function devScoreToTenPoint(devScore) {
  if (typeof devScore !== "number" || Number.isNaN(devScore)) {
    return null;
  }
  const clamped = Math.max(0, Math.min(100, devScore));
  return Math.max(1, Math.min(10, Math.round(clamped / 10)));
}

// Helper: turn a 1–10 score into a label + reasons
function labelForScore(score) {
  if (typeof score !== "number") {
    return {
      label: "Analysis pending",
      reasons: ["The video is being analyzed by MindSafe."]
    };
  }
  if (score >= 8) {
    return {
      label: "Highly suitable",
      reasons: [
        "Calm and developmentally supportive content",
        "Low risk for negative emotional impact",
        "Aligns well with healthy screen-time habits"
      ]
    };
  } else if (score >= 5) {
    return {
      label: "Moderately suitable",
      reasons: [
        "Mostly appropriate but with some mild concerns",
        "Best viewed with some parental awareness",
        "Context matters more for younger children"
      ]
    };
  }
  return {
    label: "Not recommended",
    reasons: [
      "May be overstimulating or emotionally intense",
      "Themes might be confusing or stressful for young kids",
      "Consider more developmentally supportive content"
    ]
  };
}

// Call the MindSafe API to evaluate a video URL in the background.
// We do NOT hold the sendResponse callback open; instead we:
//   1) store a 'pending' state immediately
//   2) fire this async function
//   3) when it returns, update storage + notify content scripts
async function evaluateVideoWithApi(videoUrl, childAge, meta) {
  const url = new URL("/evaluate", API_BASE_URL);
  url.searchParams.set("url", videoUrl);
  url.searchParams.set("age", String(childAge));

  console.log("[MindSafe BG] Calling API:", url.toString());

  try {
    const controller = new AbortController();
    const timeoutMs = 1000 * 60 * 15; // up to 15 minutes
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const resp = await fetch(url.toString(), {
      method: "GET",
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!resp.ok) {
      throw new Error(`API error ${resp.status} ${resp.statusText}`);
    }

    const data = await resp.json();
    console.log("[MindSafe BG] API response:", data);

    // Extract scores from either API shape
    let devScore =
      typeof data.dev_score === "number"
        ? data.dev_score
        : data.overall_scores && typeof data.overall_scores.development_score === "number"
        ? data.overall_scores.development_score
        : null;

    let brainrot =
      typeof data.brainrot_index === "number"
        ? data.brainrot_index
        : data.overall_scores && typeof data.overall_scores.brainrot_index === "number"
        ? data.overall_scores.brainrot_index
        : null;

    const tenPointScore = devScoreToTenPoint(devScore);
    const labelMeta = labelForScore(tenPointScore);

    const enriched = {
      ...meta,
      status: "done",
      videoUrl,
      childAge,
      devScore,
      brainrotIndex: brainrot,
      tenPointScore,
      label: labelMeta.label,
      reasons: labelMeta.reasons,
      rawApiResult: data,
      receivedAt: Date.now()
    };

    inMemoryLastScore = enriched;
    chrome.storage.local.set({ lastScore: enriched }, () => {
      if (chrome.runtime.lastError) {
        console.error(
          "[MindSafe BG] chrome.storage.local.set failed",
          chrome.runtime.lastError
        );
      } else {
        console.log("[MindSafe BG] Stored final evaluation in lastScore");
      }
    });

    // Notify all YouTube / YouTube Kids tabs that a fresh score is available
    chrome.tabs.query(
      {
        url: [
          "*://www.youtube.com/*",
          "*://youtu.be/*",
          "*://www.youtubekids.com/*",
          "*://kids.youtube.com/*"
        ]
      },
      (tabs) => {
        for (const tab of tabs) {
          chrome.tabs.sendMessage(tab.id, {
            type: "SCORE_UPDATED",
            lastScore: enriched
          });
        }
      }
    );
  } catch (err) {
    console.error("[MindSafe BG] Evaluation API call failed:", err);

    const errorResult = {
      ...meta,
      status: "error",
      videoUrl,
      childAge,
      error: err && err.message ? err.message : String(err),
      receivedAt: Date.now()
    };

    inMemoryLastScore = errorResult;
    chrome.storage.local.set({ lastScore: errorResult }, () => {
      if (chrome.runtime.lastError) {
        console.error(
          "[MindSafe BG] chrome.storage.local.set failed after error",
          chrome.runtime.lastError
        );
      }
    });

    chrome.tabs.query(
      {
        url: [
          "*://www.youtube.com/*",
          "*://youtu.be/*",
          "*://www.youtubekids.com/*",
          "*://kids.youtube.com/*"
        ]
      },
      (tabs) => {
        for (const tab of tabs) {
          chrome.tabs.sendMessage(tab.id, {
            type: "SCORE_UPDATED",
            lastScore: errorResult
          });
        }
      }
    );
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // 1) NEW_VIDEO: content script detected a video
  if (msg.type === "NEW_VIDEO") {
    console.log("[MindSafe BG] NEW_VIDEO received", msg, "from", sender);

    const videoUrl = msg.videoUrl || null;
    const title = msg.title || "Video";
    const childAge =
      typeof msg.childAge === "number" ? msg.childAge : DEFAULT_CHILD_AGE;

    if (!videoUrl) {
      sendResponse({
        ok: false,
        error: "Missing videoUrl in NEW_VIDEO message"
      });
      return true;
    }

    // Store a pending state immediately so popup / panel can show something
    const pending = {
      videoId: msg.videoId || null,
      videoUrl,
      title,
      childAge,
      status: "pending",
      devScore: null,
      brainrotIndex: null,
      tenPointScore: null,
      label: "Analysis pending",
      reasons: ["The video is being analyzed by MindSafe."],
      startedAt: Date.now()
    };

    inMemoryLastScore = pending;
    chrome.storage.local.set({ lastScore: pending }, () => {
      if (chrome.runtime.lastError) {
        console.error(
          "[MindSafe BG] chrome.storage.local.set failed (pending)",
          chrome.runtime.lastError
        );
      }
    });

    // Fire-and-forget the actual evaluation
    evaluateVideoWithApi(videoUrl, childAge, {
      videoId: msg.videoId || null,
      title
    });

    // Respond quickly; we don't keep sendResponse open for minutes
    sendResponse({ ok: true, lastScore: pending });
    return true;
  }

  // 2) GET_LAST_SCORE: popup or content script asking for whatever we last stored
  if (msg.type === "GET_LAST_SCORE") {
    console.log("[MindSafe BG] GET_LAST_SCORE");

    if (inMemoryLastScore) {
      sendResponse({ lastScore: inMemoryLastScore });
      return true;
    }

    chrome.storage.local.get("lastScore", (data) => {
      if (chrome.runtime.lastError) {
        console.error(
          "[MindSafe BG] chrome.storage.local.get failed",
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

    return true;
  }
});
