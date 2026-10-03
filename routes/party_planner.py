"""
routes/party_planner.py
-----------------------
Party Budget Planner Blueprint.

Routes:
  GET  /party              — render the planner input form
  POST /generate-party     — process form, call AI, store result in session
  GET  /party/results      — render the AI recommendation results
"""

import traceback

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from services.product_service import get_party_catalog
from services.prompt_builder import build_party_prompt
from services import gemini_service

bp = Blueprint("party", __name__)

VALID_EVENT_TYPES = {
    "Birthday",
    "Wedding",
    "Corporate",
    "Anniversary",
    "Casual Gathering",
}

VALID_VENUE_PREFERENCES = {"Indoor", "Outdoor", "No Preference"}


@bp.route("/party")
def planner():
    """Render the Party Budget Planner input form."""
    return render_template("party/planner.html")


@bp.route("/generate-party", methods=["POST"])
def generate():
    """
    Process the party planner form submission.

    Expected form fields:
      budget               — total budget (float)
      guests               — number of guests (int)
      event_type           — one of VALID_EVENT_TYPES
      venue_preference     — one of VALID_VENUE_PREFERENCES
      city                 — optional location text
      special_requirements — optional free-text
    """
    print("\n[PARTY ROUTE] === POST /generate-party received ===")
    print(f"[PARTY ROUTE] Form keys: {list(request.form.keys())}")

    # ── Parse and validate budget ──────────────────────────────────────────
    try:
        budget = float(request.form.get("budget", 0))
        if budget <= 0:
            raise ValueError("Budget must be positive.")
        print(f"[PARTY ROUTE] Budget parsed: {budget}")
    except (ValueError, TypeError) as e:
        print(f"[PARTY ROUTE] Budget parse error: {e}")
        flash("Please enter a valid budget amount.", "error")
        return redirect(url_for("party.planner"))

    # ── Parse and validate guest count ────────────────────────────────────
    try:
        guests = int(request.form.get("guests", 0))
        if guests <= 0:
            raise ValueError("Guest count must be positive.")
        print(f"[PARTY ROUTE] Guests parsed: {guests}")
    except (ValueError, TypeError) as e:
        print(f"[PARTY ROUTE] Guests parse error: {e}")
        flash("Please enter a valid number of guests.", "error")
        return redirect(url_for("party.planner"))

    # ── Parse and validate event type ─────────────────────────────────────
    event_type = request.form.get("event_type", "").strip()
    print(f"[PARTY ROUTE] Event type: '{event_type}'")
    if event_type not in VALID_EVENT_TYPES:
        print(f"[PARTY ROUTE] Invalid event type — redirecting")
        flash("Please select a valid event type.", "error")
        return redirect(url_for("party.planner"))

    # ── Parse venue preference ─────────────────────────────────────────────
    venue_preference = request.form.get("venue_preference", "No Preference").strip()
    if venue_preference not in VALID_VENUE_PREFERENCES:
        venue_preference = "No Preference"
    print(f"[PARTY ROUTE] Venue preference: '{venue_preference}'")

    # ── Optional fields ────────────────────────────────────────────────────
    city = request.form.get("city", "").strip() or "Not specified"
    special_requirements = (
        request.form.get("special_requirements", "").strip() or "None"
    )
    print(f"[PARTY ROUTE] City: '{city}' | Special reqs: '{special_requirements}'")

    # ── Get filtered service catalog ───────────────────────────────────────
    print("[PARTY ROUTE] Calling get_party_catalog ...")
    try:
        catalog = get_party_catalog(event_type)
        print(f"[PARTY ROUTE] Catalog fetched, categories: {list(catalog.keys())}")
    except Exception as e:
        print(f"[PARTY ROUTE] get_party_catalog FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        flash("Internal error loading catalog.", "error")
        return redirect(url_for("party.planner"))

    # ── Build prompt ───────────────────────────────────────────────────────
    print("[PARTY ROUTE] Building prompt ...")
    try:
        form_data = {
            "budget": budget,
            "guests": guests,
            "event_type": event_type,
            "venue_preference": venue_preference,
            "city": city,
            "special_requirements": special_requirements,
        }
        prompt = build_party_prompt(form_data, catalog)
        print(f"[PARTY ROUTE] Prompt built, length={len(prompt)} chars")
        print(f"[PARTY ROUTE] Prompt preview (first 300 chars): {repr(prompt[:300])}")
    except Exception as e:
        print(f"[PARTY ROUTE] build_party_prompt FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        flash("Internal error building prompt.", "error")
        return redirect(url_for("party.planner"))

    # ── Call Gemini ────────────────────────────────────────────────────────
    print("[PARTY ROUTE] Calling gemini_service.generate_recommendation ...")
    result = gemini_service.generate_recommendation(prompt)
    print(f"[PARTY ROUTE] generate_recommendation returned: error={result.get('error')}")

    # ── Handle AI errors ───────────────────────────────────────────────────
    if result.get("error"):
        print(f"[PARTY ROUTE] AI error message: {result.get('message')}")
        flash(f"AI Error: {result.get('message', 'Unknown error')}", "error")
        return redirect(url_for("party.planner"))

    # ── Store result and redirect ──────────────────────────────────────────
    print("[PARTY ROUTE] Success — storing result in session")
    session["party_result"] = result
    return redirect(url_for("party.results"))


@bp.route("/party/results")
def results():
    """Render the Party Planner AI results page."""
    result = session.pop("party_result", None)
    if not result:
        flash("No results found. Please fill in the planner form first.", "info")
        return redirect(url_for("party.planner"))
    return render_template("party/results.html", result=result)
