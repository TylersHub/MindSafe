(function() {
  function getVideoId() {
    const url = new URL(location.href);
    return url.searchParams.get("v");
  }

  function sendVideoId(videoId) {
    if (!videoId) return;
    chrome.runtime.sendMessage({ type: "NEW_VIDEO", videoId });
  }

  let lastVideoId = null;

  function checkVideo() {
    const vid = getVideoId();
    if (vid && vid !== lastVideoId) {
      lastVideoId = vid;
      sendVideoId(vid);
    }
  }

  checkVideo(); // initial check

  // Detect SPA navigation
  let lastHref = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== lastHref) {
      lastHref = location.href;
      checkVideo();
    }
  });
  observer.observe(document, { childList: true, subtree: true });
})();

