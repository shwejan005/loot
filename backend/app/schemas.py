"""Pydantic request / response schemas for the Loot Wallet API."""

from datetime import datetime
from decimal import Decimal
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


# ── Pagination ──────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


# ── Auth ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── User ────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    display_name: Optional[str] = None
    country: str = "IN"
    onboarded: bool = False
    created_at: datetime


# ── Card Issuer ─────────────────────────────────────────────────────────

class CardIssuerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    country: str = "IN"


# ── Card Product ────────────────────────────────────────────────────────

class CardProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issuer_id: int
    name: str
    slug: str
    network: str
    card_tier: str = "standard"
    annual_fee: Decimal = Decimal("0")
    reward_currency: str = "points"
    base_earn_rate: Decimal = Decimal("0")
    point_value: Decimal = Decimal("0.25")
    image_url: Optional[str] = None
    benefits: dict = {}
    country: str = "IN"


class CardProductDetail(CardProductOut):
    issuer: Optional[CardIssuerOut] = None
    reward_rules: list["RewardRuleOut"] = []


# ── Reward Rule ─────────────────────────────────────────────────────────

class RewardRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_product_id: int
    category: str
    earn_rate: Decimal
    earn_type: str = "multiplier"
    monthly_cap: Optional[Decimal] = None
    quarterly_cap: Optional[Decimal] = None
    min_spend: Optional[Decimal] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    conditions: dict = {}


# ── User Card ───────────────────────────────────────────────────────────

class UserCardCreate(BaseModel):
    card_product_id: int
    nickname: Optional[str] = None
    last_four: Optional[str] = Field(default=None, pattern=r"^\d{4}$")
    is_default: bool = False


class UserCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    card_product_id: int
    nickname: Optional[str] = None
    last_four: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    added_at: datetime


class UserCardDetail(UserCardOut):
    card_product: Optional[CardProductDetail] = None


# ── Merchant ────────────────────────────────────────────────────────────

class MerchantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_name: str
    normalized_name: str
    display_name: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    mcc_code: Optional[str] = None
    logo_url: Optional[str] = None


# ── Transaction ─────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    card_id: Optional[int] = None
    merchant_raw: Optional[str] = Field(default=None, max_length=512)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = "INR"
    category: Optional[str] = None
    source: str = "manual"
    transacted_at: Optional[datetime] = None


class SMSTransactionCreate(BaseModel):
    """Parse a raw bank SMS into a transaction."""
    sms_body: str = Field(min_length=1, max_length=4000)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    card_id: Optional[int] = None
    merchant_id: Optional[int] = None
    merchant_raw: Optional[str] = None
    amount: Decimal
    currency: str = "INR"
    category: Optional[str] = None
    source: str = "manual"
    reward_earned: Decimal = Decimal("0")
    optimal_card_id: Optional[int] = None
    optimal_reward: Decimal = Decimal("0")
    reward_missed: Decimal = Decimal("0")
    transacted_at: Optional[datetime] = None
    created_at: datetime


class TransactionDetail(TransactionOut):
    card_used: Optional[UserCardDetail] = None
    optimal_card: Optional[UserCardDetail] = None
    merchant: Optional[MerchantOut] = None


# ── Routing ─────────────────────────────────────────────────────────────

class RoutingRequest(BaseModel):
    """Ask Loot Wallet which card to use for a purchase."""
    merchant_name: str = Field(min_length=1, max_length=512)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = "INR"


class CardRanking(BaseModel):
    card: UserCardDetail
    reward_value: Decimal
    earn_rate: Decimal
    reasoning: str


class RoutingResponse(BaseModel):
    recommended: CardRanking
    alternatives: list[CardRanking] = []
    category_detected: str
    savings_vs_worst: Decimal = Decimal("0")


# ── Analytics ───────────────────────────────────────────────────────────

class SpendingByCategoryItem(BaseModel):
    category: str
    total_spent: Decimal
    reward_earned: Decimal
    reward_missed: Decimal
    transaction_count: int


class MonthlyReportOut(BaseModel):
    month: str                              # "2026-09"
    total_spent: Decimal
    total_reward_earned: Decimal
    total_reward_missed: Decimal
    top_category: str
    worst_card_losses: list[dict] = []      # cards where user lost the most
    best_card_to_add: Optional[str] = None  # AI recommendation


class CardUtilizationItem(BaseModel):
    card: UserCardDetail
    transaction_count: int
    total_spent: Decimal
    reward_earned: Decimal
    times_was_optimal: int
    times_was_used: int
    utilization_pct: float                  # % of times this was the best AND was used


# ── Subscription ────────────────────────────────────────────────────────

class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    amount: Optional[Decimal] = None
    currency: str = "INR"
    frequency: str = "monthly"
    status: str = "active"
    next_charge_at: Optional[datetime] = None
    detected_at: datetime


class SubscriptionDetail(SubscriptionOut):
    card: Optional[UserCardDetail] = None
    optimal_card: Optional[UserCardDetail] = None
    merchant: Optional[MerchantOut] = None


# ── Forward refs ────────────────────────────────────────────────────────

TokenResponse.model_rebuild()
CardProductDetail.model_rebuild()
UserCardDetail.model_rebuild()
TransactionDetail.model_rebuild()
SubscriptionDetail.model_rebuild()
