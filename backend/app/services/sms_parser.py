"""SMS parser for Indian bank transaction messages.

Handles common patterns from HDFC, ICICI, SBI, Axis, Kotak, Amex, etc.
Extracts: amount, card last-four, merchant name, and transaction timestamp.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass
class ParsedSMS:
    """Structured data extracted from a bank SMS."""
    amount: Decimal
    merchant: Optional[str] = None
    last_four: Optional[str] = None
    card_network: Optional[str] = None  # if determinable
    timestamp: Optional[datetime] = None
    is_credit: bool = False             # True = refund/cashback
    raw: str = ""


# ── Regex patterns for common Indian bank SMS formats ───────────────────

# Amount patterns: "Rs.1,234.56", "INR 1234.56", "Rs 1,234", etc.
AMOUNT_PATTERNS = [
    r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",
    r"([\d,]+(?:\.\d{1,2})?)\s*(?:Rs\.?|INR|₹)",
]

# Card last-four: "card ending 1234", "xx1234", "XX1234", "****1234"
LAST_FOUR_PATTERNS = [
    r"(?:card\s+(?:ending|no\.?)\s*)(\d{4})",
    r"[xX*]{2,}\s*(\d{4})",
    r"(?:ending\s+(?:with\s+)?)(\d{4})",
]

# Merchant: "at AMAZON", "at Swiggy", "to UBER INDIA", "Info: ZOMATO"
MERCHANT_PATTERNS = [
    r"(?:at|to|@)\s+([A-Za-z0-9\s\-\.&']+?)(?:\s+on|\s*\.|\s*$)",
    r"Info:\s*([A-Za-z0-9\s\-\.&']+?)(?:\s*\.|\s*$)",
    r"(?:towards|for)\s+([A-Za-z0-9\s\-\.&']+?)(?:\s+on|\s*\.|\s*$)",
]

# Date patterns: "on 29-09-2026", "on 29/09/26", "on 29-Sep-2026"
DATE_PATTERNS = [
    r"on\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    r"on\s+(\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4})",
    r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s",
]

# Debit/credit indicators
DEBIT_KEYWORDS = ["debited", "spent", "purchase", "payment", "withdrawn", "charged", "txn"]
CREDIT_KEYWORDS = ["credited", "refund", "cashback", "reversed", "received"]


def _extract_amount(text: str) -> Optional[Decimal]:
    """Extract monetary amount from SMS text."""
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                raw = match.group(1).replace(",", "")
                return Decimal(raw)
            except InvalidOperation:
                continue
    return None


def _extract_last_four(text: str) -> Optional[str]:
    """Extract card last-four digits."""
    for pattern in LAST_FOUR_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_merchant(text: str) -> Optional[str]:
    """Extract merchant name."""
    for pattern in MERCHANT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            merchant = match.group(1).strip()
            # Clean up: remove trailing "on", numbers, etc.
            merchant = re.sub(r"\s+on$", "", merchant, flags=re.IGNORECASE)
            merchant = merchant.strip(". ")
            if len(merchant) >= 2:
                return merchant
    return None


def _extract_date(text: str) -> Optional[datetime]:
    """Extract transaction date."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
                        "%d-%b-%Y", "%d/%b/%Y", "%d-%b-%y", "%d/%b/%y"]:
                try:
                    return datetime.strptime(raw_date, fmt)
                except ValueError:
                    continue
    return None


def _is_credit(text: str) -> bool:
    """Determine if this is a credit (refund) transaction."""
    text_lower = text.lower()
    for kw in CREDIT_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def parse_sms(sms_body: str) -> Optional[ParsedSMS]:
    """Parse a raw bank SMS and extract transaction data.

    Returns None if the SMS doesn't appear to be a transaction alert.
    """
    amount = _extract_amount(sms_body)
    if amount is None:
        return None

    # Basic check: does this look like a transaction SMS?
    text_lower = sms_body.lower()
    is_transaction = any(kw in text_lower for kw in DEBIT_KEYWORDS + CREDIT_KEYWORDS)
    if not is_transaction:
        return None

    return ParsedSMS(
        amount=amount,
        merchant=_extract_merchant(sms_body),
        last_four=_extract_last_four(sms_body),
        timestamp=_extract_date(sms_body),
        is_credit=_is_credit(sms_body),
        raw=sms_body,
    )
