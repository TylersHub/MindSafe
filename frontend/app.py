from flask import Flask, render_template

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
