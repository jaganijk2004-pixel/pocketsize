"""
routes/home_planner.py
----------------------
Home Interior Planner Blueprint.

Routes:
  GET  /home              — render the planner input form
  POST /generate-home     — process form, call AI, store result in session
  GET  /home/results      — render the AI recommendation results
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
import traceback

from services.product_service import get_home_catalog
from services.prompt_builder import build_home_prompt
from services import gemini_service

bp = Blueprint("home", __name__)

# Valid room keys accepted from the form
VALID_ROOMS = {"living_room", "bedroom", "kitchen", "dining_room", "bathroom"}


@bp.route("/home")
def planner():
    """Render the Home Interior Planner input form."""
    return render_template("home/planner.html")


@bp.route("/generate-home", methods=["POST"])
def generate():
    """
    Process the home planner form submission.

    Expected form fields:
      budget          — total budget (float)
      rooms           — one or more room checkboxes (e.g. "living_room", "bedroom")
      {room}_items    — comma-separated item names per room (e.g. "living_room_items")
      {room}_qty_{n}  — quantity for each item (e.g. "living_room_qty_0")
    """
    print("\n[HOME ROUTE] === POST /generate-home received ===")
    print(f"[HOME ROUTE] Form keys: {list(request.form.keys())}")

    # ── Parse budget ───────────────────────────────────────────────────────
    try:
        budget = float(request.form.get("budget", 0))
        if budget <= 0:
            raise ValueError("Budget must be positive.")
        print(f"[HOME ROUTE] Budget parsed: {budget}")
    except (ValueError, TypeError) as e:
        print(f"[HOME ROUTE] Budget parse error: {e}")
        flash("Please enter a valid budget amount.", "error")
        return redirect(url_for("home.planner"))

    # ── Parse selected rooms ───────────────────────────────────────────────
    selected_rooms = request.form.getlist("rooms")
    selected_rooms = [r for r in selected_rooms if r in VALID_ROOMS]
    print(f"[HOME ROUTE] Selected rooms: {selected_rooms}")

    if not selected_rooms:
        print("[HOME ROUTE] No valid rooms selected — redirecting")
        flash("Please select at least one room.", "error")
        return redirect(url_for("home.planner"))

    # ── Parse items and quantities per room ────────────────────────────────
    rooms_data = []
    for room in selected_rooms:
        items_raw = request.form.getlist(f"{room}_items[]")
        quantities_raw = request.form.getlist(f"{room}_quantities[]")
        print(f"[HOME ROUTE] Room '{room}' items_raw={items_raw} qty_raw={quantities_raw}")

        items = []
        for i, item_name in enumerate(items_raw):
            item_name = item_name.strip()
            if not item_name:
                continue
            try:
                qty = int(quantities_raw[i]) if i < len(quantities_raw) else 1
                qty = max(1, qty)
            except (ValueError, IndexError):
                qty = 1
            items.append({"name": item_name, "quantity": qty})

        if not items:
            items = [{"name": "General furnishing and decor", "quantity": 1}]

        rooms_data.append({
            "room_type": room.replace("_", " ").title(),
            "items": items,
        })

    print(f"[HOME ROUTE] rooms_data built: {rooms_data}")

    # ── Get filtered product catalog ───────────────────────────────────────
    print("[HOME ROUTE] Calling get_home_catalog ...")
    try:
        catalog = get_home_catalog(selected_rooms)
        print(f"[HOME ROUTE] Catalog fetched, rooms present: {list(catalog.keys())}")
    except Exception as e:
        print(f"[HOME ROUTE] get_home_catalog FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        flash("Internal error loading catalog.", "error")
        return redirect(url_for("home.planner"))

    # ── Build prompt ───────────────────────────────────────────────────────
    print("[HOME ROUTE] Building prompt ...")
    try:
        form_data = {"budget": budget, "rooms": rooms_data}
        prompt = build_home_prompt(form_data, catalog)
        print(f"[HOME ROUTE] Prompt built, length={len(prompt)} chars")
    except Exception as e:
        print(f"[HOME ROUTE] build_home_prompt FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        flash("Internal error building prompt.", "error")
        return redirect(url_for("home.planner"))

    # ── Call Gemini ────────────────────────────────────────────────────────
    print("[HOME ROUTE] Calling gemini_service.generate_recommendation ...")
    result = gemini_service.generate_recommendation(prompt)
    print(f"[HOME ROUTE] generate_recommendation returned: error={result.get('error')}")

    # ── Handle AI errors ───────────────────────────────────────────────────
    if result.get("error"):
        print(f"[HOME ROUTE] AI error message: {result.get('message')}")
        flash(f"AI Error: {result.get('message', 'Unknown error')}", "error")
        return redirect(url_for("home.planner"))

    # ── Store result and redirect ──────────────────────────────────────────
    print("[HOME ROUTE] Success — storing result in session")
    session["home_result"] = result
    return redirect(url_for("home.results"))


@bp.route("/home/results")
def results():
    """Render the Home Planner AI results page."""
    result = session.pop("home_result", None)
    if not result:
        flash("No results found. Please fill in the planner form first.", "info")
        return redirect(url_for("home.planner"))
    return render_template("home/results.html", result=result)
