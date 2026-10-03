"""
prompt_builder.py
-----------------
Builds structured AI prompts for each of the three planners.

Each function:
  1. Accepts the user's form data and a pre-filtered catalog from product_service.py
  2. Constructs a detailed prompt that instructs Gemini to:
     - Stay within the user's total budget (strict constraint)
     - Recommend ONLY items from the provided catalog
     - Return a specific JSON structure (schema embedded in prompt)
     - Label all prices as "Estimated / Demo Price"
  3. Returns the prompt string, ready to pass to gemini_service.generate_recommendation()
"""

import json


# ── Shared instruction fragments ───────────────────────────────────────────

_BUDGET_RULE = (
    "CRITICAL RULE: The sum of all recommended prices MUST NOT exceed the total budget. "
    "If the budget is too low for meaningful recommendations, set 'budget_too_low' to true "
    "and suggest a minimum budget in 'suggested_minimum_budget'. "
    "Otherwise set 'budget_too_low' to false."
)

_CATALOG_RULE = (
    "IMPORTANT: You MUST recommend items ONLY from the catalog provided below. "
    "Do NOT invent or suggest products that are not in the catalog. "
    "Use the exact 'id', 'name', and 'platform' fields from the catalog entries."
)

_PRICE_LABEL_RULE = (
    "All prices are demo/estimated data — NOT from live APIs. "
    "Always include the field: \"price_note\": \"Estimated / Demo Price – Not from Live API\""
)

_JSON_RULE = (
    "Return ONLY valid JSON — no markdown, no code fences, no explanation text. "
    "Your entire response must be a single JSON object matching the schema below exactly."
)


# ── Home Interior Prompt ───────────────────────────────────────────────────

def build_home_prompt(form_data: dict, catalog: dict) -> str:
    """
    Build the prompt for the Home Interior Planner.

    form_data keys expected:
        budget        (float)  — total budget in INR
        rooms         (list)   — list of room dicts, each with:
                                  'room_type' (str), 'items' (list of dicts with 'name', 'quantity')

    catalog: dict returned by product_service.get_home_catalog()
    """
    budget = form_data.get("budget", 0)
    rooms = form_data.get("rooms", [])

    rooms_description = json.dumps(rooms, ensure_ascii=False, indent=2)
    catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)

    schema = """{
  "total_budget": <number>,
  "total_estimated_cost": <number>,
  "remaining_budget": <number>,
  "budget_too_low": <boolean>,
  "suggested_minimum_budget": <number or null>,
  "price_note": "Estimated / Demo Price – Not from Live API",
  "rooms": [
    {
      "room": "<room type string>",
      "allocated_budget": <number>,
      "estimated_spend": <number>,
      "items": [
        {
          "item_id": "<id from catalog>",
          "name": "<name from catalog>",
          "category": "<category from catalog>",
          "platform": "<platform from catalog>",
          "quantity": <number>,
          "unit_price": <number>,
          "total_price": <number>,
          "reason": "<one sentence why this item fits the room and budget>"
        }
      ]
    }
  ]
}"""

    prompt = f"""You are PocketSmart AI, a budget-aware home interior planning assistant.

{_BUDGET_RULE}
{_CATALOG_RULE}
{_PRICE_LABEL_RULE}
{_JSON_RULE}

## User Request
- Total Budget: ₹{budget:,.0f} INR
- Rooms and items needed:
{rooms_description}

## Available Product Catalog
{catalog_json}

## Instructions
1. Allocate the total budget proportionally across the requested rooms based on the number and type of items needed.
2. For each room, select the most suitable items from the catalog that fit within the allocated budget.
3. If multiple quantities are requested for an item, multiply unit_price by quantity to get total_price.
4. Prefer items that match the room context and provide good value.
5. The sum of all total_price values across all rooms must not exceed ₹{budget:,.0f}.
6. Set remaining_budget = total_budget - total_estimated_cost.

## Output JSON Schema
{schema}
"""
    return prompt


# ── Party Budget Prompt ────────────────────────────────────────────────────

def build_party_prompt(form_data: dict, catalog: dict) -> str:
    """
    Build the prompt for the Party Budget Planner.

    form_data keys expected:
        budget               (float)  — total budget in INR
        guests               (int)    — number of guests
        event_type           (str)    — Birthday / Wedding / Corporate / Anniversary / Casual Gathering
        venue_preference     (str)    — Indoor / Outdoor / No Preference
        city                 (str)    — optional location
        special_requirements (str)    — optional free-text

    catalog: dict returned by product_service.get_party_catalog()
    """
    budget = form_data.get("budget", 0)
    guests = form_data.get("guests", 0)
    event_type = form_data.get("event_type", "")
    venue_preference = form_data.get("venue_preference", "No Preference")
    city = form_data.get("city", "Not specified")
    special_requirements = form_data.get("special_requirements", "None")

    catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)

    schema = """{
  "total_budget": <number>,
  "total_estimated_cost": <number>,
  "remaining_budget": <number>,
  "budget_too_low": <boolean>,
  "suggested_minimum_budget": <number or null>,
  "price_note": "Estimated / Demo Price – Not from Live API",
  "event_summary": "<brief one-line summary of the event>",
  "categories": [
    {
      "category": "<Catering | Decoration | Entertainment | Venue>",
      "allocated_budget": <number>,
      "estimated_spend": <number>,
      "recommendation": {
        "id": "<id from catalog>",
        "name": "<name from catalog>",
        "platform": "<platform from catalog>",
        "estimated_price": <number>,
        "pricing_detail": "<e.g. '₹350 x 50 guests = ₹17,500' or flat fee>",
        "note": "<one sentence on why this suits the event type and budget>"
      }
    }
  ]
}"""

    prompt = f"""You are PocketSmart AI, a budget-aware party and event planning assistant.

{_BUDGET_RULE}
{_CATALOG_RULE}
{_PRICE_LABEL_RULE}
{_JSON_RULE}

## User Request
- Total Budget: ₹{budget:,.0f} INR
- Number of Guests: {guests}
- Event Type: {event_type}
- Venue Preference: {venue_preference}
- City / Location: {city}
- Special Requirements: {special_requirements}

## Available Services Catalog
{catalog_json}

## Instructions
1. Allocate the total budget across categories: Catering, Decoration, Entertainment, and (if relevant) Venue.
2. Catering is typically the largest expense — allocate proportionally based on guest count.
3. For catering items with price_per_person, calculate: price_per_person × {guests} guests = total catering cost.
4. Select ONE recommendation per category from the catalog that best fits the event type and budget.
5. If venue_preference is "No Preference" or the user seems to be hosting at home, you may skip the Venue category.
6. The sum of all estimated_spend values must not exceed ₹{budget:,.0f}.
7. Set remaining_budget = total_budget - total_estimated_cost.
8. Tailor suggestions to the event type: {event_type}.

## Output JSON Schema
{schema}
"""
    return prompt


# ── Jewelry Budget Prompt ──────────────────────────────────────────────────

def build_jewelry_prompt(form_data: dict, catalog: list, has_image: bool = False) -> str:
    """
    Build the prompt for the Jewelry Budget Planner.

    form_data keys expected:
        budget    (float)  — total budget in INR
        occasion  (str)    — Wedding / Festival / Birthday / Casual / Office / Party
        style     (str)    — Traditional / Modern / Minimalist / Statement / Bohemian
        metal     (str)    — Gold / Silver / Rose Gold / Platinum / No Preference

    catalog: list returned by product_service.get_jewelry_catalog()
    has_image: bool — True if an outfit image was uploaded (sent separately as multimodal)
    """
    budget = form_data.get("budget", 0)
    occasion = form_data.get("occasion", "")
    style = form_data.get("style", "")
    metal = form_data.get("metal", "No Preference")

    catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)

    image_instruction = ""
    if has_image:
        image_instruction = """
## Outfit Image Analysis
An outfit image has been provided. Please:
1. Analyze the outfit's dominant colors, fabric style, and overall aesthetic.
2. Use this analysis to improve jewelry color and style matching.
3. Include a brief outfit_analysis field describing what you observe (colors, style).
4. DO NOT attempt to identify the person in the image.
5. DO NOT infer or comment on any personal, demographic, or sensitive information.
"""
    else:
        image_instruction = """
## No Outfit Image
No outfit image was provided. Base recommendations on the occasion, style preference, and metal preference only.
Set outfit_analysis to null.
"""

    schema = """{
  "total_budget": <number>,
  "total_estimated_cost": <number>,
  "remaining_budget": <number>,
  "budget_too_low": <boolean>,
  "suggested_minimum_budget": <number or null>,
  "price_note": "Estimated / Demo Price – Not from Live API",
  "outfit_analysis": "<brief description of outfit colors and style, or null>",
  "recommendations": [
    {
      "id": "<id from catalog>",
      "name": "<name from catalog>",
      "type": "<type from catalog>",
      "platform": "<platform from catalog>",
      "estimated_price": <number>,
      "metal": "<metal from catalog>",
      "color_match": "<one sentence on how colors/materials complement the outfit or occasion>",
      "occasion_match": "<one sentence on why this suits the occasion>"
    }
  ]
}"""

    prompt = f"""You are PocketSmart AI, a budget-aware jewelry recommendation assistant.

{_BUDGET_RULE}
{_CATALOG_RULE}
{_PRICE_LABEL_RULE}
{_JSON_RULE}

## User Request
- Total Jewelry Budget: ₹{budget:,.0f} INR
- Occasion: {occasion}
- Style Preference: {style}
- Metal Preference: {metal}
{image_instruction}

## Available Jewelry Catalog
{catalog_json}

## Instructions
1. Recommend 2–4 jewelry pieces from the catalog that together stay within ₹{budget:,.0f}.
2. Try to suggest a complete, coordinated look (e.g., necklace + earrings, or a statement set).
3. Prioritise items matching the occasion: {occasion} and style: {style}.
4. If metal preference is not "No Preference", prefer items with metal: {metal}.
5. The sum of all estimated_price values must not exceed ₹{budget:,.0f}.
6. Set remaining_budget = total_budget - total_estimated_cost.
7. For each recommendation, explain how it matches the outfit (if image provided) or the occasion.

## Output JSON Schema
{schema}
"""
    return prompt
