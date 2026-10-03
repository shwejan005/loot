// Set this to the deployed Loot API origin when the backend is hosted.
const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "lootAccessToken";
const EXAMPLE_AMOUNT = 1000;

const loginView = document.querySelector("#login-view");
const assistantView = document.querySelector("#assistant-view");
const loginForm = document.querySelector("#login-form");
const loginButton = document.querySelector("#login-button");
const loginError = document.querySelector("#login-error");
const loginSite = document.querySelector("#login-site");
const siteError = document.querySelector("#site-error");
const merchantName = document.querySelector("#merchant-name");
const merchantDomain = document.querySelector("#merchant-domain");
const amountInput = document.querySelector("#amount");
const resultElement = document.querySelector("#result");
const recommendForm = document.querySelector("#recommend-form");
const signoutButton = document.querySelector("#signout-button");

let activeSite = null;
let requestInProgress = false;

const knownStores = [
  ["apple store", "Apple Store"],
  ["apple.com", "Apple Store"],
  ["amazon", "Amazon"],
  ["blinkit", "Blinkit"],
  ["chaayos", "Chaayos"],
  ["zomato", "Zomato"],
  ["swiggy", "Swiggy"],
  ["croma", "Croma"],
  ["ixigo", "Ixigo"],
  ["tata 1mg", "Tata 1mg"],
  ["tata1mg", "Tata 1mg"],
  ["1mg", "Tata 1mg"],
  ["interflora", "Interflora"],
  ["le15", "Le15 Patisserie"],
  ["comet", "Comet"],
  ["reliance", "Reliance"],
  ["flipkart", "Flipkart"],
  ["myntra", "Myntra"],
  ["nykaa", "Nykaa"],
  ["ajio", "AJIO"],
];

function getMerchant(hostname, title) {
  const haystack = `${hostname} ${title}`.toLowerCase();
  const knownStore = knownStores.find(([needle]) => haystack.includes(needle));
  if (knownStore) return knownStore[1];

  const labels = hostname.toLowerCase().replace(/^www\./, "").split(".").filter(Boolean);
  if (labels.length < 2) return hostname;
  const suffix = labels.at(-2);
  const secondLevelSuffixes = new Set(["co", "com", "net", "org", "gov", "ac"]);
  const labelIndex = secondLevelSuffixes.has(suffix) && labels.length > 2 ? labels.length - 3 : labels.length - 2;
  return labels[labelIndex].replaceAll(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getCurrentTab() {
  return chrome.tabs.query({ active: true, currentWindow: true }).then(([tab]) => tab ?? null);
}

async function request(path, { method = "GET", token, body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error(`Can’t reach Loot at ${API_BASE}. Start the Loot API and try again.`);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
  }
  return response.json();
}

function showView(view) {
  loginView.hidden = view !== "login";
  assistantView.hidden = view !== "assistant";
}

function showLoginError(message) {
  loginError.textContent = message;
  loginError.hidden = !message;
}

function showSiteError(message) {
  siteError.textContent = message;
  siteError.hidden = !message;
}

function renderLoading() {
  resultElement.innerHTML = '<div class="loading-row"><span class="spinner" aria-hidden="true"></span><span>Comparing your eligible cards…</span></div>';
}

function renderNoSupportedCard() {
  resultElement.innerHTML = `
    <p class="result-eyebrow">NO ELIGIBLE CARD SAVED</p>
    <strong class="best-card-name">Add an Axis card</strong>
    <span class="result-reason">Save an eligible Axis Bank Visa or Mastercard credit card by name in your Loot wallet, then reopen this extension.</span>
  `;
}

function renderRecommendation(data) {
  if (!data.recommended?.card?.id) {
    renderNoSupportedCard();
    return;
  }

  const best = data.recommended;
  const cardName = best.card.nickname || best.card.card_product?.name || "Your saved card";
  const alternatives = (data.alternatives ?? []).map((item) => {
    const name = item.card.nickname || item.card.card_product?.name || "Saved card";
    const value = Number(item.reward_value).toLocaleString("en-IN", { maximumFractionDigits: 0 });
    return `<div class="alternative-row"><span>${escapeHtml(name)}</span><strong>₹${value}</strong></div>`;
  }).join("");
  const amount = Number(amountInput.value || EXAMPLE_AMOUNT).toLocaleString("en-IN", { maximumFractionDigits: 0 });
  const reward = Number(best.reward_value).toLocaleString("en-IN", { maximumFractionDigits: 0 });

  resultElement.innerHTML = `
    <p class="result-eyebrow">${escapeHtml(data.category_detected.replaceAll("_", " ").toUpperCase())} · BEST CARD</p>
    <strong class="best-card-name">${escapeHtml(cardName)}</strong>
    <span class="result-reason">${escapeHtml(best.reasoning)}</span>
    <strong class="reward-value">About ₹${reward} back on ₹${amount}</strong>
    ${alternatives ? `<div class="alternatives"><p class="alternatives-title">Other saved cards</p>${alternatives}</div>` : ""}
  `;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

async function openAssistant(token) {
  showView("assistant");
  if (!activeSite) {
    merchantName.textContent = "Open a shopping site";
    merchantDomain.textContent = "Click Loot while a store page is open.";
    resultElement.innerHTML = '<span class="result-reason">Loot needs an ordinary http or https shopping tab to identify the merchant.</span>';
    document.querySelector("#recommend-form").hidden = true;
    showSiteError("This browser tab does not have a store URL Loot can read.");
    return;
  }

  document.querySelector("#recommend-form").hidden = false;
  merchantName.textContent = activeSite.name;
  merchantDomain.textContent = activeSite.hostname;
  loginSite.textContent = `Store detected: ${activeSite.name}`;
  renderLoading();
  await recommendWithToken(token);
}

async function recommendWithToken(token) {
  if (!activeSite || requestInProgress) return;
  const amount = Number(amountInput.value || EXAMPLE_AMOUNT);
  requestInProgress = true;
  showSiteError("");
  renderLoading();
  try {
    const data = await request("/route/", {
      method: "POST",
      token,
      body: { merchant_name: activeSite.name, amount, currency: "INR", apple_pay_india: true },
    });
    renderRecommendation(data);
  } catch (error) {
    if (error.message.includes("Invalid or expired token")) {
      await chrome.storage.local.remove(TOKEN_KEY);
      showView("login");
      showLoginError("Your Loot session expired. Sign in again.");
    } else {
      resultElement.innerHTML = `<p class="result-eyebrow">COULDN’T COMPARE CARDS</p><span class="result-reason">${escapeHtml(error.message)}</span>`;
    }
  } finally {
    requestInProgress = false;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showLoginError("");
  loginButton.disabled = true;
  loginButton.textContent = "Signing in…";
  const form = new FormData(loginForm);
  try {
    const session = await request("/auth/login", {
      method: "POST",
      body: { username: form.get("username"), password: form.get("password") },
    });
    await chrome.storage.local.set({ [TOKEN_KEY]: session.access_token });
    await openAssistant(session.access_token);
  } catch (error) {
    showLoginError(error.message);
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = "Sign in to Loot";
  }
});

recommendForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const { [TOKEN_KEY]: token } = await chrome.storage.local.get(TOKEN_KEY);
  if (token) await recommendWithToken(token);
});

signoutButton.addEventListener("click", async () => {
  await chrome.storage.local.remove(TOKEN_KEY);
  showView("login");
});

async function initialize() {
  const tab = await getCurrentTab();
  if (tab?.url) {
    try {
      const parsed = new URL(tab.url);
      if (parsed.protocol === "http:" || parsed.protocol === "https:") {
        activeSite = {
          hostname: parsed.hostname.replace(/^www\./, ""),
          name: getMerchant(parsed.hostname, tab.title || ""),
        };
      }
    } catch {
      activeSite = null;
    }
  }

  if (activeSite) {
    loginSite.hidden = false;
    loginSite.textContent = `Store detected: ${activeSite.name}`;
  }

  const { [TOKEN_KEY]: token } = await chrome.storage.local.get(TOKEN_KEY);
  if (token) await openAssistant(token);
  else showView("login");
}

initialize().catch((error) => {
  showView("login");
  showLoginError(error.message || "Loot could not read this tab.");
});
