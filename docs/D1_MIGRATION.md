# moneyfinal: Supabase → Cloudflare D1 마이그레이션

## 배경
핫딜월드+머니파이널+뉴스파이널 전체 Cloudflare D1 무료 한도 점검 결과, 머니파이널은
배치 위주 저부하 구조라 D1(무료)로 옮겨도 안전하다고 판단됨. 뉴스파이널은 이미
Supabase 무료 한도를 두 번 초과한 이력이 있어 이번 이전 대상에서 제외.

## 이번 작업으로 만들어진 것
- `migrations/0001_init.sql` — Supabase 21개(관련 앱 테이블 34개) 스키마를 SQLite/D1
  방언으로 변환한 초기 마이그레이션. 컬럼명은 원본과 동일하게 유지.
- `utils/common.py` — Supabase REST API 대신 Cloudflare D1 HTTP API를 쓰도록 내부
  구현을 교체. **함수 이름(`supabase_upsert`, `supabase_select` 등)은 의도적으로
  그대로 유지** — 39개 fetcher + exporters/export_data.py + processors가 이 함수들을
  호출하는데, 이름까지 바꾸면 그 모든 호출부를 다 고쳐야 해서 이번 1차 작업 범위에서는
  뺐음. 필요하면 후속 작업으로 `db_upsert` 등으로 일괄 리네임 가능.
- `functions/api/company-info.js`, `crypto.js`, `market-news.js` — Supabase fetch
  호출을 D1 네이티브 바인딩(`env.DB.prepare(...).all()`)으로 교체.
- `wrangler.toml` — D1 바인딩(`DB` → `moneyfinal-db`) 선언. `database_id`는 실제 값으로
  채워야 함(아래 절차 참고).
- `scripts/backfill_to_d1.py` — Supabase에 있는 기존 데이터를 D1로 1회 복사하는 스크립트.
  멱등성 있음(여러 번 실행해도 안전, 최신값으로 덮어씀).

## 제가 직접 할 수 없었던 부분 (Cloudflare API 접근 권한 없음)
이 세션에는 Cloudflare API를 직접 호출할 수 있는 도구/토큰이 연결되어 있지 않아서,
아래는 **사용자님이 직접(로컬 터미널 또는 GitHub Actions에서) 실행**해야 합니다.

### 1. D1 데이터베이스 생성
```bash
npx wrangler login   # 최초 1회
npx wrangler d1 create moneyfinal-db
```
출력되는 `database_id`를 `wrangler.toml`의 `REPLACE_WITH_ACTUAL_D1_DATABASE_ID`에 채워넣기.

### 2. 스키마 적용
```bash
npx wrangler d1 execute moneyfinal-db --remote --file=migrations/0001_init.sql
```

### 3. Cloudflare Pages D1 바인딩 확인
`wrangler.toml`의 `[[d1_databases]]`를 Pages Git 연동 빌드가 자동으로 읽어가는지는
계정/버전에 따라 다를 수 있음 — **Cloudflare 대시보드 → Pages 프로젝트(moneyfinal)
→ Settings → Functions → D1 database bindings**에서 바인딩 이름 `DB`가 `moneyfinal-db`에
연결되어 있는지 반드시 확인. 안 잡혀 있으면 대시보드에서 수동으로 추가.

### 4. GitHub Actions 시크릿 등록
저장소 **Settings → Secrets and variables → Actions**에 아래 3개 추가:
| Secret | 설명 |
|---|---|
| `CF_ACCOUNT_ID` | Cloudflare 대시보드 우측 사이드바 Account ID (또는 `wrangler whoami`) |
| `CF_API_TOKEN` | D1:Edit 권한을 가진 API 토큰 (Cloudflare 대시보드 → My Profile → API Tokens) |
| `CF_D1_DATABASE_ID` | 1번 단계에서 나온 database_id |

기존 `SUPABASE_URL`/`SUPABASE_KEY`를 쓰던 워크플로우 14개(`daily.yml`,
`fetch_bank_rates.yml`, `fetch_loan_rates.yml`, `fetch_stock_ai_reports.yml`,
`fetch_superinvestor_13f.yml`, `monthly.yml`, `quarterly.yml`, `rate.yml`,
`run_export.yml`, `backfill_stocks.yml`, `fetch_fss_bank_stats.yml`,
`fix_ticker_sticky.yml`, `audit_secrets.yml`, `fetch_insurance.yml`(현재 비활성))의
`env:` 블록을 `SUPABASE_URL`/`SUPABASE_KEY` → `CF_ACCOUNT_ID`/`CF_API_TOKEN`/
`CF_D1_DATABASE_ID`로 교체해야 함. (이 PR에서 아직 안 했다면 별도 커밋 확인)

### 5. 기존 데이터 백필 (1회)
```bash
SUPABASE_URL=... SUPABASE_KEY=... \
CF_ACCOUNT_ID=... CF_API_TOKEN=... CF_D1_DATABASE_ID=... \
python scripts/backfill_to_d1.py
```
34개 테이블 전체를 순서대로 옮김. 특정 테이블만 다시 돌리려면
`python scripts/backfill_to_d1.py rates market_indicators` 처럼 인자로 지정.

### 6. 검증
- `npx wrangler d1 execute moneyfinal-db --remote --command="SELECT COUNT(*) FROM stock_prices"` 등으로
  Supabase 쪽 행 수(`rates` 2,932 / `stock_prices` 215,983 / `superinvestor_holdings` 9,596 등,
  2026-09-23 기준 실측치)와 대조.
- 워크플로우 1개(예: `daily.yml`)를 `workflow_dispatch`로 수동 실행해 에러 없이 끝나는지 확인.
- `functions/api/crypto.js` 등 게이트웨이가 실제로 D1에서 값을 반환하는지 curl로 확인.
- 문제없이 며칠 안정화되면 Supabase 프로젝트(`ygnwfkvjjjfqrsqbymdp`)는 정지(pause) 또는 삭제.

## 확인이 필요한 기존 데이터 불일치 (제가 고치지 않고 그대로 이식함)
Supabase 실제 스키마를 조회하다 발견한 것 — `migrations/0001_init.sql` 상단 주석에도 적어둠.
- **stock_dividends**: 코드(`CONFLICT_COLUMNS`)는 `stock_code,base_date,dividend_type` 3컬럼으로
  upsert하지만 실제 Postgres UNIQUE 인덱스는 `(stock_code, base_date)` 2컬럼뿐. D1에서도 실제
  DB 제약(2컬럼)을 그대로 이식함 — 원래 의도가 3컬럼이었다면 여기서 한 번 짚고 넘어가야 함.
- **stock_issuance**: 코드는 3컬럼(`stock_code,issuance_date,issuance_type`)으로 upsert를 시도하는데
  원본 Postgres에는 PK(id) 외에 UNIQUE 인덱스가 전혀 없음 — PostgREST에서 이 upsert가 실제로는
  매번 42P10 오류로 실패했을 가능성이 있음(현재 테이블 행 수 0건인 것과 일치). D1 스키마에는
  코드가 기대하는 3컬럼 UNIQUE를 새로 만들어뒀으니, D1 이전 후에는 이 upsert가 (원본과 달리)
  정상 동작하기 시작할 수 있음 — fetcher 쪽 의도와 맞는지 확인 필요.
- **card_news** 테이블은 `CONFLICT_COLUMNS`에 없어(=upsert 대상이 아님) 이번 백필 스크립트
  대상에서 제외했음. 실제로 쓰는 코드가 있는지 확인 후 필요하면 별도 처리.
