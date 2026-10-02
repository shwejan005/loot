"""Database seeder — populates card issuers, products, and reward rules.

Usage:
    python -m app.seed.load
"""

import logging

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CardIssuer, CardProduct, RewardRule
from app.seed import get_seed_data

logger = logging.getLogger("loot.seed")


def seed_cards(db: Session) -> dict:
    """Seed the card catalog. Skips entries that already exist (by slug).

    Returns a summary dict: {"issuers": N, "products": N, "rules": N}
    """
    data = get_seed_data()
    stats = {"issuers": 0, "products": 0, "rules": 0}

    for issuer_slug, issuer_name, country, cards in data:
        # Upsert issuer
        issuer = db.query(CardIssuer).filter_by(slug=issuer_slug).first()
        if not issuer:
            issuer = CardIssuer(
                name=issuer_name,
                slug=issuer_slug,
                country=country,
            )
            db.add(issuer)
            db.flush()
            stats["issuers"] += 1
            logger.info("Created issuer: %s", issuer_name)

        for (card_slug, card_name, network, tier, annual_fee,
             reward_currency, base_earn_rate, point_value, rules) in cards:
            # Upsert card product
            product = (
                db.query(CardProduct)
                .filter_by(issuer_id=issuer.id, slug=card_slug)
                .first()
            )
            if not product:
                product = CardProduct(
                    issuer_id=issuer.id,
                    name=card_name,
                    slug=card_slug,
                    network=network,
                    card_tier=tier,
                    annual_fee=annual_fee,
                    reward_currency=reward_currency,
                    base_earn_rate=base_earn_rate,
                    point_value=point_value,
                    country=country,
                )
                db.add(product)
                db.flush()
                stats["products"] += 1
                logger.info("  Created product: %s %s", issuer_name, card_name)

                # Add reward rules (only for new products)
                for category, earn_rate, earn_type, monthly_cap in rules:
                    rule = RewardRule(
                        card_product_id=product.id,
                        category=category,
                        earn_rate=earn_rate,
                        earn_type=earn_type,
                        monthly_cap=monthly_cap,
                    )
                    db.add(rule)
                    stats["rules"] += 1

    db.commit()
    logger.info("Seed complete: %s", stats)
    return stats


def run_seed():
    """Standalone entry point."""
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        result = seed_cards(db)
        print(f"Seeded: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
