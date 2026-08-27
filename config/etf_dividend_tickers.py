"""
배당금 계산기 페이지 대상 ETF/종목 목록.
fetchers/etf_dividends.py (데이터 수집)와 scripts/generate_dividend_pages.py (정적 페이지 생성)가
이 목록을 공용으로 사용한다. 새 티커 추가 시 여기 한 곳만 수정하면 됨.

형식: (ticker, 표시이름, 카테고리)
"""

TICKERS = [
    # 커버드콜/옵션 인컴 ETF (월배당)
    ("JEPI", "JPMorgan Equity Premium Income ETF", "커버드콜"),
    ("JEPQ", "JPMorgan Nasdaq Equity Premium Income ETF", "커버드콜"),
    ("QYLD", "Global X Nasdaq 100 Covered Call ETF", "커버드콜"),
    ("RYLD", "Global X Russell 2000 Covered Call ETF", "커버드콜"),
    ("XYLD", "Global X S&P 500 Covered Call ETF", "커버드콜"),
    ("DIVO", "Amplify CWP Enhanced Dividend Income ETF", "커버드콜"),
    ("SPYI", "NEOS S&P 500 High Income ETF", "커버드콜"),
    ("QQQI", "NEOS Nasdaq 100 High Income ETF", "커버드콜"),
    ("SVOL", "Simplify Volatility Premium ETF", "커버드콜"),
    ("NUSI", "Nationwide Risk-Managed Income ETF", "커버드콜"),
    ("FEPI", "REX FANG & Innovation Equity Premium Income ETF", "커버드콜"),
    ("GPIX", "Goldman Sachs S&P 500 Core Premium Income ETF", "커버드콜"),
    ("GPIQ", "Goldman Sachs Nasdaq-100 Core Premium Income ETF", "커버드콜"),
    ("QDTE", "Roundhill Innovation-100 0DTE Covered Call ETF", "커버드콜"),
    ("XDTE", "Roundhill S&P 500 0DTE Covered Call ETF", "커버드콜"),
    ("YMAG", "YieldMax Magnificent 7 Fund of Option Income ETFs", "커버드콜"),
    ("YMAX", "YieldMax Universe Fund of Option Income ETFs", "커버드콜"),
    ("LFGY", "YieldMax Crypto Industry & Tech Portfolio Option Income ETF", "커버드콜"),
    ("GDXY", "YieldMax Gold Miners Option Income Strategy ETF", "커버드콜"),

    # YieldMax 개별종목 옵션 인컴 ETF (월배당)
    ("TSLY", "YieldMax TSLA Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("NVDY", "YieldMax NVDA Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("CONY", "YieldMax COIN Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("MSTY", "YieldMax MSTR Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("AMZY", "YieldMax AMZN Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("FBY", "YieldMax META Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("GOOY", "YieldMax GOOGL Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("APLY", "YieldMax AAPL Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("NFLY", "YieldMax NFLX Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("XOMO", "YieldMax XOM Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("JPMO", "YieldMax JPM Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("DISO", "YieldMax DIS Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("PYPY", "YieldMax PYPL Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("SQY", "YieldMax SQ Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("ULTY", "YieldMax Ultra Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("OARK", "YieldMax Innovation Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("AIYY", "YieldMax AI Option Income ETF", "개별종목 옵션인컴"),
    ("SMCY", "YieldMax SMCI Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("PLTY", "YieldMax PLTR Option Income Strategy ETF", "개별종목 옵션인컴"),
    ("ABNY", "YieldMax ABNB Option Income Strategy ETF", "개별종목 옵션인컴"),

    # 월배당 리츠/BDC/개별주
    ("O", "Realty Income Corp", "월배당 리츠"),
    ("MAIN", "Main Street Capital Corp", "월배당 BDC"),
    ("STAG", "Stag Industrial", "월배당 리츠"),
    ("AGNC", "AGNC Investment Corp", "월배당 모기지리츠"),
    ("ARR", "ARMOUR Residential REIT", "월배당 모기지리츠"),
    ("GAIN", "Gladstone Investment Corp", "월배당 BDC"),
    ("GOOD", "Gladstone Commercial Corp", "월배당 리츠"),
    ("LAND", "Gladstone Land Corp", "월배당 리츠"),
    ("PSEC", "Prospect Capital Corp", "월배당 BDC"),
    ("EPR", "EPR Properties", "월배당 리츠"),
    ("ORC", "Orchid Island Capital", "월배당 모기지리츠"),
    ("NLY", "Annaly Capital Management", "월배당 모기지리츠"),

    # 채권/우선주 인컴 (월배당)
    ("TLTW", "iShares 20+ Year Treasury Bond BuyWrite Strategy ETF", "채권인컴"),
    ("HYG", "iShares iBoxx High Yield Corp Bond ETF", "채권인컴"),
    ("JNK", "SPDR Bloomberg High Yield Bond ETF", "채권인컴"),
    ("PFF", "iShares Preferred and Income Securities ETF", "채권인컴"),
    ("SPHY", "SPDR Portfolio High Yield Bond ETF", "채권인컴"),
    ("USHY", "iShares Broad USD High Yield Corp Bond ETF", "채권인컴"),
    ("BKLN", "Invesco Senior Loan ETF", "채권인컴"),

    # 분기배당 대표 ETF (검색 수요 반영)
    ("SCHD", "Schwab US Dividend Equity ETF", "분기배당 대표"),
    ("VYM", "Vanguard High Dividend Yield ETF", "분기배당 대표"),
    ("DGRO", "iShares Core Dividend Growth ETF", "분기배당 대표"),
    ("VIG", "Vanguard Dividend Appreciation ETF", "분기배당 대표"),
    ("HDV", "iShares Core High Dividend ETF", "분기배당 대표"),
    ("SPHD", "Invesco S&P 500 High Dividend Low Volatility ETF", "분기배당 대표"),
    ("SDIV", "Global X SuperDividend ETF", "분기배당 대표"),
    ("DGRW", "WisdomTree US Quality Dividend Growth Fund", "분기배당 대표"),
    ("NOBL", "ProShares S&P 500 Dividend Aristocrats ETF", "분기배당 대표"),
]

# fetcher용 티커 심볼만 추출
SYMBOLS = [t[0] for t in TICKERS]
