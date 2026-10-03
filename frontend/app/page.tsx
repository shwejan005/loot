"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  ChevronRight,
  CircleDollarSign,
  Coffee,
  CreditCard,
  Eye,
  EyeOff,
  Film,
  Home,
  Lightbulb,
  LockKeyhole,
  LogOut,
  Moon,
  Plus,
  ReceiptText,
  RotateCcw,
  Search,
  ShoppingBag,
  Sparkles,
  Sun,
  Wallet,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  analytics,
  auth,
  cards as cardsApi,
  catalog,
  transactions as transactionsApi,
  type AuthResponse,
  type CardProduct,
  type CardUtilization,
  type DashboardSummary,
  type Issuer,
  type MonthlyReport,
  type SpendingCategory,
  type Transaction,
  type User,
  type UserCard,
} from "@/lib/api";

type TabKey = "home" | "activity" | "wallet" | "insights" | "profile";
type ThemeMode = "light" | "dark" | null;
type TransactionRecord = {
  id: number;
  merchant: string;
  detail: string;
  amount: number;
  reward: string;
  rewardState: "earned" | "missed";
  category: string;
  time: string;
  date: Date;
  icon: LucideIcon;
};

const TOKEN_KEY = "loot-access-token";
const THEME_KEY = "loot-theme";
const PERIODS = ["All", "This month", "Last month"];
const CARD_TONES = ["card-ink", "card-wine", "card-paper"];

function formatINR(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function categoryLabel(value: string | null | undefined) {
  if (!value) return "Other";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function categoryIcon(value: string | null | undefined): LucideIcon {
  const category = value?.toLowerCase() ?? "";
  if (category === "dining") return Coffee;
  if (category === "entertainment") return Film;
  if (["online", "department_store", "grocery"].includes(category)) return ShoppingBag;
  if (category === "travel") return ArrowUpRight;
  return ReceiptText;
}

function monthName(month: string) {
  const [year, number] = month.split("-").map(Number);
  return new Date(year, number - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
}

function toRecord(item: Transaction, userCards: UserCard[]): TransactionRecord {
  const date = new Date(item.transacted_at ?? item.created_at);
  const usedCard = userCards.find((card) => card.id === item.card_id);
  const merchant = item.merchant_raw?.trim() || "Purchase";
  const cardName = usedCard?.nickname || usedCard?.card_product?.name;
  const detail = [categoryLabel(item.category), cardName].filter(Boolean).join(" · ");
  const missed = Number(item.reward_missed || 0);
  const earned = Number(item.reward_earned || 0);
  const rewardState = missed > 0 ? "missed" : "earned";
  const reward = missed > 0 ? `${formatINR(missed)} missed` : `+${formatINR(earned)}`;
  return {
    id: item.id,
    merchant,
    detail: detail || "Purchase",
    amount: Number(item.amount),
    reward,
    rewardState,
    category: categoryLabel(item.category),
    time: Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }),
    date,
    icon: categoryIcon(item.category),
  };
}

function BrandMark() {
  return (
    <div className="brand-lockup" aria-label="Loot Wallet">
      <span className="brand-symbol" aria-hidden="true"><span>L</span></span>
      <span className="brand-name">Loot</span>
      <span className="brand-wallet">WALLET</span>
    </div>
  );
}

function Header({
  isDark,
  user,
  onThemeToggle,
  onNotify,
  onProfile,
}: {
  isDark: boolean;
  user: User;
  onThemeToggle: () => void;
  onNotify: () => void;
  onProfile: () => void;
}) {
  const initial = (user.display_name || user.username).slice(0, 1).toUpperCase();
  return (
    <header className="topbar">
      <BrandMark />
      <div className="topbar-actions">
        <button className="icon-button" type="button" aria-label={isDark ? "Switch to light appearance" : "Switch to dark appearance"} onClick={onThemeToggle}>
          {isDark ? <Sun size={19} strokeWidth={1.8} /> : <Moon size={19} strokeWidth={1.8} />}
        </button>
        <button className="icon-button notification-button" type="button" aria-label="Notifications" onClick={onNotify}><Bell size={19} strokeWidth={1.8} /></button>
        <button className="avatar-button" type="button" aria-label="Open profile" onClick={onProfile}>{initial}</button>
      </div>
    </header>
  );
}

function SectionTitle({ label, action, onAction }: { label: string; action?: string; onAction?: () => void }) {
  return (
    <div className="section-title">
      <h2>{label}</h2>
      {action && <button type="button" className="text-action" onClick={onAction}>{action}<ChevronRight size={15} /></button>}
    </div>
  );
}

function TransactionRow({ item }: { item: TransactionRecord }) {
  const Icon = item.icon;
  return (
    <div className="transaction-row">
      <span className="transaction-icon"><Icon size={19} strokeWidth={1.7} /></span>
      <span className="transaction-copy"><strong>{item.merchant}</strong><span>{item.detail} · {item.time}</span></span>
      <span className="transaction-value"><strong>{formatINR(item.amount)}</strong><span className={item.rewardState === "earned" ? "reward-earned" : "reward-missed"}>{item.reward}</span></span>
    </div>
  );
}

function HomeScreen({
  user,
  transactions,
  categories,
  report,
  showBalance,
  onBalanceToggle,
  onTabChange,
  onAddTransaction,
}: {
  user: User;
  transactions: TransactionRecord[];
  categories: SpendingCategory[];
  report: MonthlyReport | null;
  showBalance: boolean;
  onBalanceToggle: () => void;
  onTabChange: (tab: TabKey) => void;
  onAddTransaction: () => void;
}) {
  const [firstName] = (user.display_name || user.username).split(/[\s@]/);
  const now = new Date();
  const topCategory = categories[0];
  const categoryTotal = categories.reduce((sum, item) => sum + Number(item.total_spent), 0);
  const shownCategories: SpendingCategory[] = categories.length > 3
    ? [...categories.slice(0, 2), { category: "other", total_spent: categories.slice(2).reduce((sum, item) => sum + Number(item.total_spent), 0), reward_earned: 0, reward_missed: 0, transaction_count: 0 }]
    : categories;
  const categoryShares = shownCategories.map((item) => categoryTotal ? Number(item.total_spent) / categoryTotal * 100 : 0);
  const greetings = now.getHours() < 12 ? "Good morning" : now.getHours() < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="screen-content">
      <div className="welcome-row">
        <div><p className="eyebrow">YOUR MONEY, IN GOOD FORM</p><h1>{greetings}, {firstName}<span className="greeting-period">.</span></h1></div>
        <span className="live-status"><i /> LIVE</span>
      </div>

      <section className="reward-hero" aria-label="Monthly rewards earned">
        <div className="hero-topline"><p>EST. REWARD VALUE <span>·</span> THIS MONTH</p><button className="hero-eye" type="button" onClick={onBalanceToggle} aria-label={showBalance ? "Hide reward estimate" : "Show reward estimate"}>{showBalance ? <Eye size={17} /> : <EyeOff size={17} />}</button></div>
        <div className="hero-amount-row"><p className="hero-amount">{showBalance ? formatINR(Number(report?.total_reward_earned ?? 0)) : "••••••"}</p><span className="hero-growth"><ArrowUpRight size={14} /> THIS MONTH</span></div>
        <p className="hero-caption">An estimate from your card reward rules.</p>
        <div className="hero-bottom"><div className="hero-period"><span className="period-dot" /> {now.toLocaleDateString("en-IN", { month: "long", year: "numeric" })}</div><button type="button" className="hero-link" onClick={() => onTabChange("insights")}>See report <ArrowRight size={15} /></button></div>
        <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
      </section>

      <div className="quick-metrics">
        <div className="quick-metric"><span className="metric-label">SPENT THIS MONTH</span><strong>{showBalance ? formatINR(Number(report?.total_spent ?? 0)) : "••••••"}</strong><span className="metric-foot"><ArrowDownLeft size={13} /> {report?.total_spent ? `${report.top_category === "none" ? "Spending tracked" : `${categoryLabel(report.top_category)} leads`}` : "No purchases tracked yet"}</span></div>
        <div className="metric-divider" />
        <div className="quick-metric"><span className="metric-label">REWARDS MISSED</span><strong className="missed-value">{showBalance ? formatINR(Number(report?.total_reward_missed ?? 0)) : "••••••"}</strong><button type="button" className="metric-foot metric-link" onClick={() => onTabChange("insights")}>Find out why <ArrowRight size={13} /></button></div>
      </div>

      <section className="content-section">
        <SectionTitle label="Apple Pay in India" action="Add cards" onAction={() => onTabChange("wallet")} />
        <button type="button" className="recommendation-card recommendation-button" onClick={() => onTabChange("wallet")}>
          <span className="recommendation-icon"><Sparkles size={19} strokeWidth={1.7} /></span>
          <span className="recommendation-copy"><span className="eyebrow">LOOT FOR APPLE PAY</span><span className="recommendation-headline">See the best card before you pay.</span><span>Loot for Chrome spots the store and compares your eligible cards.</span></span>
          <span className="round-arrow" aria-hidden="true"><ArrowRight size={17} /></span>
        </button>
      </section>

      <section className="content-section">
        <SectionTitle label="Your spending" action="Details" onAction={() => onTabChange("insights")} />
        <div className="spending-card">
          {topCategory ? <>
            <div className="spending-summary"><span>Top category · last 30 days</span><strong><span className="category-marker" /> {categoryLabel(topCategory.category)} <small>{formatINR(Number(topCategory.total_spent))}</small></strong></div>
            <div className="spend-progress" role="img" aria-label={`Spending in ${categoryLabel(topCategory.category)} and other categories`}>
              {categoryShares.map((share, index) => <span key={index} className={`spend-fill ${["dining-fill", "travel-fill", "other-fill"][index]}`} style={{ width: `${share}%` }} />)}
            </div>
            <div className="spending-legend">{shownCategories.map((item) => <span key={item.category}><i className={item.category === topCategory.category ? "legend-wine" : "legend-grey"} /> {categoryLabel(item.category)} <b>{categoryTotal ? Math.round(Number(item.total_spent) / categoryTotal * 100) : 0}%</b></span>)}</div>
          </> : <p className="empty-state">Your spending breakdown will appear after you add a purchase.</p>}
        </div>
      </section>

      <section className="content-section activity-section"><SectionTitle label="Recent activity" action="View all" onAction={() => onTabChange("activity")} /><div className="transaction-list">{transactions.slice(0, 3).map((item) => <TransactionRow key={item.id} item={item} />)}{transactions.length === 0 && <p className="empty-state">Your first purchase is a good place to start.</p>}</div></section>

      <section className="content-section last-home-section"><SectionTitle label="Your toolkit" action="View wallet" onAction={() => onTabChange("wallet")} /><button type="button" className="subscription-preview toolkit-preview" onClick={() => onTabChange("wallet")}><span className="subscription-count"><CircleDollarSign size={20} /></span><span className="subscription-copy"><strong>Cards in your wallet</strong><span>Use your card rewards more intentionally.</span></span><ChevronRight size={18} className="sub-chevron" /></button></section>
      <button type="button" className="floating-add" aria-label="Add transaction" onClick={onAddTransaction}><Plus size={22} /></button>
    </div>
  );
}

function ActivityScreen({ transactions, selectedPeriod, onSelectPeriod, report, totalTransactions, loadingMore, onLoadMore }: { transactions: TransactionRecord[]; selectedPeriod: string; onSelectPeriod: (period: string) => void; report: MonthlyReport | null; totalTransactions: number; loadingMore: boolean; onLoadMore: () => void }) {
  const shown = transactions.filter((item) => {
    if (selectedPeriod === "All" || Number.isNaN(item.date.getTime())) return true;
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - (selectedPeriod === "Last month" ? 1 : 0), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + (selectedPeriod === "Last month" ? 0 : 1), 1);
    return item.date >= start && item.date < end;
  });
  return (
    <div className="screen-content inner-screen">
      <p className="eyebrow">YOUR MONEY, MOVING</p><h1>Activity<span className="greeting-period">.</span></h1><p className="screen-subtitle">Every purchase, with the full picture.</p>
      <div className="activity-total-card"><div><span>THIS MONTH’S SPEND</span><strong>{formatINR(Number(report?.total_spent ?? 0))}</strong></div><div className="total-divider" /><div><span>EST. REWARD VALUE</span><strong className="wine-text">{formatINR(Number(report?.total_reward_earned ?? 0))}</strong></div></div>
      <div className="filter-pills" role="group" aria-label="Filter activity">{PERIODS.map((period) => <button type="button" key={period} className={selectedPeriod === period ? "filter-pill selected" : "filter-pill"} onClick={() => onSelectPeriod(period)}>{period}</button>)}</div>
      <section className="content-section activity-full"><SectionTitle label={selectedPeriod === "All" ? "All activity" : selectedPeriod} /><div className="transaction-list transaction-list-large">{shown.map((item) => <TransactionRow key={item.id} item={item} />)}{shown.length === 0 && <p className="empty-state">No transactions in this period yet.</p>}</div>{transactions.length < totalTransactions && <button type="button" className="load-more-button" disabled={loadingMore} onClick={onLoadMore}>{loadingMore ? "Loading…" : "Load older purchases"}</button>}</section>
      <div className="privacy-note"><LockKeyhole size={15} /><span>Showing {transactions.length} of {totalTransactions} saved purchases. Your activity is private.</span></div>
    </div>
  );
}

function PaymentCard({ card, index, onRemove, onDefault, onRename }: { card: UserCard; index: number; onRemove: (card: UserCard) => void; onDefault: (card: UserCard) => void; onRename: (card: UserCard, nickname: string) => Promise<boolean> }) {
  const product = card.card_product;
  const [editingNickname, setEditingNickname] = useState(false);
  const [nickname, setNickname] = useState(card.nickname || product?.name || "Card");
  const [savingNickname, setSavingNickname] = useState(false);

  async function saveNickname(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = nickname.trim();
    if (!value) return;
    setSavingNickname(true);
    try {
      if (await onRename(card, value)) setEditingNickname(false);
    } finally {
      setSavingNickname(false);
    }
  }

  return (
    <div className={`payment-card ${CARD_TONES[index % CARD_TONES.length]}`}>
      <div className="payment-card-top"><span>{product?.issuer?.name ?? "CREDIT CARD"}</span><span className="card-contactless">)))</span></div>
      <div className="card-chip" aria-hidden="true"><i /><i /><i /><i /></div>
      <strong className="payment-card-name">{card.nickname || product?.name || "Card"}</strong>
      <div className="payment-card-bottom"><span>Saved by card name</span><span>{product?.network?.toUpperCase() ?? ""}</span></div>
      {editingNickname ? <form className="card-actions card-rename-form" onSubmit={saveNickname}>
        <input aria-label={`Nickname for ${product?.name ?? "card"}`} maxLength={64} required value={nickname} onChange={(event) => setNickname(event.target.value)} />
        <button type="submit" disabled={savingNickname}>{savingNickname ? "Saving…" : "Save"}</button>
        <button type="button" onClick={() => { setNickname(card.nickname || product?.name || "Card"); setEditingNickname(false); }}>Cancel</button>
      </form> : <div className="card-actions">
        <button type="button" onClick={() => onDefault(card)}>{card.is_default ? "Default card" : "Make default"}</button>
        <button type="button" onClick={() => { setNickname(card.nickname || product?.name || "Card"); setEditingNickname(true); }}>Rename</button>
        <button type="button" onClick={() => onRemove(card)} aria-label={`Remove ${product?.name ?? "card"}`}>Remove</button>
      </div>}
    </div>
  );
}

function WalletScreen({ cards, onAdd, onRemove, onDefault, onRename }: { cards: UserCard[]; onAdd: () => void; onRemove: (card: UserCard) => void; onDefault: (card: UserCard) => void; onRename: (card: UserCard, nickname: string) => Promise<boolean> }) {
  return (
    <div className="screen-content inner-screen">
      <p className="eyebrow">YOUR PAYMENT TOOLKIT</p><h1>Your wallet<span className="greeting-period">.</span></h1><p className="screen-subtitle">{cards.length} {cards.length === 1 ? "card" : "cards"} · add by card name only</p>
      <div className="wallet-cards">{cards.map((card, index) => <PaymentCard key={card.id} card={card} index={index} onRemove={onRemove} onDefault={onDefault} onRename={onRename} />)}</div>
      {cards.length === 0 && <div className="empty-card-state"><CreditCard size={24} /><strong>Your wallet is ready for a card.</strong><span>Add an eligible Axis Bank Visa or Mastercard by name.</span></div>}
      <button type="button" className="add-card-button" onClick={onAdd}><Plus size={17} /> Add a card</button>
      <div className="wallet-security"><LockKeyhole size={16} /><span>No card number, expiry date, or security code is needed. Loot compares eligible Axis Bank Visa and Mastercard credit cards found in its starter catalog.</span></div>
    </div>
  );
}

function InsightsScreen({ categories, report, utilization }: { categories: SpendingCategory[]; report: MonthlyReport | null; utilization: CardUtilization[] }) {
  const total = categories.reduce((sum, item) => sum + Number(item.total_spent), 0);
  return (
    <div className="screen-content inner-screen">
      <p className="eyebrow">A LITTLE MORE CLARITY</p><h1>Insights<span className="greeting-period">.</span></h1><p className="screen-subtitle">Small changes, more value kept.</p>
      <div className="insight-lead"><div className="insight-lead-icon"><Lightbulb size={20} /></div><span className="eyebrow">{report?.month ? monthName(report.month).toUpperCase() : "MONTHLY RECAP"}</span><strong>{Number(report?.total_spent ?? 0) > 0 ? "Your spending, made clearer." : "Your insights start here."}</strong><p>{Number(report?.total_spent ?? 0) > 0 ? `You spent ${formatINR(Number(report?.total_spent))} and have an estimated ${formatINR(Number(report?.total_reward_earned))} in rewards this month.` : "Add purchases to see your category breakdown and reward opportunities."}</p></div>
      <section className="content-section insight-category-section"><SectionTitle label="Where it goes" action="Last 30 days" /><div className="category-list">{categories.map((item, index) => {
        const share = total ? Math.round(Number(item.total_spent) / total * 100) : 0;
        const dot = index === 0 ? "dining-dot" : index === 1 ? "shopping-dot" : index === 2 ? "travel-dot" : "other-dot";
        return <div key={item.category}><div className="category-row"><span className={`category-dot ${dot}`} /><span>{categoryLabel(item.category)}</span><strong>{formatINR(Number(item.total_spent))}</strong><small>{share}%</small></div><div className="category-meter"><i style={{ width: `${share}%` }} /></div></div>;
      })}{categories.length === 0 && <p className="empty-state">No categorized spending yet.</p>}</div></section>
      <section className="content-section"><SectionTitle label="Card utilization" action="Last 30 days" />{utilization.length ? <div className="utilization-list">{utilization.map((item) => <div className="utilization-row" key={item.card.id}><div><strong>{item.card.nickname || item.card.card_product?.name || "Card"}</strong><span>{item.times_was_used} purchases · {formatINR(Number(item.total_spent))}</span></div><b>{Math.round(item.utilization_pct)}%<small>used when optimal</small></b></div>)}</div> : <p className="empty-state">Add a card and log purchases to see how well your cards are working.</p>}</section>
      <div className="privacy-note"><LockKeyhole size={15} /><span>Insights use only transactions saved in your account.</span></div>
    </div>
  );
}

function ProfileScreen({ user, isDark, onThemeToggle, onLogout }: { user: User; isDark: boolean; onThemeToggle: () => void; onLogout: () => void }) {
  const displayName = user.display_name || user.username;
  return (
    <div className="screen-content inner-screen profile-screen"><p className="eyebrow">YOUR LOOT</p><h1>Profile<span className="greeting-period">.</span></h1>
      <div className="profile-identity"><span className="profile-avatar">{displayName.slice(0, 1).toUpperCase()}</span><div><strong>{displayName}</strong><span>{user.email}</span></div></div>
      <section className="content-section profile-settings"><SectionTitle label="Preferences" />
        <button type="button" className="setting-row" onClick={onThemeToggle}><span className="setting-icon">{isDark ? <Sun size={18} /> : <Moon size={18} />}</span><span><strong>Appearance</strong><small>{isDark ? "Dark mode" : "Light mode"}</small></span><span className={`switch ${isDark ? "switch-on" : ""}`}><i /></span></button>
        <div className="setting-row setting-static"><span className="setting-icon"><LockKeyhole size={18} /></span><span><strong>Privacy & security</strong><small>Your account data is stored privately.</small></span><ChevronRight size={18} /></div>
        <button type="button" className="setting-row" onClick={onLogout}><span className="setting-icon"><LogOut size={18} /></span><span><strong>Sign out</strong><small>Sign out of {user.username}</small></span><ChevronRight size={18} /></button>
      </section><div className="profile-footer">LOOT WALLET <span>VERSION 1.0.0</span></div>
    </div>
  );
}

function BottomNav({ activeTab, onChange }: { activeTab: TabKey; onChange: (tab: TabKey) => void }) {
  const items: { id: TabKey; label: string; icon: LucideIcon }[] = [
    { id: "home", label: "Home", icon: Home }, { id: "activity", label: "Activity", icon: ReceiptText }, { id: "wallet", label: "Wallet", icon: Wallet }, { id: "insights", label: "Insights", icon: Sparkles }, { id: "profile", label: "You", icon: CircleDollarSign },
  ];
  return <nav className="bottom-nav" aria-label="Main navigation">{items.map((item) => { const Icon = item.icon; return <button key={item.id} type="button" className={`nav-item ${activeTab === item.id ? "nav-active" : ""}`} aria-current={activeTab === item.id ? "page" : undefined} onClick={() => onChange(item.id)}><Icon size={20} strokeWidth={activeTab === item.id ? 2.15 : 1.7} /><span>{item.label}</span></button>; })}</nav>;
}

function AuthScreen({ onAuthenticated, isDark }: { onAuthenticated: (response: AuthResponse) => void; isDark: boolean }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = mode === "login"
        ? await auth.login({ username, password })
        : await auth.register({ username, email, password });
      onAuthenticated(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in right now.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className={`auth-page ${isDark ? "auth-dark" : ""}`}><div className="auth-brand"><BrandMark /></div><section className="auth-card"><p className="eyebrow">YOUR MONEY, IN GOOD FORM</p><h1>{mode === "login" ? "Welcome back." : "Make room for more."}</h1><p className="screen-subtitle">{mode === "login" ? "Sign in to see your wallet and spending." : "Create an account to start tracking your rewards."}</p>
      <form className="auth-form" onSubmit={submit}>
        <label>Username or email<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
        {mode === "register" && <label>Email address<input autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>}
        <label>Password<input autoComplete={mode === "login" ? "current-password" : "new-password"} type="password" minLength={mode === "register" ? 8 : 1} maxLength={72} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="primary-submit" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}<ArrowRight size={17} /></button>
      </form><p className="auth-toggle">{mode === "login" ? "New to Loot?" : "Already have an account?"} <button type="button" onClick={() => { setError(""); setMode(mode === "login" ? "register" : "login"); }}> {mode === "login" ? "Create an account" : "Sign in"}</button></p>
      <p className="auth-privacy"><LockKeyhole size={13} /> Your data stays yours.</p>
    </section></main>
  );
}

function AddTransactionSheet({ cards, merchant, amount, selectedCardId, smsBody, busy, error, onMerchant, onAmount, onCard, onSmsBody, onSmsSubmit, onClose, onSubmit }: {
  cards: UserCard[]; merchant: string; amount: string; selectedCardId: string; busy: boolean; error: string;
  onMerchant: (value: string) => void; onAmount: (value: string) => void; onCard: (value: string) => void; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  smsBody: string; onSmsBody: (value: string) => void; onSmsSubmit: () => void;
}) {
  const [smsMode, setSmsMode] = useState(false);
  return <div className="sheet-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="add-sheet" role="dialog" aria-modal="true" aria-labelledby="add-sheet-title"><div className="sheet-handle" /><div className="sheet-heading"><div><p className="eyebrow">KEEP YOUR PICTURE COMPLETE</p><h2 id="add-sheet-title">Add a purchase</h2></div><button type="button" className="icon-button" aria-label="Close" onClick={onClose}><X size={20} /></button></div>
    <div className="entry-mode"><button type="button" className={!smsMode ? "entry-mode-active" : ""} onClick={() => setSmsMode(false)}>Enter details</button><button type="button" className={smsMode ? "entry-mode-active" : ""} onClick={() => setSmsMode(true)}>Paste bank SMS</button></div>
    {!smsMode ? <form className="add-form" onSubmit={onSubmit}><label>Merchant<input autoFocus value={merchant} onChange={(event) => onMerchant(event.target.value)} placeholder="e.g. Blue Tokai" maxLength={512} required /></label><label>Amount<input value={amount} onChange={(event) => onAmount(event.target.value)} type="number" inputMode="decimal" min="0.01" step="0.01" placeholder="₹ 0" required /></label>
      <label>Card used <select value={selectedCardId} onChange={(event) => onCard(event.target.value)}><option value="">Not sure / cash / not tracked</option>{cards.map((card) => <option key={card.id} value={card.id}>{card.nickname || card.card_product?.name || "Card"}</option>)}</select></label>
      {error && <p className="form-error" role="alert">{error}</p>}<button type="submit" className="primary-submit" disabled={busy}>{busy ? "Saving…" : "Add transaction"} <ArrowRight size={17} /></button>
    </form> : <div className="add-form"><label>Purchase alert<textarea value={smsBody} onChange={(event) => onSmsBody(event.target.value)} placeholder="Paste the bank's purchase alert" rows={4} maxLength={4000} /></label><p className="sms-note">Paste a purchase alert only. The original message is not saved.</p>{error && <p className="form-error" role="alert">{error}</p>}<button type="button" className="primary-submit" disabled={busy || !smsBody.trim()} onClick={onSmsSubmit}>{busy ? "Reading alert…" : "Import purchase"}<ArrowRight size={17} /></button></div>}
    <p className="form-privacy"><LockKeyhole size={13} /> Your data stays yours.</p>
  </section></div>;
}

function CardCatalogSheet({ products, issuers, search, busy, error, loading, onSearch, onClose, onAdd }: {
  products: CardProduct[]; issuers: Issuer[]; search: string; busy: boolean; error: string; loading: boolean;
  onSearch: (value: string) => void; onClose: () => void; onAdd: (product: CardProduct) => void;
}) {
  const issuerById = new Map<number, Issuer>(issuers.map((issuer) => [issuer.id, issuer] as const));
  const issuerNames = new Map<number, string>(issuers.map((issuer) => [issuer.id, issuer.name] as const));
  const filtered = products.filter((product) => {
    const issuer = issuerById.get(product.issuer_id);
    const supported = issuer?.slug === "axis" && ["visa", "mastercard"].includes(product.network.toLowerCase());
    return supported && `${product.name} ${issuer?.name ?? ""} ${product.network}`.toLowerCase().includes(search.toLowerCase());
  });
  return <div className="sheet-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="add-sheet catalog-sheet" role="dialog" aria-modal="true" aria-labelledby="catalog-title"><div className="sheet-handle" /><div className="sheet-heading"><div><p className="eyebrow">CHOOSE YOUR CARD</p><h2 id="catalog-title">Apple Pay cards</h2></div><button type="button" className="icon-button" aria-label="Close" onClick={onClose}><X size={20} /></button></div>
    <p className="sms-note">At launch, Apple Pay in India supports eligible Axis Bank Visa and Mastercard credit cards. Save by card name only; the starter catalog may not include every eligible card yet.</p>
    <label className="catalog-search"><Search size={17} /><input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="Search Axis card name" /></label>
    <div className="catalog-results">{loading ? <p className="empty-state">Loading supported cards…</p> : filtered.map((product) => <div className="catalog-product" key={product.id}><span className="catalog-product-mark"><CreditCard size={19} /></span><span><strong>{product.name}</strong><small>{issuerNames.get(product.issuer_id) ?? "Card issuer"} · {product.network.toUpperCase()} · {formatINR(Number(product.annual_fee))}/yr</small></span><button type="button" className="catalog-add" disabled={busy} onClick={() => onAdd(product)}>Add</button></div>)}{!loading && filtered.length === 0 && <p className="empty-state">No matching eligible Axis Bank card is in the starter catalog yet.</p>}</div>{error && <p className="form-error" role="alert">{error}</p>}
    </section></div>;
}

export default function LootWalletApp() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [theme, setTheme] = useState<ThemeMode>(null);
  const [showBalance, setShowBalance] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState("All");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [userCards, setUserCards] = useState<UserCard[]>([]);
  const [rawTransactions, setRawTransactions] = useState<Transaction[]>([]);
  const [transactionPage, setTransactionPage] = useState(1);
  const [loadingMoreTransactions, setLoadingMoreTransactions] = useState(false);
  const [categories, setCategories] = useState<SpendingCategory[]>([]);
  const [report, setReport] = useState<MonthlyReport | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [utilization, setUtilization] = useState<CardUtilization[]>([]);
  const [ready, setReady] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [reloadAttempt, setReloadAttempt] = useState(0);
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [showAddSheet, setShowAddSheet] = useState(false);
  const [showCardCatalog, setShowCardCatalog] = useState(false);
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [selectedCardId, setSelectedCardId] = useState("");
  const [smsBody, setSmsBody] = useState("");
  const [catalogProducts, setCatalogProducts] = useState<CardProduct[]>([]);
  const [issuers, setIssuers] = useState<Issuer[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");

  const month = useMemo(() => {
    const current = new Date();
    return `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}`;
  }, []);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_KEY);
    // This is a browser-only preference, unavailable during static prerendering.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(savedTheme === "light" || savedTheme === "dark" ? savedTheme : window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const savedToken = window.localStorage.getItem(TOKEN_KEY);
    if (savedToken) setToken(savedToken);
    else setReady(true);
  }, []);

  useEffect(() => {
    if (!token) return;
    let active = true;
    Promise.all([
      auth.me(token),
      cardsApi.list(token),
      transactionsApi.list(token),
      analytics.spendingByCategory(token, 1),
      analytics.monthlyReport(token, month),
      analytics.cardUtilization(token, 1),
      analytics.summary(token),
    ]).then(([profile, wallet, transactionPage, spending, monthly, cardStats, dashboardSummary]) => {
      if (!active) return;
      setUser(profile);
      setUserCards(wallet);
      setRawTransactions(transactionPage.items);
      setTransactionPage(transactionPage.page);
      setCategories(spending);
      setReport(monthly);
      setUtilization(cardStats);
      setSummary(dashboardSummary);
    }).catch((reason: unknown) => {
      if (!active) return;
      const message = reason instanceof Error ? reason.message : "Could not load your account.";
      if (message.includes("Invalid or expired token")) {
        window.localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setReady(true);
        setLoadError("Your session expired. Please sign in again.");
      } else {
        setLoadError(message);
      }
    }).finally(() => {
      if (active) {
        setLoadingData(false);
        setReady(true);
      }
    });
    return () => { active = false; };
  }, [token, month, reloadAttempt]);

  useEffect(() => {
    if (!showCardCatalog || !user) return;
    let active = true;
    Promise.all([catalog.cards({ country: user.country }), catalog.issuers(user.country)]).then(([products, issuerList]) => {
      if (!active) return;
      setCatalogProducts(products);
      setIssuers(issuerList);
    }).catch((reason: unknown) => {
      if (active) setActionError(reason instanceof Error ? reason.message : "Could not load card catalog.");
    }).finally(() => { if (active) setCatalogLoading(false); });
    return () => { active = false; };
  }, [showCardCatalog, user]);

  const isDark = theme === "dark";
  const transactionRecords = useMemo(() => rawTransactions.map((item) => toRecord(item, userCards)), [rawTransactions, userCards]);

  function toggleTheme() {
    const nextTheme = isDark ? "light" : "dark";
    setTheme(nextTheme);
    window.localStorage.setItem(THEME_KEY, nextTheme);
  }

  function showToast(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 2800);
  }

  function onAuthenticated(response: AuthResponse) {
    window.localStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.user);
    setToken(response.access_token);
    setActiveTab("home");
    setLoadError("");
    setReady(false);
    setLoadingData(true);
  }

  function logout(message = "") {
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setUserCards([]);
    setRawTransactions([]);
    setTransactionPage(1);
    setCategories([]);
    setReport(null);
    setSummary(null);
    setUtilization([]);
    setLoadError("");
    setReady(true);
    if (message) showToast(message);
  }

  async function refreshDashboard(activeToken: string) {
    const [wallet, transactionPage, spending, monthly, cardStats, dashboardSummary] = await Promise.all([
      cardsApi.list(activeToken), transactionsApi.list(activeToken), analytics.spendingByCategory(activeToken, 1), analytics.monthlyReport(activeToken, month), analytics.cardUtilization(activeToken, 1), analytics.summary(activeToken),
    ]);
    setUserCards(wallet);
    setRawTransactions(transactionPage.items);
    setTransactionPage(transactionPage.page);
    setCategories(spending);
    setReport(monthly);
    setUtilization(cardStats);
    setSummary(dashboardSummary);
  }

  async function addTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setActionError("");
    setBusy(true);
    try {
      await transactionsApi.add(token, {
        merchant_raw: merchant.trim(),
        amount: Number(amount),
        currency: user?.country === "US" ? "USD" : "INR",
        ...(selectedCardId ? { card_id: Number(selectedCardId) } : {}),
      });
      await refreshDashboard(token);
      setMerchant(""); setAmount(""); setSelectedCardId(""); setShowAddSheet(false); setActiveTab("activity");
      showToast("Purchase saved to your activity.");
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Could not save this purchase.");
    } finally { setBusy(false); }
  }

  async function loadMoreTransactions() {
    if (!token || loadingMoreTransactions) return;
    setLoadingMoreTransactions(true);
    try {
      const nextPage = await transactionsApi.list(token, transactionPage + 1);
      setRawTransactions((current) => [...current, ...nextPage.items]);
      setTransactionPage(nextPage.page);
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : "Could not load older purchases.");
    } finally { setLoadingMoreTransactions(false); }
  }

  async function importSmsTransaction() {
    if (!token || !smsBody.trim()) return;
    setActionError("");
    setBusy(true);
    try {
      await transactionsApi.addFromSMS(token, smsBody.trim());
      await refreshDashboard(token);
      setSmsBody(""); setShowAddSheet(false); setActiveTab("activity");
      showToast("Purchase imported from your bank alert.");
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Could not read this bank alert.");
    } finally { setBusy(false); }
  }

  async function addCard(product: CardProduct) {
    if (!token) return;
    setBusy(true);
    setActionError("");
    try {
      await cardsApi.add(token, { card_product_id: product.id, is_default: userCards.length === 0 });
      await refreshDashboard(token);
      setCatalogSearch(""); setShowCardCatalog(false);
      showToast(`${product.name} added to your wallet.`);
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Could not add this card.");
    } finally { setBusy(false); }
  }

  async function removeCard(card: UserCard) {
    if (!token) return;
    setBusy(true);
    try {
      await cardsApi.remove(token, card.id);
      await refreshDashboard(token);
      showToast(`${card.nickname || card.card_product?.name || "Card"} removed.`);
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : "Could not remove that card.");
    } finally { setBusy(false); }
  }

  async function makeDefault(card: UserCard) {
    if (!token || card.is_default) return;
    setBusy(true);
    try {
      await cardsApi.update(token, card.id, { is_default: true });
      await refreshDashboard(token);
      showToast("Default card updated.");
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : "Could not update the default card.");
    } finally { setBusy(false); }
  }

  async function renameCard(card: UserCard, nickname: string): Promise<boolean> {
    if (!token) return false;
    setBusy(true);
    try {
      const updated = await cardsApi.update(token, card.id, { nickname });
      setUserCards((current) => current.map((item) => item.id === card.id ? { ...item, nickname: updated.nickname } : item));
      showToast("Card nickname updated.");
      return true;
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : "Could not update this card name.");
      return false;
    } finally { setBusy(false); }
  }

  function handleTabChange(tab: TabKey) {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (!ready) return <main className={`loot-app ${theme ? `theme-${theme}` : ""}`}><div className="loading-state"><BrandMark /><span>Loading your wallet…</span></div></main>;
  if (!token) return <AuthScreen onAuthenticated={onAuthenticated} isDark={isDark} />;
  if (!user) return <main className={`loot-app ${theme ? `theme-${theme}` : ""}`}><div className="connection-error"><BrandMark /><h1>We couldn’t reach your wallet.</h1><p>{loadError || "Your account data could not be loaded."}</p><button type="button" className="primary-submit" onClick={() => { setLoadError(""); setReady(false); setLoadingData(true); setReloadAttempt((value) => value + 1); }}><RotateCcw size={16} /> Try again</button><button type="button" className="signout-link" onClick={() => logout()}>Sign out</button></div></main>;

  const rootClassName = `loot-app${theme ? ` theme-${theme}` : ""}`;
  return (
    <main className={rootClassName}>
      <div className="app-frame">
        <Header user={user} isDark={isDark} onThemeToggle={toggleTheme} onNotify={() => showToast("You’re all caught up.")} onProfile={() => handleTabChange("profile")} />
        {loadError && <div className="inline-error"><span>{loadError}</span><button type="button" onClick={() => { setLoadError(""); setLoadingData(true); setReloadAttempt((value) => value + 1); }}><RotateCcw size={14} /> Retry</button></div>}
        {loadingData && <div className="inline-loading">Refreshing your account…</div>}
        {activeTab === "home" && <HomeScreen user={user} transactions={transactionRecords} categories={categories} report={report} showBalance={showBalance} onBalanceToggle={() => setShowBalance((value) => !value)} onTabChange={handleTabChange} onAddTransaction={() => { setActionError(""); setShowAddSheet(true); }} />}
        {activeTab === "activity" && <ActivityScreen transactions={transactionRecords} selectedPeriod={selectedPeriod} onSelectPeriod={setSelectedPeriod} report={report} totalTransactions={Number(summary?.total_transactions ?? 0)} loadingMore={loadingMoreTransactions} onLoadMore={loadMoreTransactions} />}
        {activeTab === "wallet" && <WalletScreen cards={userCards} onAdd={() => { setActionError(""); setCatalogLoading(true); setShowCardCatalog(true); }} onRemove={removeCard} onDefault={makeDefault} onRename={renameCard} />}
        {activeTab === "insights" && <InsightsScreen categories={categories} report={report} utilization={utilization} />}
        {activeTab === "profile" && <ProfileScreen user={user} isDark={isDark} onThemeToggle={toggleTheme} onLogout={() => logout("You’ve signed out.")} />}
        <BottomNav activeTab={activeTab} onChange={handleTabChange} />
      </div>

      {toast && <div className="toast" role="status"><Check size={16} />{toast}</div>}
      {showAddSheet && <AddTransactionSheet cards={userCards} merchant={merchant} amount={amount} selectedCardId={selectedCardId} smsBody={smsBody} busy={busy} error={actionError} onMerchant={setMerchant} onAmount={setAmount} onCard={setSelectedCardId} onSmsBody={setSmsBody} onSmsSubmit={importSmsTransaction} onClose={() => setShowAddSheet(false)} onSubmit={addTransaction} />}
      {showCardCatalog && <CardCatalogSheet products={catalogProducts} issuers={issuers} search={catalogSearch} busy={busy} error={actionError} loading={catalogLoading} onSearch={setCatalogSearch} onClose={() => setShowCardCatalog(false)} onAdd={addCard} />}
    </main>
  );
}
