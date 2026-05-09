# SHL Conversational Assessment Recommender

This project is a FastAPI service for recommending SHL Individual Test Solutions through a short conversation. It was built for the SHL Research Intern AI take-home task.

The service has two endpoints:

- `GET /health` returns `{"status":"ok"}`
- `POST /chat` accepts the full message history and returns the next reply with optional recommendations

The API is stateless. It does not store conversation sessions. Every response follows the required schema.

## Why this design

The assignment is not just a search problem. A recruiter may start with a vague requirement, add more details later, or ask for a comparison. So the app uses a small conversation layer before retrieval.

The logic is intentionally simple and defendable:

1. Read the full message history.
2. Check whether the user is asking something outside SHL assessment selection.
3. Ask a clarification question if the hiring need is still vague.
4. Search the local SHL catalog when enough context exists.
5. Return only assessment names and URLs that exist in the catalog data.

Gemini is optional. The core recommendation logic works without an API key. When `GEMINI_API_KEY` is available, Gemini is only used to polish the reply text, not to invent catalog items.

## Project structure

```text
app/
  main.py              FastAPI endpoints
  models.py            Pydantic request and response schema
  conversation.py      intent checks, clarification, refinement and comparison handling
  retrieval.py         semantic + keyword retrieval
  catalog_loader.py    loads scraped catalog with a small fallback catalog
  prompts.py           LLM guardrails
scraper/
  scrape_catalog.py    scraper for SHL product catalog
requirements.txt
Procfile
runtime.txt
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

Optional Gemini setup:

```bash
copy .env.example .env
# Add GEMINI_API_KEY in .env if you want polished replies
```

## Build the catalog

Run this once before deployment:

```bash
python scraper/scrape_catalog.py
```

It writes the catalog to:

```text
data/shl_catalog.json
```

The app has a small fallback catalog so local testing still works if scraping is blocked, but for final submission the scraped catalog should be used.

## Run locally

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/health
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Hiring a mid-level Java developer who works with stakeholders\"}]}"
```

Example response shape:

```json
{
  "reply": "Based on the role details, here are SHL assessments that best match the requirement.",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": true
}
```

## Deploy on Render

1. Push this project to GitHub.
2. Create a new Web Service in Render.
3. Use the following build command:

```bash
pip install -r requirements.txt
```

4. Use the following start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Add `GEMINI_API_KEY` only if needed.
6. Confirm both endpoints work:

```text
https://your-app.onrender.com/health
https://your-app.onrender.com/chat
```

## Testing

```bash
pytest
```

Tests check the health endpoint, vague-query clarification, and response schema.

## Notes for the approach document

What worked well:

- Stateless reconstruction from conversation history
- Hard schema using Pydantic
- Catalog-only recommendations
- Clarification before retrieval for vague requests
- Hybrid retrieval instead of pure keyword search

What did not work well initially:

- Recommending immediately on short requests caused poor behavior.
- Letting the LLM create recommendations directly risked hallucinated assessment names and URLs.
- Pure semantic search sometimes missed exact skill names, so keyword boosting was added.

## Limitations

The scraper is defensive, but SHL can change page markup. If scraping returns too few records, inspect the catalog page HTML and update the CSS selectors in `scraper/scrape_catalog.py`.
