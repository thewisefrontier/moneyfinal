"""
ETF 프로필 정보 수집기 (Yahoo Finance, yfinance)
출처: finance.yahoo.com (비공식 엔드포인트, yfinance 라이브러리 경유)

Alpha Vantage ETF_PROFILE 대체. 실측 확인(SCHD 기준)한 필드 매핑:
- net_assets: info['netAssets'] (raw USD, 프론트가 /1e8로 "억 달러" 환산)
- expense_ratio: funds_data.fund_operations의 'Annual Report Expense Ratio' 행
  (info['netExpenseRatio']는 단위가 달라 0.06=6%로 잘못 해석됨 - 실측으로 확인)
- dividend_yield: info['yield'] (decimal, 프론트가 *100으로 % 환산)
- inception_date: info['fundInceptionDate'] (unix timestamp) -> YYYY-MM-DD
- sectors/top_holdings: funds_data.sector_weightings / top_holdings

config/etf_dividend_tickers.py의 SYMBOLS에는 O/MAIN/STAG 등 ETF가 아닌
개별 리츠/BDC 종목도 섞여 있음 - 이들은 quoteType != 'ETF'라
funds_data가 YFDataException을 던지므로 프로필 수집을 건너뛴다
(기존 Alpha Vantage ETF_PROFILE도 개별종목엔 데이터를 준 적이 없어 동일 동작).

운용사 프로필은 분기 단위로만 바뀌는 정보지만, yfinance는 일일 호출 한도가
없어 굳이 로테이션할 필요가 없으므로 매일 전체를 갱신한다.
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone
from utils.common import supabase_upsert, now_kst
from config.etf_dividend_tickers import SYMBOLS
import yfinance as yf

logger = logging.getLogger(__name__)
TOP_HOLDINGS = 10
REQUEST_SLEEP = 0.5


def fetch_profile(symbol: str) -> dict | None:
    try:
        t = yf.Ticker(symbol)
        info = t.info
        if info.get('quoteType') != 'ETF':
            return None

        net_assets = info.get('netAssets') or info.get('totalAssets') or 0

        expense_ratio = 0.0
        sectors, holdings = [], []
        try:
            fd = t.funds_data
            fo = fd.fund_operations
            if fo is not None and not fo.empty and 'Annual Report Expense Ratio' in fo.index:
                expense_ratio = float(fo.iloc[:, 0].get('Annual Report Expense Ratio', 0) or 0)
            sw = fd.sector_weightings or {}
            sectors = sorted(
                [{'sector': k, 'weight': float(v)} for k, v in sw.items()],
                key=lambda s: s['weight'], reverse=True
            )
            th = fd.top_holdings
            if th is not None and not th.empty:
                holdings = [
                    {'symbol': sym, 'weight': float(row['Holding Percent'])}
                    for sym, row in th.head(TOP_HOLDINGS).iterrows()
                ]
        except Exception as e:
            logger.warning(f"{symbol}: funds_data 일부 조회 실패 - {type(e).__name__}")

        inception_ts = info.get('fundInceptionDate')
        inception_date = (
            datetime.fromtimestamp(inception_ts, tz=timezone.utc).strftime('%Y-%m-%d')
            if inception_ts else None
        )

        return {
            'ticker': symbol,
            'net_assets': float(net_assets),
            'expense_ratio': expense_ratio,
            'dividend_yield': float(info.get('yield', 0) or 0),
            'inception_date': inception_date,
            'sectors': sectors,
            'top_holdings': holdings,
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"{symbol} 프로필 예외: {type(e).__name__}")
        return None


def main():
    logger.info("=== ETF 프로필 수집 시작 (Yahoo Finance) ===")
    logger.info(f"오늘 처리 대상 {len(SYMBOLS)}개 (전체)")

    results = []
    for symbol in SYMBOLS:
        p = fetch_profile(symbol)
        if not p:
            logger.info(f"⏭️ {symbol}: ETF 아님 또는 데이터 없음 (건너뜀)")
            time.sleep(REQUEST_SLEEP)
            continue
        results.append(p)
        logger.info(f"✅ {symbol} 프로필 수집 (운용규모 {p['net_assets']:,.0f})")
        time.sleep(REQUEST_SLEEP)

    if results:
        supabase_upsert('etf_profiles', results)
        logger.info(f"✅ ETF 프로필 {len(results)}건 저장")
    logger.info("=== ETF 프로필 수집 완료 ===")


if __name__ == '__main__':
    main()
