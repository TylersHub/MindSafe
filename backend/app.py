from pathlib import Path
from io import BytesIO
import zipfile

from flask import Flask, render_template, send_file


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


@app.route("/download-extension")
def download_extension():
    """
    Create a ZIP of the chrome_extension folder on the fly and return it.

    This lets the user click a single download button on the marketing site
    and receive the unpacked Chrome extension as a zip file.
    """
    extension_dir = BASE_DIR / "chrome_extension"
    if not extension_dir.exists():
        # Fail gracefully if the folder is missing
        return (
            "chrome_extension folder not found on server",
            500,
            {"Content-Type": "text/plain"},
        )

    # Build an in-memory ZIP so we don't have to touch the filesystem.
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in extension_dir.rglob("*"):
            if path.is_file():
                # Ensure everything is nested under a top-level chrome_extension/ folder
                arcname = Path("chrome_extension") / path.relative_to(extension_dir)
                zf.write(path, arcname)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="mindsafe-chrome-extension.zip",
    )


if __name__ == "__main__":
    # Run on a separate port to avoid clashing with the ai-agents API (5001).
    app.run(debug=True, host="0.0.0.0", port=8000)


