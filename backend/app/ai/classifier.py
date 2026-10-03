"""AI-powered merchant classifier.

Uses OpenAI GPT-4o-mini to classify merchant names into spending categories.
Falls back to keyword-based heuristics when AI is unavailable.
"""

import json
import logging
from typing import Optional

import httpx

from app.config import settings
from app.services.routing_engine import CATEGORIES

logger = logging.getLogger("loot.classifier")

# ── Keyword-based fallback classifier ───────────────────────────────────

KEYWORD_MAP: dict[str, list[str]] = {
    "dining": [
        "swiggy", "zomato", "dominos", "mcdonalds", "starbucks", "pizza hut",
        "kfc", "burger king", "subway", "dunkin", "cafe", "restaurant",
        "food", "eat", "dine", "biryani", "chai", "chaayos", "le15", "ubereats", "uber eats",
    ],
    "grocery": [
        "bigbasket", "blinkit", "zepto", "jiomart", "dmart", "reliance fresh",
        "more supermarket", "grofers", "nature basket", "swiggy instamart",
        "grocery", "supermarket", "kirana",
    ],
    "fuel": [
        "indian oil", "bharat petroleum", "hp petrol", "shell", "reliance petrol",
        "iocl", "bpcl", "hpcl", "petrol", "diesel", "fuel", "ev charging",
    ],
    "travel": [
        "makemytrip", "irctc", "cleartrip", "goibibo", "yatra", "easemytrip",
        "ola", "uber", "rapido", "airline", "airways", "indigo", "air india",
        "vistara", "hotel", "oyo", "taj hotel", "marriott", "booking.com",
    ],
    "online": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "snapdeal",
        "nykaa", "tatacliq", "apple store", "croma", "reliance digital", "comet", "interflora",
    ],
    "entertainment": [
        "netflix", "hotstar", "prime video", "spotify", "youtube", "sony liv",
        "jio cinema", "zee5", "apple music", "bookmyshow", "pvr", "inox",
    ],
    "utilities": [
        "electricity", "water bill", "gas bill", "broadband", "airtel", "jio",
        "vodafone", "bsnl", "tata play", "dish tv", "internet", "postpaid",
    ],
    "healthcare": [
        "apollo", "pharmeasy", "1mg", "netmeds", "medplus", "practo",
        "hospital", "clinic", "doctor", "pharmacy", "medical",
    ],
    "education": [
        "coursera", "udemy", "unacademy", "byju", "upgrad", "school",
        "college", "university", "tuition",
    ],
    "insurance": [
        "lic", "hdfc life", "icici prudential", "max life", "policybazaar",
        "insurance", "premium",
    ],
    "government": [
        "income tax", "gst", "passport", "challan", "e-stamp", "mca",
    ],
    "international": [],  # detected by currency or merchant origin
    "department_store": [
        "shoppers stop", "lifestyle", "westside", "pantaloons", "central",
        "reliance brands", "reliance retail", "reliance trends",
    ],
}


def classify_by_keywords(merchant_name: str) -> str:
    """Simple keyword-based classification. Returns 'other' if no match."""
    name_lower = merchant_name.lower()
    for category, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in name_lower:
                return category
    return "other"


# ── AI-powered classifier ──────────────────────────────────────────────

CLASSIFICATION_PROMPT = """You are a merchant category classifier for a credit card rewards app.

Given a merchant name (exactly as it appears on a bank statement or SMS), classify it into exactly ONE of these categories:
{categories}

Rules:
- Return ONLY a JSON object: {{"category": "<category>", "confidence": <0.0-1.0>}}
- If the merchant is ambiguous, pick the most likely category.
- "Uber" alone is travel; "Uber Eats" is dining.
- Online stores like Amazon, Flipkart are "online" (not their specific product category).
- Default to "other" only when truly unrecognisable.
"""


async def classify_merchant_ai(merchant_name: str) -> tuple[str, float]:
    """Use OpenAI to classify a merchant name.

    Returns (category, confidence). Falls back to keyword classifier on error.
    """
    if not settings.openai_api_key:
        category = classify_by_keywords(merchant_name)
        return category, 0.7

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": CLASSIFICATION_PROMPT.format(
                                categories=", ".join(CATEGORIES)
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Merchant: {merchant_name}",
                        },
                    ],
                    "temperature": 0.1,
                    "max_tokens": 64,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON response
            parsed = json.loads(content)
            category = parsed.get("category", "other")
            confidence = parsed.get("confidence", 0.5)

            if category not in CATEGORIES:
                category = "other"

            return category, confidence

    except Exception as e:
        logger.warning("AI classification failed: %s", e)
        category = classify_by_keywords(merchant_name)
        return category, 0.5


def classify_merchant(merchant_name: str) -> str:
    """Classify a merchant for synchronous API handlers.

    The local rules are the default. When an OpenAI key is configured, try the
    hosted classifier and fall back to the local rules on any provider error.
    """
    if not settings.openai_api_key:
        return classify_by_keywords(merchant_name)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": CLASSIFICATION_PROMPT.format(categories=", ".join(CATEGORIES)),
                        },
                        {"role": "user", "content": f"Merchant: {merchant_name}"},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 64,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            category = json.loads(content).get("category", "other")
            if category not in CATEGORIES:
                return "other"
            return category
    except Exception as exc:
        logger.warning("AI classification failed: %s", exc)
        return classify_by_keywords(merchant_name)
