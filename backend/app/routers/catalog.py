"""Catalog router — browse all supported card products and issuers."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import CardIssuer, CardProduct, RewardRule
from app.schemas import CardIssuerOut, CardProductOut, CardProductDetail

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/issuers", response_model=list[CardIssuerOut])
def list_issuers(
    country: str = Query("IN", description="Filter by country code"),
    db: Session = Depends(get_db),
):
    """List all card issuers."""
    issuers = (
        db.query(CardIssuer)
        .filter(CardIssuer.country == country)
        .order_by(CardIssuer.name)
        .all()
    )
    return [CardIssuerOut.model_validate(i) for i in issuers]


@router.get("/cards", response_model=list[CardProductOut])
def list_card_products(
    issuer_id: int | None = Query(None, description="Filter by issuer"),
    network: str | None = Query(None, description="Filter by network (visa, mastercard, etc.)"),
    tier: str | None = Query(None, description="Filter by tier"),
    country: str = Query("IN"),
    db: Session = Depends(get_db),
):
    """List all available card products. Supports filtering."""
    query = db.query(CardProduct).filter(CardProduct.country == country, CardProduct.is_active == True)

    if issuer_id:
        query = query.filter(CardProduct.issuer_id == issuer_id)
    if network:
        query = query.filter(CardProduct.network == network)
    if tier:
        query = query.filter(CardProduct.card_tier == tier)

    products = query.order_by(CardProduct.name).all()
    return [CardProductOut.model_validate(p) for p in products]


@router.get("/cards/{product_id}", response_model=CardProductDetail)
def get_card_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get detailed info about a specific card product, including reward rules."""
    product = (
        db.query(CardProduct)
        .options(
            joinedload(CardProduct.issuer),
            joinedload(CardProduct.reward_rules),
        )
        .filter(CardProduct.id == product_id)
        .first()
    )
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Card product not found")

    return CardProductDetail.model_validate(product)


@router.get("/categories", response_model=list[str])
def list_categories():
    """List all spending categories recognised by Loot Wallet."""
    from app.services.routing_engine import CATEGORIES
    return CATEGORIES
