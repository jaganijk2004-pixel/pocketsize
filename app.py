"""
app.py
------
PocketSmart AI — Flask application entry point.
Registers all route Blueprints and configures the session.
"""

from flask import Flask, render_template
import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# ── Register Blueprints ────────────────────────────────────────────────────
from routes.home_planner import bp as home_bp
from routes.party_planner import bp as party_bp
from routes.jewelry_planner import bp as jewelry_bp

app.register_blueprint(home_bp)
app.register_blueprint(party_bp)
app.register_blueprint(jewelry_bp)


# ── Landing page ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── Error handlers ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ── Dev server entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(
        debug=config.FLASK_DEBUG,
        port=config.PORT,
    )
