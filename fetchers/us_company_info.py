"""
미국 기업정보 수집기 (Financial Modeling Prep + yfinance 보완)
출처: financialmodelingprep.com/stable/* (2026-09-02 실측 확인 — 구 /api/v3/ 는
      2025-08-31부로 레거시 전용이라 신규 키에서 막힘, 반드시 /stable/ 사용)
무료티어 제약(실측 확인, 2026-09-02): 재무제표/실적/배당/분할 4개 엔드포인트가
종목 단위로 화이트리스트돼있어 대형주(FINNHUB_TICKERS)만 되고, 중소형
리츠·BDC(REIT_BDC_TICKERS)는 전부 402. limit 파라미터도 5 이하만 허용.
프로필만 전 종목 공통으로 열려있음. FMP 호출량: 대형주 10종*5회 + 나머지
16종*1회(프로필만) = 66회/일로 하루 250회 한도에 여유 있음.

그래서 REIT_BDC_TICKERS의 재무제표/실적/분할은 yfinance로 대신 채운다
(일반 주식이라 .financials/.balance_sheet/.earnings_dates/.splits 전부 정상
동작함을 실측 확인 - 배당은 이미 etf_dividends.py가 수집 중이라 건드리지 않음).
뉴스 엔드포인트(/stable/news/stock)는 실측 결과 402(유료 전용)라 아예 제외.
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst
import requests
import yfinance as yf

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FMP_API_KEY', '')
BASE_URL = "https://financialmodelingprep.com/stable"

FINNHUB_TICKERS = ['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','AVGO','JPM','V']
REIT_BDC_TICKERS = ['O','MAIN','STAG','AGNC','ARR','GAIN','GOOD','LAND','PSEC','EPR','ORC','NLY','ADC','LTC','ABR','EFC']
TICKERS = FINNHUB_TICKERS + REIT_BDC_TICKERS


def _get(path: str, params: dict) -> list | None:
    params = {**params, 'apikey': API_KEY}
    try:
        res = requests.get(f"{BASE_URL}/{path}", params=params, timeout=15)
        if res.status_code >= 400:
            logger.warning(f"{path} {params.get('symbol')} HTTP {res.status_code}: {res.text[:150]}")
            return None
        data = res.json()
        return data if isinstance(data, list) else None
    except Exception as e:
        logger.error(f"{path} {params.get('symbol')} 예외: {type(e).__name__} - {e}")
        return None


def fetch_profile(symbol: str) -> dict | None:
    data = _get('profile', {'symbol': symbol})
    if not data:
        return None
    p = data[0]
    return {
        'ticker': symbol,
        'name': p.get('companyName'),
        'sector': p.get('sector'),
        'industry': p.get('industry'),
        'description': p.get('description'),
        'ceo': p.get('ceo'),
        'website': p.get('website'),
        'exchange': p.get('exchange'),
        'ipo_date': p.get('ipoDate') or None,
        'employees': int(p['fullTimeEmployees']) if p.get('fullTimeEmployees') else None,
        'market_cap': p.get('marketCap'),
        'image_url': p.get('image'),
        'fetched_at': now_kst()
    }


def fetch_financials(symbol: str) -> list:
    income = _get('income-statement', {'symbol': symbol, 'period': 'annual', 'limit': 5}) or []
    balance = _get('balance-sheet-statement', {'symbol': symbol, 'period': 'annual', 'limit': 5}) or []
    by_year = {b.get('fiscalYear'): b for b in balance}
    rows = []
    for i in income:
        fy = i.get('fiscalYear')
        b = by_year.get(fy, {})
        rows.append({
            'ticker': symbol,
            'fiscal_year': int(fy) if fy else None,
            'period': i.get('period') or 'FY',
            'revenue': i.get('revenue'),
            'gross_profit': i.get('grossProfit'),
            'operating_income': i.get('operatingIncome'),
            'net_income': i.get('netIncome'),
            'eps': i.get('eps'),
            'total_assets': b.get('totalAssets'),
            'total_liabilities': b.get('totalLiabilities'),
            'total_equity': b.get('totalEquity') or b.get('totalStockholdersEquity'),
            'fetched_at': now_kst()
        })
    return [r for r in rows if r['fiscal_year']]


def fetch_earnings(symbol: str) -> list:
    data = _get('earnings', {'symbol': symbol, 'limit': 5}) or []
    return [{
        'ticker': symbol,
        'report_date': e.get('date'),
        'eps_estimated': e.get('epsEstimated'),
        'eps_actual': e.get('epsActual'),
        'revenue_estimated': e.get('revenueEstimated'),
        'revenue_actual': e.get('revenueActual'),
        'fetched_at': now_kst()
    } for e in data if e.get('date')]


def fetch_dividends(symbol: str) -> list:
    data = _get('dividends', {'symbol': symbol, 'limit': 5}) or []
    return [{
        'ticker': symbol,
        'ex_date': d.get('date'),
        'payment_date': d.get('paymentDate') or None,
        'amount': d.get('dividend'),
        'fetched_at': now_kst()
    } for d in data if d.get('date')]


def fetch_splits(symbol: str) -> list:
    data = _get('splits', {'symbol': symbol}) or []
    return [{
        'ticker': symbol,
        'split_date': s.get('date'),
        'numerator': s.get('numerator'),
        'denominator': s.get('denominator'),
        'fetched_at': now_kst()
    } for s in data if s.get('date')]


def fetch_financials_yf(symbol: str) -> list:
    try:
        t = yf.Ticker(symbol)
        inc, bs = t.financials, t.balance_sheet
        if inc is None or inc.empty:
            return []
        rows = []
        for col in inc.columns:
            year = col.year
            b = bs[col] if bs is not None and col in bs.columns else None
            def g(df_col, key):
                return float(df_col[key]) if df_col is not None and key in df_col.index and df_col[key] == df_col[key] else None
            rows.append({
                'ticker': symbol,
                'fiscal_year': year,
                'period': 'FY',
                'revenue': g(inc[col], 'Total Revenue'),
                'gross_profit': g(inc[col], 'Gross Profit'),
                'operating_income': g(inc[col], 'Operating Income'),
                'net_income': g(inc[col], 'Net Income'),
                'eps': g(inc[col], 'Diluted EPS'),
                'total_assets': g(b, 'Total Assets'),
                'total_liabilities': g(b, 'Total Liabilities Net Minority Interest'),
                'total_equity': g(b, 'Stockholders Equity'),
                'fetched_at': now_kst()
            })
        return rows
    except Exception as e:
        logger.error(f"{symbol} yfinance 재무제표 예외: {type(e).__name__} - {e}")
        return []


def fetch_earnings_yf(symbol: str) -> list:
    try:
        ed = yf.Ticker(symbol).earnings_dates
        if ed is None or ed.empty:
            return []
        rows = []
        for idx, row in ed.head(5).iterrows():
            est, act = row.get('EPS Estimate'), row.get('Reported EPS')
            rows.append({
                'ticker': symbol,
                'report_date': idx.date().isoformat(),
                'eps_estimated': float(est) if est == est else None,
                'eps_actual': float(act) if act == act else None,
                'revenue_estimated': None,
                'revenue_actual': None,
                'fetched_at': now_kst()
            })
        return rows
    except Exception as e:
        logger.error(f"{symbol} yfinance 실적 예외: {type(e).__name__} - {e}")
        return []


def fetch_splits_yf(symbol: str) -> list:
    try:
        sp = yf.Ticker(symbol).splits
        if sp is None or sp.empty:
            return []
        return [{
            'ticker': symbol,
            'split_date': idx.date().isoformat(),
            'numerator': float(ratio),
            'denominator': 1,
            'fetched_at': now_kst()
        } for idx, ratio in sp.items()]
    except Exception as e:
        logger.error(f"{symbol} yfinance 분할 예외: {type(e).__name__} - {e}")
        return []


def main():
    logger.info("=== 미국 기업정보 수집 시작 (FMP) ===")
    profiles, financials, earnings, dividends, splits = [], [], [], [], []

    for symbol in TICKERS:
        p = fetch_profile(symbol)
        if p:
            profiles.append(p)
        time.sleep(0.3)

        # 재무제표/실적/배당/분할은 FMP 무료티어에서 대형주(FINNHUB_TICKERS)만
        # 제공되고, 중소형 리츠·BDC(REIT_BDC_TICKERS)는 종목 단위로 402가 떠서
        # 프로필만 수집한다 (실측 확인, 2026-09-02).
        if symbol in FINNHUB_TICKERS:
            financials.extend(fetch_financials(symbol))
            earnings.extend(fetch_earnings(symbol))
            dividends.extend(fetch_dividends(symbol))
            splits.extend(fetch_splits(symbol))
            time.sleep(0.3)
        else:
            financials.extend(fetch_financials_yf(symbol))
            earnings.extend(fetch_earnings_yf(symbol))
            splits.extend(fetch_splits_yf(symbol))

        logger.info(f"✅ {symbol} 수집 완료")

    if profiles:
        supabase_upsert('us_company_profile', profiles)
        logger.info(f"✅ 프로필 {len(profiles)}건 저장")
    if financials:
        supabase_upsert('us_company_financials', financials)
        logger.info(f"✅ 재무제표 {len(financials)}건 저장")
    if earnings:
        supabase_upsert('us_company_earnings', earnings)
        logger.info(f"✅ 실적발표 {len(earnings)}건 저장")
    if dividends:
        supabase_upsert('us_company_dividends', dividends)
        logger.info(f"✅ 배당 {len(dividends)}건 저장")
    if splits:
        supabase_upsert('us_company_splits', splits)
        logger.info(f"✅ 액면분할 {len(splits)}건 저장")
    logger.info("=== 미국 기업정보 수집 완료 ===")


if __name__ == '__main__': main()
