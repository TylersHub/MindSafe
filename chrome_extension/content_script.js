// contentScript.js

function getYouTubeVideoId(urlString) {
  try {
    const url = new URL(urlString);

    // Standard YouTube watch URL: https://www.youtube.com/watch?v=VIDEO_ID
    if (url.hostname.includes("youtube.com") && url.pathname === "/watch") {
      return url.searchParams.get("v");
    }

    // Short URL: https://youtu.be/VIDEO_ID
    if (url.hostname === "youtu.be") {
      return url.pathname.slice(1); // remove leading '/'
    }

    // Shorts: https://www.youtube.com/shorts/VIDEO_ID
    if (url.hostname.includes("youtube.com") && url.pathname.startsWith("/shorts/")) {
      const parts = url.pathname.split("/");
      return parts[2] || null;
    }

    // Embed: https://www.youtube.com/embed/VIDEO_ID
    if (url.hostname.includes("youtube.com") && url.pathname.startsWith("/embed/")) {
      const parts = url.pathname.split("/");
      return parts[2] || null;
    }

    // YouTube Kids watch URL:
    // https://www.youtubekids.com/watch?v=VIDEO_ID
    // https://kids.youtube.com/watch?v=VIDEO_ID
    if (
      (url.hostname.includes("youtubekids.com") || url.hostname.includes("kids.youtube.com")) &&
      url.pathname === "/watch"
    ) {
      return url.searchParams.get("v");
    }

    return null;
  } catch (e) {
    return null;
  }
}

function isYouTubeLikeUrl(urlString) {
  try {
    const url = new URL(urlString);
    return (
      url.hostname.includes("youtube.com") ||
      url.hostname === "youtu.be" ||
      url.hostname.includes("youtubekids.com") ||
      url.hostname.includes("kids.youtube.com")
    );
  } catch (e) {
    return false;
  }
}

// Listen for clicks on links pointing to videos
document.addEventListener(
  "click",
  (event) => {
    const anchor = event.target.closest("a");
    if (!anchor || !anchor.href) return;

    const url = anchor.href;
    if (!isYouTubeLikeUrl(url)) return;

    const videoId = getYouTubeVideoId(url);
    if (!videoId) {
      console.log("[ContentScript] Clicked link is not a recognized video URL:", url);
      return;
    }

    console.log("[ContentScript] Sending NEW_VIDEO:", { videoId, videoUrl: url });
    // Expose last clicked video info on the page for debugging (temporary)
    try {
      window.__MINDSAFE_LAST_CLICKED = { videoId, videoUrl: url, title: document.title || 'Video', time: Date.now() };
    } catch (e) {
      // ignore if page blocks writes
    }

    chrome.runtime.sendMessage({
      type: "NEW_VIDEO",
      videoId,
      videoUrl: url,
      title: document.title || "Video",
      copied: false
    });
  },
  true // capture phase: catch early
);
