# 암호화폐 시세 데이터 소스 (crypto.html / fetchers/crypto_price.py)

## 현재 구성: 3단계 폴백

1. **CoinMarketCap** (1차, 기본) — 무료 Basic 플랜, `CMC_API_KEY` 필요(GitHub Secret으로 등록됨). 상업적 이용이 명시적으로 허용된 소스라 라이선스 걱정 없이 1차로 둠.
2. **yfinance** (2차 폴백) — `BTC-USD` 등 Yahoo Finance 암호화폐 티커, 키 불필요. CoinMarketCap이 실패(키 없음/장애/한도 초과 등)할 때만 사용.
3. **CoinGecko** (3차 폴백) — `https://api.coingecko.com/api/v3/coins/markets`, 무료 Demo 플랜, 키 불필요. 1·2차가 둘 다 실패할 때만 호출.

세 소스 모두 같은 coingecko 스타일 id(`bitcoin`, `ethereum` 등)로 매핑해서 `crypto_prices` 테이블에 upsert하므로, 어느 소스로 수집되든 같은 코인은 같은 행에 저장된다. 어느 소스에서 왔는지는 `crypto_prices.source` 컬럼에 기록됨.

## 왜 CoinMarketCap을 1차로 뒀나

2026-09-04 공식 약관(coingecko.com/en/api/pricing, coingecko.com/en/api_terms) 확인 결과, **CoinGecko 무료(Demo) 플랜은 "Personal Use only, not for any commercial purpose"**로 명시돼 있음. 상업적 이용은 Basic 이상 유료 플랜부터 허용됨.

moneyfinal은 AdSense·제휴 링크 등 어떤 형태의 광고/수익화도 없는 무료 정보 사이트라는 걸 코드베이스 전체 검색으로 확인했고, 지금 상태로는 CoinGecko 무료 플랜을 써도 문제없다고 판단했었음. 다만 마침 **CoinMarketCap 무료 Basic 플랜은 상업적 이용을 처음부터 명시적으로 허용**하고(월 15,000회/분당 50회, 하루 1회 배치 수집엔 충분) 이미 키도 발급받아 등록해뒀길래, 아예 이쪽을 1차로 두기로 함 — 이러면 "지금 사이트가 상업적인가 아닌가"를 매번 재판단할 필요 자체가 없어짐. CoinGecko는 최후 폴백(키 불필요라는 장점은 여전히 유효)으로만 남겨둠.

**참고**: 만약 CMC_API_KEY가 만료/삭제되어 CoinMarketCap이 계속 실패하는 상황이 오래 지속되면, 사실상 yfinance가 상시 1차처럼 동작하게 됨 — 이것도 상업적 이용 제약이 없는 소스라 문제없음. CoinGecko까지 내려가는 경우에만 위 라이선스 판단이 다시 유효해짐(현재는 무료 사이트라 문제없다는 결론).

## 검토했지만 채택 안 한 소스

- **CoinCap**: 예전 v2(키 불필요, 완전 무료)는 2025년에 폐지됨. v3부터는 API 키 필수 + USDC 기반 프리페이드 크레딧 시스템(x402 결제 프로토콜)으로 전환되어, 단순 일일 배치 수집 용도로는 과도하게 복잡함. 채택 안 함.

## 각 소스 필드 커버리지 차이

| 필드 | CoinMarketCap | yfinance | CoinGecko |
|---|---|---|---|
| 가격/시가총액/거래량/순위 | ✅ | ✅ | ✅ |
| 24시간 변동률 | ✅ | ✅ | ✅ |
| 7일 변동률 | ✅ | ❌ (비움) | ✅ |
| 코인 아이콘 이미지 | ❌ (비움, 별도 엔드포인트 필요) | ❌ (비움) | ✅ |
| 24h 고가/저가 | ❌ (해당 엔드포인트에 없음) | ❌ (신뢰도 낮아 비움) | ✅ |
| 사상 최고가(ATH) | ❌ | ❌ | ✅ |

`crypto_prices` 테이블 컬럼이 전부 nullable이고 `crypto.html`도 결측값을 `-`로 안전하게 표시하므로 어느 소스로 수집되든 페이지는 정상 동작한다(다만 코인 아이콘/ATH 등은 CoinGecko로 폴백됐을 때만 채워짐).
