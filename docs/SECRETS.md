# 시크릿 / 환경변수 감사 결과

> ⚠️ **이 파일은 `scripts/audit_secrets.py`가 생성한다. 직접 편집하지 말 것.**
> 워크플로우나 코드를 바꾼 뒤 `python scripts/audit_secrets.py`를 실행해 갱신한다.

## 🚨 점검 결과

### 미실행 모듈이 읽는 환경변수 (참고)
아직 어떤 워크플로우에서도 실행되지 않는 코드다. 지금은 장애가 아니지만,
스케줄에 편입할 때 반드시 `env:`에 추가해야 한다.

| 환경변수 | 읽는 파일 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | `exporters/telegram_sender.py` |
| `TELEGRAM_CHANNEL_ID` | `exporters/telegram_sender.py` |

---

## 매핑표 (GitHub Secret → 환경변수 → 사용 파일)

| GitHub Secret | 코드가 읽는 이름 | 사용 파일 |
|---|---|---|
| `ALPHA_VANTAGE_API_KEY` | `ALPHA_VANTAGE_API_KEY` | `fetchers/etf_profile.py`, `fetchers/us_technical.py` |
| `ALPHA_VANTAGE_API_KEY_2` | `ALPHA_VANTAGE_API_KEY_2` | `fetchers/etf_dividends.py` |
| `DART_API_KEY` | `DART_API_KEY` | `fetchers/dart_disclosure.py` |
| `DATA_GO_KR_API_KEY_DEC` | `DATA_GO_KR_API_KEY` | `fetchers/bank_stats.py`, `fetchers/bond_info.py`, `fetchers/corp_finance.py`, `fetchers/derivatives_info.py`, `fetchers/disclosure_alerts.py`, `fetchers/emission_price.py`, `fetchers/fdi_stats.py`, `fetchers/financial_corp_info.py`, `fetchers/fund_info.py`, `fetchers/gold_price.py`, `fetchers/governance_info.py`, `fetchers/insurance_info.py`, `fetchers/isa_info.py`, `fetchers/kofia_stats.py`, `fetchers/krx_index.py`, `fetchers/oil_price.py`, `fetchers/stock_prices.py` |
| `ECOS_API_KEY` | `ECOS_API_KEY` | `fetchers/ecos_base_rate.py`, `fetchers/ecos_daily.py`, `fetchers/ecos_household_credit.py`, `fetchers/ecos_m2.py` |
| `FINLIFE_API_KEY` | `FINLIFE_API_KEY` | `fetchers/annuity_savings.py`, `fetchers/bank_rates.py`, `fetchers/loan_rates.py` |
| `FINNHUB_API_KEY` | `FINNHUB_API_KEY` | `fetchers/etf_prices.py`, `fetchers/us_stocks.py` |
| `FRED_API_KEY` | `FRED_API_KEY` | `fetchers/fred_global.py` |
| `FSS_API_KEY` | `FSS_API_KEY` | `fetchers/fss_bank_stats_fisis.py`, `fetchers/fss_consumer_news.py`, `fetchers/fss_fintip.py`, `fetchers/fss_foreign_invest.py`, `fetchers/fss_info.py`, `fetchers/fss_jobs.py`, `fetchers/fss_market_trend.py`, `fetchers/fss_press.py`, `fetchers/fss_realm_general.py`, `fetchers/fss_realm_sector.py` |
| `GEMINI_API_KEY` | `GEMINI_API_KEY` | `processors/gemini_analyzer.py` |
| `SUPABASE_SERVICE_KEY` | `SUPABASE_KEY` | `utils/common.py` |
| `SUPABASE_URL` | `SUPABASE_URL` | `utils/common.py` |
| — (미주입) | `TELEGRAM_BOT_TOKEN` | `exporters/telegram_sender.py` |
| — (미주입) | `TELEGRAM_CHANNEL_ID` | `exporters/telegram_sender.py` |

---

## 워크플로우별 주입 환경변수

| 워크플로우 | 실행 스크립트 | 주입 환경변수 |
|---|---|---|
| `audit_secrets.yml` | `scripts/audit_secrets.py` | — |
| `backfill_stocks.yml` | `fetchers/stock_prices.py`, `processors/kr_technical.py` | `DATA_GO_KR_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `daily.yml` | `fetchers/us_stocks.py`, `fetchers/us_technical.py`, `fetchers/stock_prices.py`, `processors/kr_technical.py`, `fetchers/dart_disclosure.py`, `fetchers/ecos_daily.py`, `fetchers/fred_global.py`, `fetchers/crypto_price.py`, `fetchers/gold_price.py`, `fetchers/oil_price.py`, `fetchers/emission_price.py`, `fetchers/isa_info.py`, `fetchers/kofia_stats.py`, `fetchers/krx_index.py`, `fetchers/fss_jobs.py`, `fetchers/bond_info.py`, `fetchers/derivatives_info.py`, `fetchers/disclosure_alerts.py`, `fetchers/fund_info.py`, `fetchers/governance_info.py`, `fetchers/fss_info.py`, `fetchers/fss_fintip.py`, `fetchers/fss_press.py`, `fetchers/fss_consumer_news.py`, `fetchers/fss_realm_sector.py`, `fetchers/fss_realm_general.py`, `fetchers/fss_foreign_invest.py`, `fetchers/fss_market_trend.py`, `fetchers/etf_dividends.py`, `fetchers/etf_prices.py`, `fetchers/etf_profile.py`, `processors/gemini_analyzer.py`, `exporters/export_data.py` | `ALPHA_VANTAGE_API_KEY`, `ALPHA_VANTAGE_API_KEY_2`, `DART_API_KEY`, `DATA_GO_KR_API_KEY`, `ECOS_API_KEY`, `FINNHUB_API_KEY`, `FRED_API_KEY`, `FSS_API_KEY`, `GEMINI_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `fetch_bank_rates.yml` | `fetchers/bank_rates.py`, `exporters/export_data.py` | `FINLIFE_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `fetch_fss_bank_stats.yml` | `fetchers/fss_bank_stats_fisis.py` | `FSS_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `fetch_insurance.yml` | `fetchers/insurance_info.py`, `exporters/export_data.py` | `DATA_GO_KR_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `fetch_loan_rates.yml` | `fetchers/loan_rates.py`, `fetchers/annuity_savings.py` | `FINLIFE_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `fix_ticker_sticky.yml` | — | — |
| `monthly.yml` | `fetchers/ecos_m2.py`, `fetchers/bank_stats.py`, `fetchers/financial_corp_info.py`, `exporters/export_data.py` | `DATA_GO_KR_API_KEY`, `ECOS_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `quarterly.yml` | `fetchers/ecos_household_credit.py`, `fetchers/fdi_stats.py`, `fetchers/corp_finance.py`, `exporters/export_data.py` | `DATA_GO_KR_API_KEY`, `ECOS_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `rate.yml` | `fetchers/ecos_base_rate.py`, `exporters/export_data.py` | `ECOS_API_KEY`, `SUPABASE_KEY`, `SUPABASE_URL` |
| `run_export.yml` | `exporters/export_data.py` | `SUPABASE_KEY`, `SUPABASE_URL` |

