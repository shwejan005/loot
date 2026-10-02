"""Seed data: popular Indian credit cards and their reward rules.

Run via `python -m app.seed.cards_in` or called from the startup lifespan.
"""

# Each entry: (issuer_slug, issuer_name, cards)
# Each card: (slug, name, network, tier, annual_fee, reward_currency,
#              base_earn_rate, point_value, rules)
# Each rule: (category, earn_rate, earn_type, monthly_cap)

ISSUERS_AND_CARDS = [
    # ── HDFC ────────────────────────────────────────────────────────────
    ("hdfc", "HDFC Bank", "IN", [
        ("infinia", "Infinia", "visa", "super-premium", 12500, "points", 0.033, 1.0, [
            ("dining", 5.0, "multiplier", None),
            ("travel", 5.0, "multiplier", None),
            ("online", 3.33, "multiplier", None),
            ("grocery", 3.33, "multiplier", None),
        ]),
        ("regalia-gold", "Regalia Gold", "visa", "platinum", 2500, "points", 0.025, 0.50, [
            ("dining", 4.0, "multiplier", 7500),
            ("travel", 4.0, "multiplier", 7500),
            ("online", 2.0, "multiplier", 5000),
        ]),
        ("diners-black", "Diners Club Black", "diners", "super-premium", 10000, "points", 0.033, 1.0, [
            ("dining", 5.0, "multiplier", None),
            ("travel", 5.0, "multiplier", None),
            ("online", 5.0, "multiplier", None),
            ("grocery", 5.0, "multiplier", None),
            ("entertainment", 5.0, "multiplier", None),
        ]),
        ("millennia", "Millennia", "visa", "standard", 1000, "cashback", 0.01, 1.0, [
            ("online", 2.5, "cashback_pct", 750),
            ("dining", 1.0, "cashback_pct", None),
        ]),
        ("swiggy", "Swiggy HDFC", "visa", "standard", 500, "cashback", 0.01, 1.0, [
            ("dining", 10.0, "cashback_pct", 1500),
            ("online", 5.0, "cashback_pct", 1000),
            ("fuel", 1.0, "cashback_pct", None),
        ]),
    ]),

    # ── ICICI ───────────────────────────────────────────────────────────
    ("icici", "ICICI Bank", "IN", [
        ("amazon-pay", "Amazon Pay", "visa", "standard", 500, "cashback", 0.01, 1.0, [
            ("online", 5.0, "cashback_pct", None),  # Amazon purchases
            ("dining", 2.0, "cashback_pct", None),
            ("travel", 2.0, "cashback_pct", None),
        ]),
        ("emeralde", "Emeralde", "visa", "super-premium", 12000, "points", 0.033, 1.0, [
            ("dining", 5.0, "multiplier", None),
            ("travel", 5.0, "multiplier", None),
            ("entertainment", 5.0, "multiplier", None),
        ]),
        ("coral", "Coral", "visa", "gold", 500, "points", 0.02, 0.50, [
            ("dining", 2.0, "multiplier", None),
            ("grocery", 2.0, "multiplier", None),
            ("entertainment", 2.0, "multiplier", None),
        ]),
        ("sapphiro", "Sapphiro", "visa", "platinum", 3500, "points", 0.025, 0.75, [
            ("dining", 4.0, "multiplier", None),
            ("travel", 4.0, "multiplier", None),
            ("entertainment", 4.0, "multiplier", None),
        ]),
    ]),

    # ── SBI ─────────────────────────────────────────────────────────────
    ("sbi", "SBI Card", "IN", [
        ("elite", "Elite", "visa", "platinum", 4999, "points", 0.02, 0.25, [
            ("dining", 5.0, "multiplier", None),
            ("grocery", 5.0, "multiplier", None),
            ("department_store", 5.0, "multiplier", None),
            ("entertainment", 5.0, "multiplier", None),
        ]),
        ("simplysave", "SimplySave", "visa", "standard", 499, "points", 0.01, 0.25, [
            ("dining", 10.0, "multiplier", None),
            ("grocery", 5.0, "multiplier", None),
            ("entertainment", 5.0, "multiplier", None),
        ]),
        ("cashback", "Cashback", "visa", "standard", 999, "cashback", 0.01, 1.0, [
            ("online", 5.0, "cashback_pct", 5000),
        ]),
    ]),

    # ── Axis ────────────────────────────────────────────────────────────
    ("axis", "Axis Bank", "IN", [
        ("magnus", "Magnus", "visa", "super-premium", 12500, "points", 0.033, 1.0, [
            ("dining", 5.0, "multiplier", None),
            ("travel", 5.0, "multiplier", None),
            ("online", 5.0, "multiplier", None),
        ]),
        ("flipkart", "Flipkart Axis", "visa", "standard", 500, "cashback", 0.015, 1.0, [
            ("online", 5.0, "cashback_pct", None),   # Flipkart
            ("dining", 4.0, "cashback_pct", None),
            ("travel", 4.0, "cashback_pct", None),
        ]),
        ("ace", "ACE", "visa", "standard", 499, "cashback", 0.02, 1.0, [
            ("utilities", 5.0, "cashback_pct", None),
            ("dining", 4.0, "cashback_pct", None),
            ("online", 2.0, "cashback_pct", None),
        ]),
    ]),

    # ── Amex ────────────────────────────────────────────────────────────
    ("amex", "American Express", "IN", [
        ("gold", "Membership Rewards Gold", "amex", "gold", 1500, "points", 0.02, 0.50, [
            ("dining", 5.0, "multiplier", None),
            ("travel", 3.0, "multiplier", None),
            ("online", 2.0, "multiplier", None),
        ]),
        ("platinum-travel", "Platinum Travel", "amex", "platinum", 5000, "points", 0.025, 0.75, [
            ("travel", 5.0, "multiplier", None),
            ("dining", 3.0, "multiplier", None),
            ("international", 5.0, "multiplier", None),
        ]),
        ("smartearn", "SmartEarn", "amex", "standard", 0, "points", 0.01, 0.25, [
            ("online", 10.0, "multiplier", None),
            ("dining", 5.0, "multiplier", None),
        ]),
    ]),

    # ── AU Small Finance Bank ───────────────────────────────────────────
    ("au", "AU Small Finance Bank", "IN", [
        ("lit", "LIT", "visa", "standard", 0, "cashback", 0.01, 1.0, [
            # LIT lets users pick 3 categories — simplified here
            ("dining", 5.0, "cashback_pct", 500),
            ("entertainment", 5.0, "cashback_pct", 500),
            ("online", 5.0, "cashback_pct", 500),
        ]),
    ]),

    # ── Kotak ───────────────────────────────────────────────────────────
    ("kotak", "Kotak Mahindra Bank", "IN", [
        ("811", "811 #DreamDifferent", "visa", "standard", 0, "cashback", 0.01, 1.0, [
            ("online", 2.0, "cashback_pct", 500),
            ("dining", 1.0, "cashback_pct", None),
        ]),
    ]),

    # ── IndusInd ────────────────────────────────────────────────────────
    ("indusind", "IndusInd Bank", "IN", [
        ("legend", "Legend", "visa", "super-premium", 10000, "points", 0.033, 0.75, [
            ("dining", 4.0, "multiplier", None),
            ("travel", 4.0, "multiplier", None),
            ("entertainment", 4.0, "multiplier", None),
            ("online", 3.0, "multiplier", None),
        ]),
    ]),
]


def get_seed_data():
    """Return structured seed data for the database seeder."""
    return ISSUERS_AND_CARDS
