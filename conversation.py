import os
import re
from typing import Dict, List

from app.models import ChatResponse, Recommendation, Message
from app.retrieval import get_retriever, normalize
from app.prompts import SYSTEM_RULES

OFF_TOPIC = [
    "salary", "compensation", "legal", "lawsuit", "visa", "contract", "terminate",
    "fire employee", "interview questions", "write jd", "resume", "cv", "ignore previous",
    "system prompt", "jailbreak", "prompt injection"
]
ROLE_WORDS = [
    "developer", "engineer", "analyst", "manager", "sales", "support", "consultant",
    "java", "python", "javascript", "sql", "data", "graduate", "lead", "qa", "tester"
]
DETAIL_WORDS = [
    "senior", "junior", "mid", "entry", "years", "stakeholder", "personality",
    "cognitive", "coding", "technical", "leadership", "communication", "remote"
]
COMPARE_RE = re.compile(r"\b(compare|difference|different|versus|vs\.?|between)\b", re.I)


def latest_user_text(messages: List[Message]) -> str:
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def joined_user_text(messages: List[Message]) -> str:
    return "\n".join(m.content for m in messages if m.role == "user")


def is_off_topic(text: str) -> bool:
    low = text.lower()
    if "shl" in low and any(x in low for x in ["assessment", "test", "catalog"]):
        return False
    return any(term in low for term in OFF_TOPIC)


def has_enough_context(text: str) -> bool:
    low = normalize(text)
    has_role = any(word in low for word in ROLE_WORDS)
    details = sum(1 for word in DETAIL_WORDS if word in low)
    long_jd = len(text.split()) >= 25
    return long_jd or (has_role and details >= 1)


def clarification_question(text: str) -> str:
    low = normalize(text)
    if not any(word in low for word in ROLE_WORDS):
        return "Sure, I can help. What role are you hiring for, and which main skills should the assessment cover?"
    if not any(word in low for word in ["senior", "junior", "mid", "entry", "years"]):
        return "What seniority level is this role, and do you need only technical tests or personality/behavioral tests too?"
    return "Should I focus on technical skills, personality/behavioral fit, cognitive ability, or a mix of these?"


def recommendation_query(history_text: str) -> str:
    low = history_text.lower()
    additions = []
    if "personality" in low or "stakeholder" in low or "communication" in low or "leadership" in low:
        additions.append("personality workplace behaviour stakeholder")
    if "cognitive" in low or "reasoning" in low or "aptitude" in low:
        additions.append("cognitive ability reasoning")
    return history_text + " " + " ".join(additions)


def to_recommendations(items: List[Dict]) -> List[Recommendation]:
    out: List[Recommendation] = []
    seen = set()
    for item in items:
        name = item.get("name", "").strip()
        url = item.get("url", "").strip()
        if not name or not url or url in seen:
            continue
        seen.add(url)
        out.append(Recommendation(name=name, url=url, test_type=str(item.get("test_type", ""))))
        if len(out) == 10:
            break
    return out


def extract_compare_terms(text: str) -> List[str]:
    cleaned = re.sub(COMPARE_RE, " ", text)
    pieces = re.split(r"\band\b|,|/|\bvs\.?\b|\bwith\b", cleaned, flags=re.I)
    terms = []
    for piece in pieces:
        piece = piece.strip(" ?.!:;'")
        if 2 <= len(piece) <= 60:
            terms.append(piece)
    return terms[:4]


def compare_reply(text: str) -> ChatResponse:
    retriever = get_retriever()
    terms = extract_compare_terms(text)
    found = []
    for term in terms:
        item = retriever.find_by_name(term)
        if item is None:
            results = retriever.search(term, limit=1)
            item = results[0] if results else None
        if item and item not in found:
            found.append(item)
    if len(found) < 2:
        return ChatResponse(
            reply="I can compare them, but please provide the exact SHL assessment names you want compared.",
            recommendations=[],
            end_of_conversation=False,
        )
    a, b = found[0], found[1]
    reply = (
        f"{a['name']} is a {a.get('test_type', '')} type assessment. {a.get('description', 'No catalog description available')}\n\n"
        f"{b['name']} is a {b.get('test_type', '')} type assessment. {b.get('description', 'No catalog description available')}\n\n"
        "In short, choose the first when its measured area matches the role requirement better, and choose the second when its catalog description is closer to the hiring need."
    )
    return ChatResponse(reply=reply, recommendations=to_recommendations(found), end_of_conversation=False)


def llm_polish(reply: str, catalog_items: List[Dict]) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return reply
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        names = "\n".join(f"- {x.get('name')}: {x.get('description', '')}" for x in catalog_items[:10])
        prompt = f"{SYSTEM_RULES}\n\nCatalog items:\n{names}\n\nRewrite this reply in one concise paragraph without adding facts:\n{reply}"
        response = model.generate_content(prompt)
        text = getattr(response, "text", "").strip()
        return text or reply
    except Exception:
        return reply


def chat(messages: List[Message]) -> ChatResponse:
    current = latest_user_text(messages)
    history = joined_user_text(messages)

    if is_off_topic(current):
        return ChatResponse(
            reply="I can only help with SHL assessment recommendations, refinements, and comparisons from the SHL catalog.",
            recommendations=[],
            end_of_conversation=False,
        )

    if COMPARE_RE.search(current):
        return compare_reply(current)

    if not has_enough_context(history):
        return ChatResponse(reply=clarification_question(history), recommendations=[], end_of_conversation=False)

    retriever = get_retriever()
    query = recommendation_query(history)
    items = retriever.search(query, limit=10)
    recs = to_recommendations(items)

    if not recs:
        return ChatResponse(
            reply="I could not find a strong catalog match. Could you share the role, key skills, seniority, and whether you need technical or behavioral assessments?",
            recommendations=[],
            end_of_conversation=False,
        )

    reply = f"Based on the role details, here are {len(recs)} SHL assessments that best match the requirement."
    reply = llm_polish(reply, items)
    return ChatResponse(reply=reply, recommendations=recs, end_of_conversation=True)
