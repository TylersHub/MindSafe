chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "NEW_VIDEO") {
    // --- MOCK RESPONSE ---
    const data = {
      videoId: msg.videoId,
      score: Math.floor(Math.random() * 101), // random 0-100
      label: "Highly suitable",
      title: "Demo Video Title",
      reasons: ["Mock reason 1", "Mock reason 2"]
    };

    // Store in chrome.storage.local
    chrome.storage.local.set({ lastScore: data });
  }
});
