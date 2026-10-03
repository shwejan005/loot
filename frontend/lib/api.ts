/** Typed client for the Loot Wallet FastAPI service. */

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type User = {
  id: number;
  email: string;
  username: string;
  display_name: string | null;
  country: string;
  onboarded: boolean;
  created_at: string;
};

export type AuthResponse = { access_token: string; token_type: string; user: User };

export type Issuer = { id: number; name: string; slug: string; country: string; logo_url: string | null };

export type CardProduct = {
  id: number;
  issuer_id: number;
  name: string;
  slug: string;
  network: string;
  card_tier: string;
  annual_fee: number;
  reward_currency: string;
  base_earn_rate: number;
  point_value: number;
  image_url: string | null;
  benefits: Record<string, unknown>;
  country: string;
  issuer?: Issuer | null;
  reward_rules?: RewardRule[];
};

export type RewardRule = {
  id: number;
  card_product_id: number;
  category: string;
  earn_rate: number;
  earn_type: string;
  monthly_cap: number | null;
  quarterly_cap: number | null;
  min_spend: number | null;
  valid_from: string | null;
  valid_to: string | null;
  conditions: Record<string, unknown>;
};

export type UserCard = {
  id: number;
  user_id: number;
  card_product_id: number;
  nickname: string | null;
  is_default: boolean;
  is_active: boolean;
  added_at: string;
  card_product: CardProduct | null;
};
export type UserCardRecord = Omit<UserCard, "card_product">;

export type Transaction = {
  id: number;
  user_id: number;
  card_id: number | null;
  merchant_id: number | null;
  merchant_raw: string | null;
  amount: number;
  currency: string;
  category: string | null;
  source: string;
  reward_earned: number;
  optimal_card_id: number | null;
  optimal_reward: number;
  reward_missed: number;
  transacted_at: string | null;
  created_at: string;
};

export type Paginated<T> = { items: T[]; total: number; page: number; page_size: number; pages: number };
export type SpendingCategory = {
  category: string;
  total_spent: number;
  reward_earned: number;
  reward_missed: number;
  transaction_count: number;
};
export type MonthlyReport = {
  month: string;
  total_spent: number;
  total_reward_earned: number;
  total_reward_missed: number;
  top_category: string;
  worst_card_losses: Array<Record<string, unknown>>;
  best_card_to_add: string | null;
};
export type CardUtilization = {
  card: UserCard;
  transaction_count: number;
  total_spent: number;
  reward_earned: number;
  times_was_optimal: number;
  times_was_used: number;
  utilization_pct: number;
};
export type CardRanking = { card: UserCard; reward_value: number; earn_rate: number; reasoning: string };
export type RoutingRecommendation = {
  recommended: CardRanking;
  alternatives: CardRanking[];
  category_detected: string;
  savings_vs_worst: number;
};
export type DashboardSummary = {
  total_transactions: number;
  total_reward_earned: number;
  total_reward_missed: number;
  card_count: number;
  money_left_on_table: number;
};

type RequestOptions = { method?: string; body?: unknown; token?: string };

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    throw new Error(`Can’t reach Loot Wallet API at ${API_BASE}. Start the backend and try again.`);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const auth = {
  register: (data: { username: string; email: string; password: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: data }),
  login: (data: { username: string; password: string }) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: data }),
  me: (token: string) => request<User>("/auth/me", { token }),
};

export const catalog = {
  issuers: (country = "IN") => request<Issuer[]>(`/catalog/issuers?country=${encodeURIComponent(country)}`),
  cards: (params: { country?: string; issuer_id?: number; network?: string; tier?: string } = {}) => {
    const query = new URLSearchParams();
    query.set("country", params.country ?? "IN");
    if (params.issuer_id) query.set("issuer_id", String(params.issuer_id));
    if (params.network) query.set("network", params.network);
    if (params.tier) query.set("tier", params.tier);
    return request<CardProduct[]>(`/catalog/cards?${query.toString()}`);
  },
  cardDetail: (id: number) => request<CardProduct>(`/catalog/cards/${id}`),
  categories: () => request<string[]>("/catalog/categories"),
};

export const cards = {
  list: (token: string) => request<UserCard[]>("/cards/", { token }),
  add: (token: string, data: { card_product_id: number; nickname?: string; is_default?: boolean }) =>
    request<UserCardRecord>("/cards/", { method: "POST", body: data, token }),
  update: (token: string, cardId: number, data: { nickname?: string; is_default?: boolean }) => {
    const query = new URLSearchParams();
    if (data.nickname !== undefined) query.set("nickname", data.nickname);
    if (data.is_default !== undefined) query.set("is_default", String(data.is_default));
    return request<UserCardRecord>(`/cards/${cardId}?${query.toString()}`, { method: "PATCH", token });
  },
  remove: (token: string, cardId: number) => request<void>(`/cards/${cardId}`, { method: "DELETE", token }),
};

export const transactions = {
  list: (token: string, page = 1, pageSize = 100) =>
    request<Paginated<Transaction>>(`/transactions/?page=${page}&page_size=${pageSize}`, { token }),
  add: (token: string, data: { card_id?: number; merchant_raw: string; amount: number; category?: string; currency?: string }) =>
    request<Transaction>("/transactions/", { method: "POST", body: data, token }),
  addFromSMS: (token: string, smsBody: string) =>
    request<Transaction>("/transactions/sms", { method: "POST", body: { sms_body: smsBody }, token }),
  detail: (token: string, txnId: number) => request<Transaction>(`/transactions/${txnId}`, { token }),
};

export const routing = {
  recommend: (token: string, data: { merchant_name: string; amount: number; apple_pay_india?: boolean }) =>
    request<RoutingRecommendation>("/route/", { method: "POST", body: data, token }),
};

export const analytics = {
  summary: (token: string) => request<DashboardSummary>("/analytics/summary", { token }),
  spendingByCategory: (token: string, months = 1) =>
    request<SpendingCategory[]>(`/analytics/spending-by-category?months=${months}`, { token }),
  cardUtilization: (token: string, months = 1) =>
    request<CardUtilization[]>(`/analytics/card-utilization?months=${months}`, { token }),
  monthlyReport: (token: string, month: string) =>
    request<MonthlyReport>(`/analytics/monthly-report?month=${encodeURIComponent(month)}`, { token }),
};
