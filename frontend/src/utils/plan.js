// Central plan gating config & helpers
// Plans: free < pro < elite
export const PLAN_LEVELS = { free: 0, pro: 1, elite: 2 };

export const STRIPE_LINKS = {
  pro: 'https://buy.stripe.com/14AbJ3akQ9HCgDB8U4bbG02',
  elite: 'https://buy.stripe.com/4gMeVffFa3jecnlfisbbG03',
};

export const PLAN_PRICES = {
  pro: 4.99,
  elite: 9.99,
};

// Feature → minimum plan required
export const FEATURE_PLAN = {
  // Free (always unlocked)
  transactions: 'free',
  goals: 'free',
  health_score_basic: 'free',
  insights: 'free',
  jars_limited: 'free', // 1 jar only on free

  // Pro
  budgets: 'pro',
  zero_budget: 'pro',
  loans: 'pro',
  credit_cards: 'pro',
  sip_rd: 'pro',
  jars_unlimited: 'pro',
  lend_borrow: 'pro',
  tax_basic: 'pro', // 80C/80D + ITR + calendar
  weekly_digest: 'pro',
  subscription_detector: 'pro',
  daily_limit: 'pro',
  export_pdf_csv: 'pro',
  health_score_full: 'pro',

  // Elite
  debt_payoff: 'elite',
  investments: 'elite',
  real_estate: 'elite',
  net_worth: 'elite',
  ai_chat: 'elite',
  form_26as: 'elite',
};

export const hasAccess = (userPlan, feature) => {
  const required = FEATURE_PLAN[feature] || 'free';
  return PLAN_LEVELS[userPlan || 'free'] >= PLAN_LEVELS[required];
};

export const requiredPlanFor = (feature) => FEATURE_PLAN[feature] || 'free';

export const stripeLinkFor = (plan, email) => {
  const base = STRIPE_LINKS[plan];
  if (!base) return '#';
  return email ? `${base}?prefilled_email=${encodeURIComponent(email)}` : base;
};

// Jars free-tier cap
export const FREE_LIMITS = {
  jars: 1,
  goals: 1,
  transactions_per_month: 50,
};
