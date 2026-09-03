# 암호화폐 시세 데이터 소스 (crypto.html / fetchers/crypto_price.py)

## 현재 구성: 3단계 폴백

1. **CoinGecko** (1차, 기본) — `https://api.coingecko.com/api/v3/coins/markets`, 무료 Demo 플랜, 키 불필요.
2. **yfinance** (2차 폴백) — `BTC-USD` 등 Yahoo Finance 암호화폐 티커, 키 불필요. CoinGecko가 실패할 때만 사용.
3. **CoinMarketCap** (3차 폴백) — 무료 Basic 플랜, `CMC_API_KEY` 필요(GitHub Secret으로 등록). 1·2차가 둘 다 실패할 때만 호출.

세 소스 모두 같은 coingecko 스타일 id(`bitcoin`, `ethereum` 등)로 매핑해서 `crypto_prices` 테이블에 upsert하므로, 어느 소스로 수집되든 같은 코인은 같은 행에 저장된다. 어느 소스에서 왔는지는 `crypto_prices.source` 컬럼에 기록됨.

## ⚠️ 중요: CoinGecko 무료(Demo) 플랜은 상업적 이용 금지

2026-09-04 공식 약관(coingecko.com/en/api/pricing, coingecko.com/en/api_terms) 확인 결과:

> Demo 플랜은 **"Personal Use only, not for any commercial purpose"**로 명시돼 있음. 상업적 이용은 Basic 이상 유료 플랜부터 허용되며, 그때부터 "Data provided by CoinGecko" 표시 + `coingecko.com/en/api` 링크 의무가 생김.

**현재 판단 (2026-09-04 기준)**: moneyfinal은 AdSense·제휴 링크 등 어떤 형태의 광고/수익화도 붙어있지 않은 무료 정보 사이트라는 걸 코드베이스에서 직접 확인함(전체 검색 결과 광고 스크립트 없음). 사용자도 이를 확인해줌. 그래서 CoinGecko 무료 플랜을 1차로 계속 사용하는 것으로 판단함.

**⚠️ 다음 상황이 되면 반드시 재검토할 것:**
- AdSense, 제휴 링크(쿠팡파트너스 등), 유료 구독, 그 외 어떤 형태로든 사이트에 수익화 요소가 추가되는 경우
- → 이 시점부터 CoinGecko 무료 플랜은 약관 위반 소지가 있음. **CoinMarketCap을 1차로 승격**할 것을 권장 (무료 Basic 플랜이 상업적 이용을 명시적으로 허용하며, 월 15,000회/분당 50회 한도로 매일 배치 수집 용도엔 충분함). `fetchers/crypto_price.py`의 `fetch_markets()` 함수에서 우선순위만 바꾸면 됨(코드 구조는 이미 3단계 폴백으로 되어있어 순서 변경이 쉬움).
- CoinGecko 쪽에 유료 결제를 원치 않으면 그냥 CoinMarketCap Basic으로 전환하고 CoinGecko는 제거해도 됨.

## 검토했지만 채택 안 한 소스

- **CoinCap**: 예전 v2(키 불필요, 완전 무료)는 2025년에 폐지됨. v3부터는 API 키 필수 + USDC 기반 프리페이드 크레딧 시스템(x402 결제 프로토콜)으로 전환되어, 단순 일일 배치 수집 용도로는 과도하게 복잡함. 채택 안 함.

## 각 소스 필드 커버리지 차이

| 필드 | CoinGecko | yfinance | CoinMarketCap |
|---|---|---|---|
| 가격/시가총액/거래량/순위 | ✅ | ✅ | ✅ |
| 24시간 변동률 | ✅ | ✅ | ✅ |
| 7일 변동률 | ✅ | ❌ (비움) | ✅ |
| 코인 아이콘 이미지 | ✅ | ❌ (비움) | ❌ (비움, 별도 엔드포인트 필요) |
| 24h 고가/저가 | ✅ | ❌ (신뢰도 낮아 비움) | ❌ (해당 엔드포인트에 없음) |
| 사상 최고가(ATH) | ✅ | ❌ | ❌ |

폴백으로 갈수록 필드가 줄어들지만, `crypto_prices` 테이블 컬럼이 전부 nullable이고 `crypto.html`도 결측값을 `-`로 안전하게 표시하므로 폴백 발생 시에도 페이지는 정상 동작한다(다만 코인 아이콘이 안 보이거나 7일 변동률 칸이 `-`로 나올 수 있음).
