-- moneyfinal D1 초기 스키마
-- Supabase(Postgres) 원본 스키마를 SQLite/D1 방언으로 변환.
-- 타입 매핑: bigint/int4/int2->INTEGER, varchar/text->TEXT, numeric->REAL,
--            date/timestamptz->TEXT(ISO8601), boolean->INTEGER(0/1), jsonb->TEXT(JSON 문자열)
-- id 컬럼은 원본이 identity/serial이든 아니든 D1에서는 모두 INTEGER PRIMARY KEY AUTOINCREMENT로
-- 통일 (기존 upsert 경로가 id를 payload에 넣지 않고 on_conflict 대상 컬럼만으로 동작하므로 안전).
--
-- 주의(원본 DB에서 그대로 확인된 불일치, 고치지 않고 그대로 이식함 - 별도 확인 필요):
--   - stock_dividends: 코드(CONFLICT_COLUMNS)는 'stock_code,base_date,dividend_type'로 upsert하지만
--     실제 Postgres UNIQUE 인덱스는 (stock_code, base_date) 2컬럼뿐. 여기서도 실제 DB 제약을 따름.
--   - stock_issuance: 코드는 'stock_code,issuance_date,issuance_type'로 upsert하지만
--     Postgres에는 PK(id) 외에 UNIQUE 인덱스가 전혀 없음(=on_conflict 대상이 없어 PostgREST가
--     42P10 오류를 냈을 가능성이 높음, 즉 이 테이블은 실질적으로 upsert가 성공한 적이 없을 수 있음).
--     D1에서는 코드가 요구하는 3컬럼 UNIQUE를 새로 만들어둠(막혀있던 기능이 D1에서는 살아날 수 있음
--     -> 배포 전 fetcher 쪽 실제 동작 재확인 권장).

CREATE TABLE annuity_savings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dcls_month TEXT, fin_co_no TEXT, kor_co_nm TEXT, fin_prdt_cd TEXT, fin_prdt_nm TEXT,
  join_way TEXT, pnsn_kind TEXT, pnsn_kind_nm TEXT, prdt_type TEXT, prdt_type_nm TEXT,
  sale_strt_day TEXT, mntn_cnt INTEGER, avg_prft_rate REAL, dcls_rate REAL, guar_rate REAL,
  btrm_prft_rate_1 REAL, btrm_prft_rate_2 REAL, btrm_prft_rate_3 REAL, etc TEXT, sale_co TEXT,
  sector TEXT, dcls_strt_day TEXT, source TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_annuity_savings_unique ON annuity_savings(fin_co_no, fin_prdt_cd);

CREATE TABLE business_loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dcls_month TEXT, fin_co_no TEXT, kor_co_nm TEXT, fin_prdt_cd TEXT, fin_prdt_nm TEXT,
  fin_prdt_type TEXT, fin_prdt_type_nm TEXT, loan_type TEXT, rpay_type TEXT, lend_rate_type TEXT,
  join_way TEXT, use_way TEXT, loan_limit TEXT, loan_limit_detl TEXT, join_deny TEXT,
  join_deny_detl TEXT, spcl_rate TEXT, loan_term TEXT, erly_rpay_fee TEXT, loan_inci_expn TEXT,
  dly_rate TEXT, cb_name TEXT,
  val1_grad_1 REAL, val1_grad_2 REAL, val1_grad_3 REAL, val1_grad_4 REAL, val1_grad_5 REAL,
  val1_grad_6 REAL, val1_grad_7 REAL, val1_grad_8 REAL, val1_grad_avg REAL,
  val2_grad_1 REAL, val2_grad_2 REAL, val2_grad_3 REAL, val2_grad_4 REAL, val2_grad_5 REAL,
  val2_grad_6 REAL, val2_grad_7 REAL, val2_grad_8 REAL, val2_grad_avg REAL,
  val3_grad_1 REAL, val3_grad_2 REAL, val3_grad_3 REAL, val3_grad_4 REAL, val3_grad_5 REAL,
  val3_grad_6 REAL, val3_grad_7 REAL, val3_grad_8 REAL, val3_grad_avg REAL,
  lend_rate_min REAL, lend_rate_max REAL, lend_rate_avg REAL,
  sector TEXT, dcls_strt_day TEXT, source TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_business_loans_unique ON business_loans(fin_co_no, fin_prdt_cd);

CREATE TABLE card_news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL, category TEXT, content_json TEXT, image_url TEXT,
  disclaimer TEXT DEFAULT '본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다.',
  telegram_sent INTEGER DEFAULT 0, published_at TEXT, created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE corp_finance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT NOT NULL, corp_name TEXT, base_date TEXT NOT NULL,
  fiscal_year INTEGER, fiscal_quarter INTEGER, report_type TEXT,
  revenue INTEGER, operating_profit INTEGER, net_profit INTEGER,
  total_assets INTEGER, total_liabilities INTEGER, total_equity INTEGER,
  per REAL, pbr REAL, roe REAL, roa REAL, debt_ratio REAL, eps REAL, bps REAL, dps REAL,
  dividend_yield REAL, fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_corp_finance_unique ON corp_finance(stock_code, fiscal_year);

CREATE TABLE corp_info (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT, corp_name TEXT NOT NULL, ceo_name TEXT, corp_no TEXT, biz_no TEXT,
  address TEXT, homepage TEXT, phone TEXT, industry_code TEXT, industry_name TEXT,
  fiscal_month INTEGER, listing_date TEXT, market_type TEXT,
  fetched_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_corp_info_code ON corp_info(stock_code);

CREATE TABLE corporate_alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT NOT NULL, stock_code TEXT, alert_type TEXT NOT NULL, value REAL,
  detail_text TEXT, dart_url TEXT, disclosure_date TEXT, source TEXT DEFAULT 'DART',
  is_published INTEGER DEFAULT 0, needs_review INTEGER DEFAULT 1,
  fetched_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_corporate_alerts_unique ON corporate_alerts(company_name, alert_type, disclosure_date);

CREATE TABLE credit_loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dcls_month TEXT, fin_co_no TEXT, kor_co_nm TEXT, fin_prdt_cd TEXT, fin_prdt_nm TEXT,
  join_way TEXT, cb_name TEXT, crdt_prdt_type TEXT, crdt_prdt_type_nm TEXT,
  crdt_lend_rate_type TEXT, crdt_lend_rate_type_nm TEXT,
  crdt_grad_1 REAL, crdt_grad_4 REAL, crdt_grad_5 REAL, crdt_grad_6 REAL, crdt_grad_10 REAL,
  crdt_grad_11 REAL, crdt_grad_12 REAL, crdt_grad_13 REAL, crdt_grad_avg REAL,
  sector TEXT, dcls_strt_day TEXT, source TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_credit_loans_unique ON credit_loans(fin_co_no, fin_prdt_cd, crdt_prdt_type, crdt_lend_rate_type);

CREATE TABLE crypto_prices (
  id TEXT PRIMARY KEY,
  symbol TEXT, name TEXT, image_url TEXT, current_price REAL, market_cap REAL,
  market_cap_rank INTEGER, total_volume REAL, high_24h REAL, low_24h REAL,
  change_pct_24h REAL, change_pct_7d REAL, circulating_supply REAL, ath REAL, ath_date TEXT,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now')), source TEXT DEFAULT 'CoinGecko'
);

CREATE TABLE daily_briefing (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  briefing_date TEXT NOT NULL, headline TEXT, rate_summary TEXT, market_summary TEXT,
  alert_summary TEXT, full_text TEXT, is_published INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_daily_briefing_unique ON daily_briefing(briefing_date);

CREATE TABLE etf_dividends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, ex_dividend_date TEXT NOT NULL, declaration_date TEXT,
  record_date TEXT, payment_date TEXT, amount REAL, fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_etf_dividends_unique ON etf_dividends(ticker, ex_dividend_date);

CREATE TABLE etf_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, net_assets REAL, expense_ratio REAL, dividend_yield REAL,
  inception_date TEXT, sectors TEXT, top_holdings TEXT, fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_etf_profiles_unique ON etf_profiles(ticker);

CREATE TABLE financial_health (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  institution TEXT NOT NULL, institution_type TEXT NOT NULL, bis_ratio REAL,
  delinquency_rate REAL, signal TEXT, reference_date TEXT, source TEXT NOT NULL,
  fetched_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_financial_health_unique ON financial_health(institution, reference_date);

CREATE TABLE fss_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT, title TEXT, post_date TEXT, deadline_date TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_fss_jobs_unique ON fss_jobs(company_name, title, post_date);

CREATE TABLE fss_news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL, title TEXT NOT NULL, content_summary TEXT, post_date TEXT,
  source_url TEXT, fetched_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_fss_news_unique ON fss_news(category, title, post_date);

CREATE TABLE ipo_status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT NOT NULL, status TEXT NOT NULL, market TEXT, request_date TEXT,
  decision_date TEXT, withdrawal_reason TEXT, source TEXT DEFAULT 'KIND', source_url TEXT,
  fetched_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_ipo_status_unique ON ipo_status(company_name, status, request_date);

CREATE TABLE kr_etf_dividends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, ex_dividend_date TEXT NOT NULL, amount REAL, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_kr_etf_dividends_unique ON kr_etf_dividends(ticker, ex_dividend_date);

CREATE TABLE kr_etf_prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, price REAL, change REAL, change_pct REAL, base_date TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_kr_etf_prices_unique ON kr_etf_prices(ticker);

CREATE TABLE market_indicators (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  indicator_code TEXT NOT NULL, indicator_name TEXT NOT NULL, category TEXT NOT NULL,
  value REAL, prev_value REAL, unit TEXT, signal TEXT, source TEXT NOT NULL,
  reference_date TEXT, summary_text TEXT,
  fetched_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_market_indicators_unique ON market_indicators(indicator_code, reference_date);

CREATE TABLE market_news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  headline TEXT NOT NULL, summary TEXT, source TEXT, url TEXT, category TEXT, image_url TEXT,
  published_at TEXT, fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_market_news_unique ON market_news(url);

CREATE TABLE mortgage_loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dcls_month TEXT, fin_co_no TEXT, kor_co_nm TEXT, fin_prdt_cd TEXT, fin_prdt_nm TEXT,
  join_way TEXT, loan_inci_expn TEXT, erly_rpay_fee TEXT, dly_rate TEXT, loan_lmt TEXT,
  mrtg_type TEXT, mrtg_type_nm TEXT, rpay_type TEXT, rpay_type_nm TEXT,
  lend_rate_type TEXT, lend_rate_type_nm TEXT,
  lend_rate_min REAL, lend_rate_max REAL, lend_rate_avg REAL,
  sector TEXT, dcls_strt_day TEXT, source TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_mortgage_loans_unique ON mortgage_loans(fin_co_no, fin_prdt_cd, mrtg_type, rpay_type, lend_rate_type);

CREATE TABLE rates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  institution TEXT NOT NULL, product_name TEXT NOT NULL, category TEXT NOT NULL,
  rate REAL NOT NULL, max_rate REAL, period TEXT, join_method TEXT, source TEXT NOT NULL,
  source_url TEXT, fetched_at TEXT DEFAULT (datetime('now')), is_published INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')),
  join_deny INTEGER, join_member TEXT, spcl_cnd TEXT, etc_note TEXT, max_limit INTEGER,
  mtrt_int TEXT, intr_rate_type_nm TEXT, rsrv_type_nm TEXT, dcls_strt_day TEXT,
  dcls_end_day TEXT, sector TEXT, fin_prdt_cd TEXT, dcls_month TEXT
);
CREATE UNIQUE INDEX idx_rates_unique ON rates(institution, product_name, category, period);

CREATE TABLE rent_loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dcls_month TEXT, fin_co_no TEXT, kor_co_nm TEXT, fin_prdt_cd TEXT, fin_prdt_nm TEXT,
  join_way TEXT, loan_inci_expn TEXT, erly_rpay_fee TEXT, dly_rate TEXT, loan_lmt TEXT,
  rpay_type TEXT, rpay_type_nm TEXT, lend_rate_type TEXT, lend_rate_type_nm TEXT,
  lend_rate_min REAL, lend_rate_max REAL, lend_rate_avg REAL,
  sector TEXT, dcls_strt_day TEXT, source TEXT, source_url TEXT, fetched_at TEXT
);
CREATE UNIQUE INDEX idx_rent_loans_unique ON rent_loans(fin_co_no, fin_prdt_cd, rpay_type, lend_rate_type);

CREATE TABLE stock_ai_reports (
  code TEXT PRIMARY KEY,
  market TEXT NOT NULL, corp_name TEXT NOT NULL, report_text TEXT NOT NULL, based_on TEXT,
  source TEXT DEFAULT 'Gemini (moneyfinal 자체 생성)', generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 주의: CONFLICT_COLUMNS는 'stock_code,base_date,dividend_type'을 쓰지만 원본 Postgres
-- UNIQUE 인덱스는 (stock_code, base_date)뿐이라 여기서도 원본 실제 제약을 그대로 이식함.
CREATE TABLE stock_dividends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT NOT NULL, stock_name TEXT, base_date TEXT NOT NULL, record_date TEXT,
  payment_date TEXT, dps REAL, dividend_type TEXT, fiscal_year INTEGER,
  fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_stock_dividends_unique ON stock_dividends(stock_code, base_date);

-- 주의: 원본 Postgres에는 PK(id) 외 UNIQUE 인덱스가 전혀 없어 코드의
-- on_conflict='stock_code,issuance_date,issuance_type' upsert가 원본에서 실패했을 가능성이 높음
-- (42P10). D1에서는 코드가 기대하는 대로 UNIQUE를 새로 만들어 정상 동작하게 함 - 배포 전 재확인 요망.
CREATE TABLE stock_issuance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT, corp_name TEXT, issuance_date TEXT, issuance_type TEXT,
  issuance_price REAL, issuance_quantity INTEGER, purpose TEXT,
  fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_stock_issuance_unique ON stock_issuance(stock_code, issuance_date, issuance_type);

CREATE TABLE stock_prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT NOT NULL, stock_name TEXT, base_date TEXT NOT NULL,
  close_price REAL, open_price REAL, high_price REAL, low_price REAL, vs REAL, flt_rt REAL,
  volume INTEGER, trade_amount INTEGER, market_cap INTEGER, shares_out INTEGER,
  market_type TEXT, fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_stock_prices_unique ON stock_prices(stock_code, base_date, market_type);
CREATE INDEX idx_stock_prices_market_date ON stock_prices(market_type, base_date, market_cap);

CREATE TABLE stock_short (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_code TEXT NOT NULL, stock_name TEXT, base_date TEXT NOT NULL,
  short_volume INTEGER, short_amount INTEGER, short_ratio REAL,
  fetched_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_stock_short_unique ON stock_short(stock_code, base_date);

CREATE TABLE stocks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  isin_code TEXT, stock_code TEXT, stock_name TEXT NOT NULL, market_type TEXT, industry TEXT,
  corp_name TEXT, listed_date TEXT, is_active INTEGER DEFAULT 1,
  fetched_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_stocks_code ON stocks(stock_code);

CREATE TABLE superinvestor_holdings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  investor_name TEXT NOT NULL, fund_name TEXT NOT NULL, cik TEXT NOT NULL, cusip TEXT NOT NULL,
  name_of_issuer TEXT NOT NULL, value_usd REAL NOT NULL, shares INTEGER NOT NULL DEFAULT 0,
  weight_pct REAL NOT NULL DEFAULT 0, period_of_report TEXT, source TEXT DEFAULT 'SEC EDGAR 13F',
  is_published INTEGER NOT NULL DEFAULT 1, fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
  ticker TEXT, investor_type TEXT NOT NULL DEFAULT 'concentrated'
);
CREATE UNIQUE INDEX idx_superinvestor_holdings_unique ON superinvestor_holdings(investor_name, cusip);

CREATE TABLE us_company_dividends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, ex_date TEXT NOT NULL, payment_date TEXT, amount REAL,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_us_company_dividends_unique ON us_company_dividends(ticker, ex_date);

CREATE TABLE us_company_earnings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, report_date TEXT NOT NULL, eps_estimated REAL, eps_actual REAL,
  revenue_estimated REAL, revenue_actual REAL, fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_us_company_earnings_unique ON us_company_earnings(ticker, report_date);

CREATE TABLE us_company_financials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, fiscal_year INTEGER NOT NULL, period TEXT NOT NULL,
  revenue REAL, gross_profit REAL, operating_income REAL, net_income REAL, eps REAL,
  total_assets REAL, total_liabilities REAL, total_equity REAL,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_us_company_financials_unique ON us_company_financials(ticker, fiscal_year, period);

CREATE TABLE us_company_profile (
  ticker TEXT PRIMARY KEY,
  name TEXT, sector TEXT, industry TEXT, description TEXT, ceo TEXT, website TEXT,
  exchange TEXT, ipo_date TEXT, employees INTEGER, market_cap INTEGER, image_url TEXT,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE us_company_splits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL, split_date TEXT NOT NULL, numerator REAL, denominator REAL,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_us_company_splits_unique ON us_company_splits(ticker, split_date);
