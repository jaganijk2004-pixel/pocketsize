# PocketSmart AI 💰

A GenAI-powered budget recommendation system built with Flask and Google Gemini 1.5 Flash.
Plan home interiors, events, and jewelry purchases — all within your budget.

> ⚠️ **Demo Mode:** All prices are estimated/demo data and are **not retrieved from live APIs**.

---

## Features

| Planner | What it does | Platforms |
|---|---|---|
| 🏠 **Home Interior Planner** | Recommends furniture and decor per room | IKEA, Amazon, Flipkart |
| 🎉 **Party Budget Planner** | Allocates budget across catering, decor, entertainment, venue | Swiggy, Zomato, OYO |
| 💍 **Jewelry Budget Planner** | Matches jewelry to outfit, occasion, and budget (supports outfit image upload) | Amazon, Flipkart |

---

## Local Setup

### Prerequisites

- Python 3.10 or later
- A Google Gemini API key ([Get one free at Google AI Studio](https://aistudio.google.com/app/apikey))

### Steps

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd pocketsize
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Copy `.env.example` to `.env` and fill in the values:
```bash
cp .env.example .env
```

Then edit `.env`:
```
GEMINI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=a_long_random_secret_string
GEMINI_MODEL=gemini-1.5-flash
FLASK_DEBUG=True
PORT=5000
```

**5. Run the application**
```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | — | Google Gemini API key |
| `FLASK_SECRET_KEY` | ✅ Yes | — | Flask session signing key (use a long random string) |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model name |
| `FLASK_DEBUG` | No | `True` | Enable Flask debug mode |
| `PORT` | No | `5000` | Port for local development |

---

## Project Structure

```
pocketsize/
├── app.py                    # Flask entry point, Blueprint registration
├── config.py                 # Environment variable loading
├── requirements.txt          # Python dependencies
├── Procfile                  # For Render / gunicorn deployment
├── .env.example              # Environment variable template
│
├── services/
│   ├── gemini_service.py     # Gemini API wrapper (text + multimodal)
│   ├── product_service.py    # Mock dataset loader with filtering
│   └── prompt_builder.py     # Structured AI prompt builders
│
├── data/
│   ├── home_products.json    # Mock home furniture/decor catalog
│   ├── party_services.json   # Mock party vendor/service catalog
│   └── jewelry_products.json # Mock jewelry product catalog
│
├── routes/
│   ├── home_planner.py       # /home, /generate-home, /home/results
│   ├── party_planner.py      # /party, /generate-party, /party/results
│   └── jewelry_planner.py    # /jewelry, /generate-jewelry, /jewelry/results
│
├── templates/
│   ├── base.html             # Base layout (nav, footer, flash messages)
│   ├── index.html            # Landing page
│   ├── home/                 # Home planner form + results
│   ├── party/                # Party planner form + results
│   ├── jewelry/              # Jewelry planner form + results
│   └── errors/               # 404 and 500 error pages
│
└── static/
    ├── css/styles.css        # Global responsive stylesheet
    └── js/                   # Per-planner JavaScript (home, party, jewelry)
```

---

## How It Works

1. **User fills in the planner form** — budget, preferences, and optionally an outfit image (jewelry planner).
2. **Flask route parses the form** and calls the product service to get a filtered catalog.
3. **Prompt builder** constructs a structured prompt embedding the catalog and budget constraints.
4. **Gemini 1.5 Flash** processes the prompt (and optional image) and returns a JSON recommendation plan.
5. **Results page** renders the plan with a budget summary bar, platform badges, and demo price labels.

---

## AI Budget Enforcement

The AI is explicitly instructed that:
- Total recommended costs must **never exceed** the user's budget.
- All prices must be labelled as **"Estimated / Demo Price – Not from Live API"**.
- If the budget is too low, it must flag this and suggest a minimum.

---

## Image Upload (Jewelry Planner)

- Accepted formats: JPG, JPEG, PNG, WebP
- Maximum size: 5 MB
- The image is sent **directly to Gemini as multimodal input** and is **never written to disk**.
- Gemini analyses the outfit's colors and style only. **No person identification is performed.**

---

## Extending to Real APIs

The `services/product_service.py` module is the **only** file that reads from the mock dataset.
To integrate real APIs (Amazon, Flipkart, etc.), replace the function bodies in `product_service.py`
with real API calls. The routes, prompt builders, and templates do not need to change.

---

## Deployment to Render

1. Push the project to a GitHub repository.
2. Create a new **Web Service** on [Render](https://render.com/).
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `gunicorn app:app`
5. Add all environment variables from `.env.example` in the Render dashboard.
6. Set `FLASK_DEBUG=False` in production.

---

## Tech Stack

- **Backend:** Python 3.10+, Flask 3.0, google-generativeai 0.7
- **AI:** Google Gemini 1.5 Flash (configurable via `GEMINI_MODEL`)
- **Frontend:** HTML5, CSS3 (custom properties, CSS Grid/Flexbox), Vanilla JavaScript
- **Data:** JSON mock catalogs (home, party, jewelry)
- **Deployment:** Gunicorn + Render (or any WSGI host)

---

## License

This project was built as a Naan Mudhalvan academic project. Demo data only — not for commercial use.
