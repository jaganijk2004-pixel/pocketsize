"""
routes/jewelry_planner.py
-------------------------
Jewelry Budget Planner Blueprint.

Routes:
  GET  /jewelry              — render the planner input form
  POST /generate-jewelry     — process form + optional image, call AI, store result
  GET  /jewelry/results      — render the AI recommendation results
"""

import base64

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from services.product_service import get_jewelry_catalog
from services.prompt_builder import build_jewelry_prompt
from services import gemini_service

bp = Blueprint("jewelry", __name__)

VALID_OCCASIONS = {"Wedding", "Festival", "Birthday", "Casual", "Office", "Party"}
VALID_STYLES = {"Traditional", "Modern", "Minimalist", "Statement", "Bohemian"}
VALID_METALS = {"Gold", "Silver", "Rose Gold", "Platinum", "No Preference"}

# Image upload constraints
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@bp.route("/jewelry")
def planner():
    """Render the Jewelry Budget Planner input form."""
    return render_template("jewelry/planner.html")


@bp.route("/generate-jewelry", methods=["POST"])
def generate():
    """
    Process the jewelry planner form submission.

    Expected form fields:
      budget    — total budget (float)
      occasion  — one of VALID_OCCASIONS
      style     — one of VALID_STYLES
      metal     — one of VALID_METALS

    Optional file:
      outfit_image — image file (jpg/jpeg/png/webp, max 5 MB)
                     Read into memory as bytes; never written to disk.
    """
    # ── Parse and validate budget ──────────────────────────────────────────
    try:
        budget = float(request.form.get("budget", 0))
        if budget <= 0:
            raise ValueError("Budget must be positive.")
    except (ValueError, TypeError):
        flash("Please enter a valid budget amount.", "error")
        return redirect(url_for("jewelry.planner"))

    # ── Parse and validate occasion ───────────────────────────────────────
    occasion = request.form.get("occasion", "").strip()
    if occasion not in VALID_OCCASIONS:
        flash("Please select a valid occasion.", "error")
        return redirect(url_for("jewelry.planner"))

    # ── Parse and validate style ──────────────────────────────────────────
    style = request.form.get("style", "").strip()
    if style not in VALID_STYLES:
        flash("Please select a valid style preference.", "error")
        return redirect(url_for("jewelry.planner"))

    # ── Parse metal preference ────────────────────────────────────────────
    metal = request.form.get("metal", "No Preference").strip()
    if metal not in VALID_METALS:
        metal = "No Preference"

    # ── Handle optional image upload ──────────────────────────────────────
    image_bytes = None
    image_mime_type = "image/jpeg"
    has_image = False

    uploaded_file = request.files.get("outfit_image")
    if uploaded_file and uploaded_file.filename:
        # Validate extension
        filename = uploaded_file.filename.lower()
        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            flash(
                "Unsupported image format. Please upload a JPG, PNG, or WebP file.",
                "error",
            )
            return redirect(url_for("jewelry.planner"))

        # Read into memory (never touches disk)
        raw_bytes = uploaded_file.read()

        # Validate size
        if len(raw_bytes) > MAX_IMAGE_SIZE_BYTES:
            flash("Image file is too large. Please upload an image under 5 MB.", "error")
            return redirect(url_for("jewelry.planner"))

        # Determine MIME type from extension
        content_type = uploaded_file.content_type or ""
        image_mime_type = ALLOWED_MIME_TYPES.get(
            content_type, ALLOWED_MIME_TYPES.get(f"image/{ext.lstrip('.')}", "image/jpeg")
        )

        image_bytes = raw_bytes
        has_image = True

    # ── Get filtered jewelry catalog ──────────────────────────────────────
    catalog = get_jewelry_catalog(occasion, style, metal)

    # ── Build prompt and call Gemini ──────────────────────────────────────
    form_data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "metal": metal,
    }
    prompt = build_jewelry_prompt(form_data, catalog, has_image=has_image)
    result = gemini_service.generate_recommendation(
        prompt,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
    )

    # ── Handle AI errors ──────────────────────────────────────────────────
    if result.get("error"):
        flash(f"AI Error: {result.get('message', 'Unknown error')}", "error")
        return redirect(url_for("jewelry.planner"))

    # ── Store result and redirect (image bytes are NOT stored) ────────────
    session["jewelry_result"] = result
    return redirect(url_for("jewelry.results"))


@bp.route("/jewelry/results")
def results():
    """Render the Jewelry Planner AI results page."""
    result = session.pop("jewelry_result", None)
    if not result:
        flash("No results found. Please fill in the planner form first.", "info")
        return redirect(url_for("jewelry.planner"))
    return render_template("jewelry/results.html", result=result)
