# 머니파이널 시스템 아키텍처

> 최종 검증: 2026-07-31 (레포 `thewisefrontier/moneyfinal` @ `main` 실물 조회 기준)
> 이 문서는 **실제 레포 상태를 조회해서 작성**했다. 추측 항목은 `⚠️ 미확인`으로 표시했다.

---

## 1. 개요

| 항목 | 값 |
|---|---|
| 서비스명 | 머니파이널 (슬로건: 세상의 모든 재테크) |
| 도메인 | `moneyfinal.pages.dev` |
| 레포 | `thewisefrontier/moneyfinal` (public), 기본 브랜치 `main` |
| 운영 | 1인 개발·운영 |
| 비용 | 제로비용 스택 (무료 티어만 사용) |

---

## 2. 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────┐
│ 외부 API                                                 │
│ finlife(금감원) · ECOS(한은) · FRED · Finnhub ·          │
│ Alpha Vantage · data.go.kr(금융위) · DART · FSS 오픈API  │
└────────────────────────┬────────────────────────────────┘
                         │ ① 수집
                         ▼
              ┌──────────────────────┐
              │ GitHub Actions       │  스케줄 + workflow_dispatch
              │ .github/workflows/   │  (28개 워크플로우)
              └──────────┬───────────┘
                         │ python fetchers/*.py
                         ▼
              ┌──────────────────────┐
              │ fetchers/ (39개)     │  API 호출 + 정규화
              │ utils/common.py      │  supabase_upsert()
              └──────────┬───────────┘
                         │ ② 적재 (upsert)
                         ▼
              ┌──────────────────────┐
              │ Supabase (싱가포르)   │  PostgreSQL
              │ 21개 테이블           │
              └──────────┬───────────┘
                         │ ③ 가공
                         ▼
              ┌──────────────────────┐
              │ processors/          │  kr_technical.py (RSI)
              │                      │  gemini_analyzer.py (AI 브리핑)
              └──────────┬───────────┘
                         │ ④ 내보내기
                         ▼
              ┌──────────────────────┐
              │ exporters/           │  export_data.py
              │ export_data.py       │  DB → data/*.json (8개)
              └──────────┬───────────┘
                         │ ⑤ git commit & push
                         ▼
              ┌──────────────────────┐
              │ Cloudflare Pages     │  main 브랜치 push 시 자동 배포
              │ 정적 HTML + JSON      │
              └──────────────────────┘
                         │ ⑥ 브라우저에서 fetch('/data/*.json')
                         ▼
                     사용자
```

**핵심 설계 원칙**: 런타임 서버가 없다. 프론트엔드는 순수 정적 HTML이며, 빌드 시점에 생성된 JSON 파일만 fetch한다. Supabase는 수집 파이프라인 내부에서만 접근하고 브라우저에 노출되지 않는다.

---

## 3. 디렉터리 구조

```
moneyfinal/
├─ .github/workflows/     28개 YAML — 수집 스케줄
├─ fetchers/              39개 .py — 외부 API 호출 → Supabase upsert
├─ processors/            2개 .py — DB 데이터 가공
│   ├─ kr_technical.py      국내주식 RSI(14) 계산
│   └─ gemini_analyzer.py   Gemini 기반 일일 브리핑 생성
├─ exporters/
│   ├─ export_data.py       Supabase → data/*.json
│   └─ telegram_sender.py   텔레그램 알림 발송
├─ utils/
│   └─ common.py            공통 유틸 (아래 §6)
├─ data/                  export 산출물 JSON 8개 (git 커밋됨)
├─ *.html                 정적 페이지 (아래 §7)
├─ requirements.txt
├─ robots.txt / sitemap.xml / _redirects / favicon.svg
└─ privacy.html / terms.html / about.html
```

---

## 4. 스케줄 (GitHub Actions)

### 4.1 정기 실행

| 워크플로우 | cron (UTC) | KST | 실행 내용 |
|---|---|---|---|
| `daily.yml` | `0 22 * * *` | 매일 07:00 | 아래 §4.2 파이프라인 |
| `fetch_bank_rates.yml` | `0 23 20 * *` | 매월 21일 08:00 | `bank_rates.py` → export |
| `fetch_loan_rates.yml` | `0 23 20 * *` | 매월 21일 08:00 | `loan_rates.py` → `annuity_savings.py` |
| `fetch_insurance.yml` | `0 0 21 * *` | 매월 21일 09:00 | `insurance_info.py` → export |
| `monthly.yml` | `0 0 1 * *` | 매월 1일 09:00 | `ecos_m2.py` → export |
| `quarterly.yml` | `0 0 1 1,4,7,10 *` | 1/4/7/10월 1일 09:00 | `ecos_household_credit` → `fdi_stats` → `corp_finance` → `bank_stats` → `financial_corp_info` → export |
| `rate.yml` | `0 23 16 7 *` / `0 23 27 8 *` / `0 23 22 10 *` / `0 23 26 11 *` | 금통위 전일 08:00 | `ecos_base_rate.py` → export |

> ⚠️ **`rate.yml`은 2026년 금통위 일정이 하드코딩되어 있다. 매년 10월경 다음 해 일정으로 수동 갱신 필요.**

### 4.2 `daily.yml` 실행 순서

```
us_stocks → us_technical → stock_prices → kr_technical
→ dart_disclosure → ecos_daily → fred_global
→ gold_price → oil_price
→ isa_info → kofia_stats → krx_index
→ fss_jobs → bond_info
→ gemini_analyzer → export_data
→ git commit & push (Cloudflare Pages 자동 배포)
```

### 4.3 수동 전용 (`workflow_dispatch`만, 스케줄 없음)

`backfill_stocks` (국내주식 히스토리 백필) · `fetch_bank_stats` · `fetch_bond_info` · `fetch_corp_finance` · `fetch_derivatives` · `fetch_disclosure_alerts` · `fetch_financial_corp` · `fetch_fund` · `fetch_governance` · `fetch_stock_prices` · `fetch_us_technical` · `fix_ticker_sticky` · `run_export` (긴급 export)

**FSS 오픈API 계열 (전부 수동)**: `fss_news` (fss_info + fss_fintip) · `fetch_fss_bank_stats` · `fetch_fss_consumer_news` · `fetch_fss_foreign_invest` · `fetch_fss_market_trend` · `fetch_fss_press` · `fetch_fss_realm_general` · `fetch_fss_realm_sector`

> 수동 트리거 방법: 워크플로우 페이지 → "Run workflow" 토글 클릭 → **드롭다운이 열린 뒤** 초록색 제출 버튼 클릭. (토글 전에 제출 버튼을 찾으면 잘못된 요소가 선택된다.)

---

## 5. 데이터 계층 (Supabase)

리전: 싱가포르. 접근은 서비스 롤 키로 PostgREST 경유.

### 5.1 테이블 및 upsert 충돌 키

`utils/common.py`의 `CONFLICT_COLUMNS`가 단일 진실 공급원이다.

| 테이블 | conflict 키 |
|---|---|
| `rates` | institution, product_name, category, period |
| `market_indicators` | indicator_code, reference_date |
| `corporate_alerts` | company_name, alert_type, disclosure_date |
| `ipo_status` | company_name, status, request_date |
| `financial_health` | institution, reference_date |
| `daily_briefing` | briefing_date |
| `stock_prices` | stock_code, base_date, market_type |
| `stock_short` | stock_code, base_date |
| `stock_dividends` | stock_code, base_date, dividend_type |
| `stock_issuance` | stock_code, issuance_date, issuance_type |
| `stocks` | stock_code |
| `corp_info` | stock_code |
| `corp_finance` | stock_code, fiscal_year |
| `fss_news` | category, title, post_date |
| `fss_jobs` | company_name, title, post_date |
| `mortgage_loans` | fin_co_no, fin_prdt_cd, mrtg_type, rpay_type, lend_rate_type |
| `rent_loans` | fin_co_no, fin_prdt_cd, rpay_type, lend_rate_type |
| `credit_loans` | fin_co_no, fin_prdt_cd, crdt_prdt_type, crdt_lend_rate_type |
| `business_loans` | fin_co_no, fin_prdt_cd |
| `annuity_savings` | fin_co_no, fin_prdt_cd |

### 5.2 신규 테이블 생성 시 필수 권한

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON [테이블] TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
-- 향후 생성 테이블 자동 적용
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO service_role;
```

### 5.3 컬럼 주의사항

- `rates.rate`, `rates.max_rate` → `NUMERIC(9,4)` (실손보험 손해율이 999.99%를 넘는 경우 대응)
- `rates` 테이블은 예적금·저축은행·CMA·파킹·펀드·**실손보험**을 함께 담는다. 실손보험 행의 `rate`/`max_rate`는 금리(%)가 아니라 **기준 보험료(원 단위)**다. 순위·평균 계산 시 반드시 제외해야 한다.

---

## 6. `utils/common.py` — 공통 계층

모든 fetcher가 의존하는 단일 유틸 모듈.

| 함수 | 역할 |
|---|---|
| `data_go_kr_get(url, service_key, params)` | 공공데이터포털 호출. `params`로 키 전달해 이중 인코딩 방지 |
| `fss_open_api_get(jsp_name, auth_key, days_back)` | 금감원 오픈API 호출 (authKey 방식) |
| `supabase_upsert(table, data)` | 배치 upsert. conflict 키 기준 배치 내 중복 자동 제거 |
| `supabase_select(table, params)` | 단일 조회 (PostgREST 1000행 제한 적용) |
| `supabase_select_all(table, params, page_size=1000, max_pages=20)` | 페이지네이션 조회. 1000행 초과 테이블용 |
| `now_kst()` / `today_kst()` | KST 타임스탬프 |

**실패 처리**: `_UPSERT_FAILURES` 카운터 + `atexit` 훅으로, upsert가 하나라도 실패하면 모든 작업을 마친 뒤 **non-zero exit**한다. 워크플로우가 실패를 green으로 위장하지 않도록 하는 장치다.

**환경변수 (코드가 읽는 이름)**: `SUPABASE_URL`, `SUPABASE_KEY`, `DATA_GO_KR_API_KEY`, `FINLIFE_API_KEY`, `FSS_API_KEY`, `ECOS_API_KEY`, `DART_API_KEY`, `FRED_API_KEY`, `FINNHUB_API_KEY`, `ALPHA_VANTAGE_API_KEY`, `GEMINI_API_KEY`

**GitHub Secret ↔ 환경변수 매핑 (주의)**:
- `secrets.SUPABASE_SERVICE_KEY` → 코드는 `SUPABASE_KEY`로 읽음
- `secrets.DATA_GO_KR_API_KEY_DEC` → 코드는 `DATA_GO_KR_API_KEY`로 읽음 (**DEC = 디코딩 키. ENC를 URL에 직접 삽입하면 이중 인코딩 버그**)
- 상세는 프로젝트 파일 `API_KEY_REFERENCE.md` 참조

---

## 7. 내보내기 계층 (`exporters/export_data.py`)

Supabase → `data/*.json` 8개 파일 생성. `main()`이 아래 순서로 호출한다.

| 함수 | 산출 파일 | 소스 테이블 | 필터 |
|---|---|---|---|
| `export_rates()` | `rates.json` | `rates` | **40일 cutoff**, `max_rate.desc` |
| `export_market()` | `market.json` | `market_indicators` | 전체 조회 후 `indicator_code`별 최신값만 dedupe |
| `export_briefing()` | `briefing.json` | `daily_briefing` | `is_published=true`, 최근 7건 |
| `export_corporate_alerts()` | `alerts.json` | `corporate_alerts` | `is_published=true`, 최근 100건 |
| `export_stocks()` | `stocks.json` | `stock_prices` | KOSPI 100 / KOSDAQ 100 / US 50, `base_date.desc,market_cap.desc` |
| `export_corp_finance()` | `corp_finance.json` | `corp_finance` | 최근 50건 |
| `export_loans()` | `loans.json` | `mortgage_loans` / `rent_loans` / `credit_loans` / `business_loans` | **40일 cutoff** |
| `export_annuity()` | `annuity.json` | `annuity_savings` | **40일 cutoff**, `avg_prft_rate.desc` |

### 40일 cutoff 설계 이유 (중요)

fetcher는 upsert만 수행하므로, API에서 사라진(공시 중단된) 상품이 DB에 영구히 남는다.
월 1회 수집 주기 + 실패 버퍼를 고려해 **최근 40일 내 재수집된 행만** export하여 현재 공시 중인 상품만 노출한다.
→ **일별 수집 테이블에는 3일 cutoff, 월별 수집 테이블(대출·연금저축·예적금)에는 40일 cutoff**를 쓴다.

### `market.json` 전체 조회 설계 이유

`limit 500` 방식은 `BASE_RATE`처럼 갱신 빈도가 낮은 지표가 최근 N행 밖으로 밀려 누락되는 문제가 있었다. 전체 히스토리를 조회한 뒤 코드별 최신값만 남기는 방식으로 교체했다.

---

## 8. 프론트엔드

Cloudflare Pages가 `main` 브랜치 push를 감지해 자동 배포한다. 빌드 스텝 없음 (정적 파일 그대로 서빙).

### 8.1 데이터 페이지

| 파일 | 내용 | 소비 JSON |
|---|---|---|
| `index.html` | 메인 | 복수 |
| `rates.html` | 예적금 금리 | `rates.json` |
| `loans.html` | 대출 4종 탭 (주담대/전세/신용/사업자) | `loans.json` |
| `annuity.html` | 연금저축 | `annuity.json` |
| `savings.html` | 저축·ISA | `rates.json` |
| `insurance.html` | 실손보험 | `rates.json` |
| `market.html` | 시장 대시보드 | `market.json` |
| `macro.html` | 거시지표 | `market.json` |
| `invest.html` | AI 일일 브리핑 | `briefing.json` |
| `company.html` | 기업 정보 | `corp_finance.json` / `stocks.json` |

### 8.2 계산기 (`calc.html` 허브 + 12개)

`calc-age` · `calc-date` · `calc-fire` (FIRE 은퇴) · `calc-freelancer` · `calc-fx` · `calc-interest` · `calc-loan` · `calc-lotto-sim` · `calc-lotto-tax` · `calc-pyeong` · `calc-realty` · `calc-salary`

전부 클라이언트 사이드 JS 계산. API 의존 없음.

### 8.3 SEO / 정책

`robots.txt` · `sitemap.xml` · `favicon.svg` · `_redirects` · canonical/og/twitter/JSON-LD 일괄 적용 · `privacy.html` · `terms.html` · `about.html`

---

## 9. 데이터 소스별 제약

| 소스 | 인증 | 제약 |
|---|---|---|
| finlife (금감원 금융상품한눈에) | `auth` | 필드명은 프로젝트 파일 `금융감독원_금융상품_한눈에_API_상세.txt`가 최종 권위 |
| ECOS (한국은행) | 키를 **URL 경로**에 삽입 | `/api/StatisticSearch/{KEY}/json/...` |
| data.go.kr (금융위 등) | `serviceKey` (params로 전달) | 응답 필드는 `docs/API_FIELDS.md` 참조 |
| DART | `crtfc_key` | 평문 |
| FRED | `api_key` | 평문 |
| Finnhub | - | 무료 60 calls/min |
| Alpha Vantage | - | 무료 **25 calls/day** → `us_technical.py`는 5종목만, 호출 간 12초 딜레이 |
| FSS 오픈API (www.fss.or.kr) | `authKey` | **1일 30회 제한**, 1회 최대 1개월 조회. JSON 최상위 키가 `"reponse"` (오타, `response` 아님) |
| Gemini | - | 모델 `gemini-3.1-flash-lite`, temperature 0.1, 제공 데이터만 사용하는 할루시네이션 방지 프롬프트 |

### 사용 금지 (라이선스)

- **Stooq** — 약관 5.3조 재배포 금지 + S&P DJ 지수 개인·비상업 한정 (2026-07-05 확인)
- **공공누리 Type 2 미만** API 전반 (비영리 + 변경금지)
  - 한국예탁결제원(KSD) 계열: 채권발행, 공매도, 배당, 주식권리, 주식발행
  - 금융위 DR 국제거래종목정보 `GetDrTradItemInfoService_V2` (`intl_stocks.py` 폐기됨)
- **CMA 개별 상품 금리**: 공식 공공 API로 수집 불가 (finlife는 은행 예적금만, KOFIA는 시장 잔고 통계만)

---

## 10. 작업 규칙

### GitHub 파일 수정
1. 수정 전 **매번** `get_file_contents`로 최신 SHA 재조회 → `create_or_update_file`에 명시. **세션 내 이전 SHA 재사용 금지** (충돌 오류)
2. 신규 파일 여러 개 동시 생성은 `push_files` (SHA 불필요)
3. 경로를 모를 때는 추측하지 말고 루트(`.`)부터 조회
4. `raw.githubusercontent.com`은 CDN 캐시 지연이 있다. 내용 **검증**은 MCP 도구로 할 것
5. 파일 **삭제**는 GitHub 웹 UI에서 직접 처리 (도구로 삭제하지 않음)

### 대량 HTML 일괄 수정 패턴
Python 패치 스크립트 + 임시 YAML 워크플로우를 `push_files`로 한 번에 커밋
→ `workflow_dispatch` 수동 트리거 → 완료 후 두 파일 삭제.
스크립트에 `assert`로 수정 파일 수를 검증해 불일치 시 커밋 전 중단시킨다.

### API 사용
- 엔드포인트명·필드명·서비스명은 **반드시 공식 가이드로 확인 후 사용. 추측 금지.**
- FSS 오픈API JSP 파일명은 저장된 값이 틀렸을 가능성이 있어 **실행 전 매번 공식 가이드 재확인**

---

## 11. 미해결 이슈

| 이슈 | 내용 |
|---|---|
| `annuity_savings` 금융투자 섹터 | 섹터코드 `060000`에서 0건 수집 + 2분 타임아웃. 페이지네이션·오류처리 검토 필요 |
| 미검증 fetcher | `bank_stats` · `bond_info` · `derivatives_info` · `financial_corp_info` · `fund_info` · `governance_info` · `insurance_info` · `us_technical` 등이 수동 트리거만 있고 정기 스케줄에 미통합 |
| FSS 오픈API 10종 | fetcher 파일은 존재하나 전부 수동. 1일 30회 제한 탓에 스케줄 설계 필요 |
| 주식 데이터 누락 9개 기업 | data.go.kr `crno` 검증으로 해결 예정 |
| 유럽 지수 (DAX/FTSE/CAC) | Stooq 사용 금지로 대안 소스 미확보. 보류 |
| 핫딜 기능 | 제휴 API vs. 크롤링 방향 미확정 |
| AdSense | 기존 사이트로 먼저 승인 → 개인 도메인 서브도메인으로 머니파이널 추가 (pages.dev 서브도메인은 거절 위험) |

---

## 12. 관련 문서

| 문서 | 위치 | 내용 |
|---|---|---|
| `API_KEY_REFERENCE.md` | 프로젝트 파일 | Secret ↔ 환경변수 매핑, 모델명 |
| `금융감독원_금융상품_한눈에_API_상세.txt` | 프로젝트 파일 | finlife 필드명 (최종 권위) |
| `API개발명세서_통계조회조건.xls` | 프로젝트 파일 | ECOS StatisticSearch 명세 |
| `통계표_28153634.xlsx` | 프로젝트 파일 | ECOS 통계표 코드 935개 |
| `API_FIELDS.md` | (커밋 예정) `docs/` | 공공데이터 오픈API 22종 엔드포인트·필드 압축본 |
| `ARCHITECTURE.md` | (커밋 예정) `docs/` | 본 문서 |
