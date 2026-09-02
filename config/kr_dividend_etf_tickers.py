"""
국내 상장 배당 ETF 목록 (배당ETF 계산기 국내판 대상).
fetchers/kr_etf_dividends.py와 scripts/generate_kr_dividend_pages.py가 이 목록을 공용으로 사용.

종목코드는 2026-09-02 Naver Finance 실시간 API(finance.naver.com/api/sise/etfItemList.nhn)로
직접 조회해 검증함(추측/구버전 자료 사용 안 함). 시가총액(marketSum) 상위 위주로 선정.

형식: (ticker, 표시이름, 카테고리, is_domestic_equity)
- is_domestic_equity=True: 국내주식형 ETF - 기초지수가 국내 상장주식으로만 구성.
  매매차익 비과세, 분배금만 배당소득세 15.4%.
- is_domestic_equity=False: 기타 ETF(해외지수/리츠/채권 등 추종) - 매매차익도
  배당소득세 과세 대상(Min(실제매매차익, 보유기간 과표기준가 상승분) × 15.4%).
  분배금은 국내주식형과 동일하게 15.4%.
  분류 근거: 삼성자산운용 공식 ETF세금 가이드 + TIGER 리츠부동산인프라는
  실측 검색으로 "기타자산" 분류 확인, TIGER 은행고배당플러스TOP10은 상품설명서상
  기초지수(FnGuide 은행고배당플러스TOP10)가 국내 상장 은행주로만 구성됨을 확인.
"""

TICKERS = [
    # 해외지수/리츠 추종 (기타 ETF - 매매차익도 배당소득세 과세)
    ("458730", "TIGER 미국배당다우존스", "미국배당", False),
    ("446720", "SOL 미국배당다우존스", "미국배당", False),
    ("402970", "ACE 미국배당다우존스", "미국배당", False),
    ("489250", "KODEX 미국배당다우존스", "미국배당", False),
    ("441640", "KODEX 미국배당커버드콜액티브", "미국배당 커버드콜", False),
    ("329200", "TIGER 리츠부동산인프라", "국내 리츠", False),
    ("465580", "ACE 미국빅테크TOP7 Plus", "미국 빅테크", False),
    ("429000", "TIGER 미국S&P500배당귀족", "미국배당", False),

    # 국내주식형 (매매차익 비과세)
    ("466940", "TIGER 은행고배당플러스TOP10", "국내 은행 고배당", True),
    ("161510", "PLUS 고배당주", "국내 고배당", True),
    ("279530", "KODEX 고배당주", "국내 고배당", True),
    ("325020", "KODEX 배당가치", "국내 배당가치", True),
    ("210780", "TIGER 코스피고배당", "국내 고배당", True),
    ("266160", "RISE 고배당", "국내 고배당", True),
    ("484880", "SOL 금융지주플러스고배당", "국내 금융지주 고배당", True),
]

SYMBOLS = [t[0] for t in TICKERS]
