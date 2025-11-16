from pathlib import Path
from io import BytesIO
import zipfile

from flask import Flask, render_template, send_file


# This Flask app serves the marketing/frontend pages.
# It expects templates/ and static/ to live alongside this file.
BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(__name__)  # looks for templates/ and static/ in the same folder as app.py


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/loader")
def loader():
    return render_template("loader.html")
@app.route("/data")
def data():
    return render_template("data.html")


@app.route("/download-extension")
def download_extension():
    """
    Create a ZIP of the chrome_extension folder on the fly and return it.

    This lets the user click a single download button on the frontend page
    and receive the unpacked Chrome extension as a zip file.
    """
    extension_dir = BASE_DIR / "chrome_extension"
    if not extension_dir.exists():
        return (
            "chrome_extension folder not found on server",
            500,
            {"Content-Type": "text/plain"},
        )

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in extension_dir.rglob("*"):
            if path.is_file():
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
    app.run(host="0.0.0.0", port=5000, debug=True)
