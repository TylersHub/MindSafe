chrome.storage.local.get("lastScore", (data) => {
  const r = data.lastScore;
  const resultDiv = document.getElementById("result");

  if (!r) {
    resultDiv.innerText = "No video analyzed yet.";
    return;
  }

  resultDiv.innerHTML = `
    <div><b>Score:</b> ${r.score}/100</div>
    <div><b>Rating:</b> ${r.label}</div>
    <div><b>Title:</b> ${r.title}</div>
    <div><b>Reasons:</b> ${r.reasons.join(", ")}</div>
  `;
});
