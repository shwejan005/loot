"""Loot Wallet database models.

Domain hierarchy:
  CardIssuer → CardProduct → RewardRule
  User → UserCard (links to CardProduct)
    User → Transaction → reward estimates
  User → Subscription
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Card Catalog (master data — not user-specific) ─────────────────────

class CardIssuer(Base):
    """A bank or financial institution that issues credit cards."""
    __tablename__ = "card_issuers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)      # "HDFC Bank", "ICICI", "American Express"
    slug = Column(String(64), unique=True, nullable=False)       # "hdfc", "icici", "amex"
    logo_url = Column(String(512))
    country = Column(String(4), default="IN")

    products = relationship("CardProduct", back_populates="issuer", cascade="all, delete-orphan")


class CardProduct(Base):
    """A specific credit card product offered by an issuer.

    E.g. HDFC Infinia, ICICI Amazon Pay, Amex Gold.
    Contains base reward info; detailed per-category rules live in RewardRule.
    """
    __tablename__ = "card_products"
    __table_args__ = (
        UniqueConstraint("issuer_id", "slug", name="uq_issuer_product_slug"),
    )

    id = Column(Integer, primary_key=True, index=True)
    issuer_id = Column(Integer, ForeignKey("card_issuers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(256), nullable=False)                   # "Infinia", "Regalia Gold"
    slug = Column(String(128), nullable=False)                   # "infinia", "regalia-gold"
    network = Column(String(32), nullable=False)                 # visa, mastercard, rupay, amex, diners
    card_tier = Column(String(32), default="standard")           # standard, gold, platinum, super-premium
    annual_fee = Column(Numeric(10, 2), default=0)
    reward_currency = Column(String(64), default="points")       # points, cashback, miles, thankyou-points
    base_earn_rate = Column(Numeric(6, 4), default=0)            # default earn rate (e.g. 0.01 = 1%)
    point_value = Column(Numeric(6, 4), default=0.25)            # value of 1 point in INR (for comparison)
    image_url = Column(String(512))
    benefits = Column(JSON, default=dict)                        # lounges, insurance, golf, etc.
    country = Column(String(4), default="IN")
    is_active = Column(Boolean, default=True)

    issuer = relationship("CardIssuer", back_populates="products")
    reward_rules = relationship("RewardRule", back_populates="card_product", cascade="all, delete-orphan")
    user_cards = relationship("UserCard", back_populates="card_product")


class RewardRule(Base):
    """A reward earning rule for a specific card + spending category.

    E.g. "HDFC Diners Black earns 5x on dining, capped at 5000 points/month."
    Handles rotating categories via valid_from / valid_to.
    """
    __tablename__ = "reward_rules"

    id = Column(Integer, primary_key=True, index=True)
    card_product_id = Column(Integer, ForeignKey("card_products.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(64), nullable=False)                # dining, grocery, fuel, travel, online, utilities, etc.
    earn_rate = Column(Numeric(8, 4), nullable=False)            # multiplier (e.g. 5.0 = 5x) or percentage
    earn_type = Column(String(16), default="multiplier")         # "multiplier" or "cashback_pct"
    monthly_cap = Column(Numeric(12, 2))                         # max reward value per month (NULL = uncapped)
    quarterly_cap = Column(Numeric(12, 2))
    min_spend = Column(Numeric(12, 2))                           # minimum transaction amount to earn bonus
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))                   # NULL = permanent rule
    conditions = Column(JSON, default=dict)                      # merchant-specific conditions, exclusions

    card_product = relationship("CardProduct", back_populates="reward_rules")


# ── Merchants ───────────────────────────────────────────────────────────

class Merchant(Base):
    """Enriched merchant database for accurate category classification."""
    __tablename__ = "merchants"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_merchant_normalized"),
    )

    id = Column(Integer, primary_key=True, index=True)
    raw_name = Column(String(512), nullable=False)               # as seen in SMS / statement
    normalized_name = Column(String(256), nullable=False)        # cleaned name for matching
    display_name = Column(String(256))                           # pretty name for UI
    category = Column(String(64), nullable=False)                # dining, grocery, fuel, etc.
    subcategory = Column(String(64))                             # fast_food, fine_dining, etc.
    mcc_code = Column(String(8))                                 # Merchant Category Code
    logo_url = Column(String(512))
    metadata_ = Column("metadata", JSON, default=dict)

    transactions = relationship("Transaction", back_populates="merchant")


# ── Users ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(128))
    country = Column(String(4), default="IN")
    onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    cards = relationship("UserCard", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")


class UserCard(Base):
    """A card that a user has added to their wallet."""
    __tablename__ = "user_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "card_product_id", "last_four", name="uq_user_card_product_last4"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_product_id = Column(Integer, ForeignKey("card_products.id"), nullable=False)
    nickname = Column(String(64))                                # user's custom name for this card
    last_four = Column(String(4))                                # for SMS matching
    is_default = Column(Boolean, default=False)                  # user's current "default" card
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="cards")
    card_product = relationship("CardProduct", back_populates="user_cards")
    transactions = relationship("Transaction", back_populates="card_used", foreign_keys="Transaction.card_id")


# ── Transactions ────────────────────────────────────────────────────────

class Transaction(Base):
    """A purchase transaction — imported from SMS, email, or manual entry."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("user_cards.id", ondelete="SET NULL"), index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="SET NULL"), index=True)

    merchant_raw = Column(String(512))                           # raw merchant string from SMS/statement
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(4), default="INR")
    category = Column(String(64))                                # AI-classified spending category
    source = Column(String(32), default="manual")                # sms, email, manual, api

    # Routing analysis
    reward_earned = Column(Numeric(12, 2), default=0)            # reward value on the card actually used
    optimal_card_id = Column(Integer, ForeignKey("user_cards.id", ondelete="SET NULL"))
    optimal_reward = Column(Numeric(12, 2), default=0)           # reward value on the best card
    reward_missed = Column(Numeric(12, 2), default=0)            # delta (opportunity cost)

    transacted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="transactions")
    card_used = relationship("UserCard", foreign_keys=[card_id], back_populates="transactions")
    optimal_card = relationship("UserCard", foreign_keys=[optimal_card_id])
    merchant = relationship("Merchant", back_populates="transactions")


# ── Subscriptions ───────────────────────────────────────────────────────

class Subscription(Base):
    """A recurring charge detected from transaction patterns."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="SET NULL"))
    name = Column(String(256), nullable=False)                   # "Netflix", "Spotify", "Swiggy One"
    amount = Column(Numeric(12, 2))
    currency = Column(String(4), default="INR")
    frequency = Column(String(16), default="monthly")            # monthly, annual, weekly
    card_id = Column(Integer, ForeignKey("user_cards.id", ondelete="SET NULL"))
    optimal_card_id = Column(Integer, ForeignKey("user_cards.id", ondelete="SET NULL"))
    status = Column(String(16), default="active")                # active, paused, cancelled
    next_charge_at = Column(DateTime(timezone=True))
    detected_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="subscriptions")
    card = relationship("UserCard", foreign_keys=[card_id])
    optimal_card = relationship("UserCard", foreign_keys=[optimal_card_id])
    merchant = relationship("Merchant")
