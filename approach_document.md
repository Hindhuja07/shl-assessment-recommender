# Approach Document: Conversational SHL Assessment Recommender

## Design overview

The service is built as a stateless FastAPI application with two endpoints: `GET /health` and `POST /chat`. The chat endpoint receives the full conversation history on every call and reconstructs the current user need from that history. This keeps the service aligned with the evaluator requirement that no per-conversation state is stored.

The agent is designed around four behaviors: clarification, recommendation, refinement, and comparison. If the user asks a vague question such as “I need an assessment,” the system does not recommend immediately. It asks for role, seniority, and assessment type. Once enough information is available, it retrieves matching assessments from the local SHL catalog and returns 1 to 10 recommendations. If the user changes constraints later, the full history is used to form a new retrieval query, so the shortlist is updated instead of starting over. For comparison questions, the service searches for the named catalog items and compares only the stored catalog descriptions.

## Catalog and retrieval setup

The catalog is stored as `data/shl_catalog.json`. The scraper collects product links from the SHL product catalog and visits individual product pages to extract name, URL, description, test type signals, duration signals, and keywords. Recommendations are generated only from this catalog file, which prevents non-catalog URLs from entering the response.

Retrieval uses a hybrid method. Sentence-transformer embeddings with FAISS provide semantic matching, while keyword scoring boosts exact role and skill matches such as Java, SQL, Python, personality, stakeholder, reasoning, or leadership. This combination is useful because assessment names often contain exact skill terms, while job descriptions may describe the same need in a broader way.

## Prompt and grounding strategy

The core decision logic is deterministic Python rather than fully delegated to an LLM. This reduces hallucination risk and makes the behavior easier to explain. Gemini is optional and only used to polish the final reply text. It is not allowed to create recommendation objects. All recommendation names, URLs, and test types come from retrieved catalog records.

The system rules are simple: stay within SHL assessment selection, ask clarifying questions when context is insufficient, refuse unrelated requests, and never invent catalog data. This keeps the response grounded and predictable under automated replay.

## Evaluation approach

I tested the service against common conversation patterns: vague first turn, clear role request, mid-conversation refinement, comparison request, and off-topic or prompt-injection-style requests. The most important checks were schema stability, empty recommendations during clarification/refusal, catalog-only URLs, and a maximum of 10 recommendations.

What improved the behavior most was adding a strict clarification gate. Early versions recommended too soon for short messages. Another improvement was adding keyword boosting on top of semantic search, because exact technologies in job descriptions should strongly influence the ranking.

## Trade-offs and limitations

The solution favors reliability over a complex multi-agent design. This makes it easier to debug and defend in a technical interview. The main limitation is catalog scraping: if the SHL website markup changes, the scraper may need selector updates. The application still runs with a small fallback catalog for local testing, but the final deployed version should use the freshly scraped full catalog.
