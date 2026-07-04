"""
한국 주식 기술지표 계산기 (RSI 14, Wilder 방식)
데이터 소스: Supabase stock_prices 히스토리 (외부 API 호출 없음)
대상: KOSPI/KOSDAQ 시가총액 상위 25종목씩 (stocks.json 표시 대상과 동일)
저장: market_indicators, indicator_code=KR_RSI_{종목코드} (US_RSI_* 패턴과 동일)
종가 15개(=15거래일) 미만 종목은 계산 불가로 스킵 - 백필/누적 후 자동 해소
"""
import logging, os, sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, supabase_select_all, supabase_upsert, now_kst

logger = logging.getLogger(__name__)
TOP_N = 25
RSI_PERIOD = 14


def wilder_rsi(closes: list, period: int = RSI_PERIOD):
    """Wilder 평활 RSI. closes는 오래된 날짜 → 최신 순. period+1개 미만이면 None"""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def process_market(market: str) -> list:
    # 1) 최신 거래일
    latest_rows = supabase_select('stock_prices', {
        'select': 'base_date',
        'market_type': f'eq.{market}',
        'order': 'base_date.desc',
        'limit': '1'
    })
    if not latest_rows:
        logger.warning(f"❌ {market}: stock_prices 데이터 없음")
        return []
    latest_date = latest_rows[0]['base_date']

    # 2) 최신일 기준 시총 상위 종목
    top = supabase_select('stock_prices', {
        'select': 'stock_code,stock_name',
        'market_type': f'eq.{market}',
        'base_date': f'eq.{latest_date}',
        'order': 'market_cap.desc',
        'limit': str(TOP_N)
    })
    if not top:
        logger.warning(f"❌ {market}: {latest_date} 시총 상위 조회 실패")
        return []
    codes = [t['stock_code'] for t in top if t.get('stock_code')]
    names = {t['stock_code']: t.get('stock_name', '') for t in top}

    # 3) 최근 60일(달력일) 종가 히스토리 일괄 조회 (~25종목 × 최대 40거래일)
    cutoff = (datetime.strptime(latest_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
    history = supabase_select_all('stock_prices', {
        'select': 'stock_code,base_date,close_price',
        'market_type': f'eq.{market}',
        'stock_code': f'in.({",".join(codes)})',
        'base_date': f'gte.{cutoff}',
        'order': 'stock_code.asc,base_date.asc'
    })

    by_code = {}
    for h in history:
        by_code.setdefault(h['stock_code'], []).append(h)

    results, skipped = [], 0
    for code in codes:
        rows = by_code.get(code, [])
        closes = [float(r['close_price']) for r in rows if r.get('close_price')]
        rsi = wilder_rsi(closes)
        if rsi is None:
            skipped += 1
            continue
        results.append({
            'indicator_code': f"KR_RSI_{code}",
            'indicator_name': f"{names.get(code, code)} RSI(14)",
            'category': '한국주식기술지표',
            'value': round(rsi, 2),
            'unit': '',
            'signal': 'red' if rsi >= 70 else 'yellow' if rsi <= 30 else 'green',
            'source': '자체계산(금융위 주식시세정보)',
            'reference_date': latest_date,
            'summary_text': f"{'과매수' if rsi >= 70 else '과매도' if rsi <= 30 else '중립'} 구간",
            'fetched_at': now_kst()
        })
    logger.info(f"✅ {market}: RSI {len(results)}건 계산, 히스토리 부족 스킵 {skipped}건 (기준일 {latest_date})")
    return results


def main():
    logger.info("=== 한국 주식 RSI 계산 시작 ===")
    all_results = []
    for market in ['KOSPI', 'KOSDAQ']:
        all_results.extend(process_market(market))
    if all_results:
        supabase_upsert('market_indicators', all_results)
        logger.info(f"✅ RSI {len(all_results)}건 저장")
    else:
        logger.warning("저장할 RSI 없음 - stock_prices 히스토리(15거래일+) 백필 필요 여부 확인")
    logger.info("=== 한국 주식 RSI 계산 완료 ===")


if __name__ == '__main__': main()
