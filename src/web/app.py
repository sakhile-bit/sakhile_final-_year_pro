"""
Landing-page web server for the Zambia Digital Hygiene Certification Program.

This minimal Flask app serves the public marketing/download page.
The full assessment platform (Phase 2) lives in app_full.py.

Routes:
    /           – Landing / marketing page
    /download   – Redirects to the latest .exe on GitHub Releases
    /verify/<id>– Certificate verification lookup
    /about      – About the program
"""

import os
from flask import Flask, render_template, redirect, request, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "landing-page-secret")

# GitHub Releases URL — update when a release is published
DOWNLOAD_URL = os.environ.get(
    "DOWNLOAD_URL",
    "https://github.com/sakhile-bit/sakhile_final-_year_pro/releases/latest/download/ZambiaDigitalHygiene.exe",
)


def create_app():
    return app


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", download_url=DOWNLOAD_URL)


@app.route("/download")
def download():
    """Redirect to the latest Windows .exe on GitHub Releases."""
    return redirect(DOWNLOAD_URL)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/verify/<cert_id>")
def verify(cert_id):
    """
    Public certificate verification endpoint.
    Phase 2 will query the database; for now returns a placeholder.
    """
    # TODO Phase 2: query Certificate table
    return render_template("verify.html", cert_id=cert_id, verified=False)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
