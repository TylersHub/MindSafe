from pathlib import Path

from flask import Flask, render_template


BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "frontend" / "static"),
    template_folder=str(BASE_DIR / "frontend" / "templates"),
)


@app.route("/")
def index():
    """Serve the marketing landing page."""
    return render_template("index.html")


@app.route("/templates/form.html")
def form_page():
    """
    Serve the demo form page.

    Note: The frontend JS on this page currently talks to Gemini via Google APIs.
    When you're ready, we can repoint it to your local MindSafe API at
    http://localhost:5001/evaluate.
    """
    return render_template("form.html")


if __name__ == "__main__":
    # Run on a separate port to avoid clashing with the ai-agents API (5001).
    app.run(debug=True, host="0.0.0.0", port=8000)


