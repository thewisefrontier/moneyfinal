"""
KRX 금시장 금시세 수집기
1차 출처: 공공데이터포털 금융위원회_일반상품시세정보 (getGoldPriceInfo)
2차(폴백) 출처: Yahoo Finance GC=F(COMEX 금선물, USD/oz) × 원달러 환율(이미 수집된
market_indicators의 USD_KRW 최신값, 한국은행 ECOS 소스 - data.go.kr과 무관) 환산.
[[moneyfinal_krx_backup_pipeline_research]] 조사 결과에 따른 백업.
국제 금값과 국내 KRX 금시장 시세는 완전히 같지 않음(소폭 프리미엄/디스카운트 존재) -
1차 API가 정상일 땐 항상 1차를 우선한다.
- KRX 금시장 "금 99.99_1kg" 종목 기준 (원/g 단위)
  ※ 실제 API 응답은 소문자 kg (docx 가이드의 "1Kg" 표기와 다름, 실측 확인됨)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 최신 basDt 값만 채택 (krx_index.py와 동일 패턴, 실측 확인된 이슈)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_select, now_kst, today_kst, data_go_kr_get
import yfinance as yf

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getGoldPriceInfo"
ITMS_NM = "금 99.99_1kg"
GRAMS_PER_TROY_OZ = 31.1034768


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_gold_primary(begin_date: str) -> dict | None:
    params = {'resultType': 'json', 'numOfRows': 10, 'pageNo': 1, 'beginBasDt': begin_date, 'itmsNm': ITMS_NM}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            return None
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict): items = [items]
        item = max(items, key=lambda x: x.get('basDt', ''))
        value = float(item.get('clpr', 0) or 0)
        vs = float(item.get('vs', 0) or 0)
        flt_rt = float(item.get('fltRt', 0) or 0)
        return {
            'indicator_code': 'GOLD',
            'indicator_name': '금 가격 (KRX 99.99_1kg)',
            'category': '원자재',
            'value': value,
            'prev_value': round(value - vs, 2),
            'unit': '원/g',
            'signal': 'green',
            'source': '금융위원회 (공공데이터포털, KRX 금시장)',
            'reference_date': today_kst(),
            'summary_text': f"금 {value:,.0f}원/g ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.warning(f"금시세 1차(data.go.kr) 실패: {type(e).__name__}")
        return None


def get_latest_usd_krw() -> float | None:
    rows = supabase_select('market_indicators', {
        'select': 'value', 'indicator_code': 'eq.USD_KRW',
        'order': 'reference_date.desc', 'limit': '1'
    })
    if rows:
        return float(rows[0]['value'])
    return None


def fetch_gold_fallback() -> dict | None:
    try:
        usd_krw = get_latest_usd_krw()
        if not usd_krw:
            logger.error("금시세 2차(Yahoo) 실패: USD_KRW 환율 데이터 없음(ecos_daily.py 먼저 필요)")
            return None
        hist = yf.Ticker('GC=F').history(period='5d')
        if hist.empty:
            return None
        closes = hist['Close']
        usd_per_oz = float(closes.iloc[-1])
        prev_usd_per_oz = float(closes.iloc[-2]) if len(closes) >= 2 else usd_per_oz
        value = round(usd_per_oz * usd_krw / GRAMS_PER_TROY_OZ, 2)
        prev_value = round(prev_usd_per_oz * usd_krw / GRAMS_PER_TROY_OZ, 2)
        flt_rt = (value - prev_value) / prev_value * 100 if prev_value else 0
        return {
            'indicator_code': 'GOLD',
            'indicator_name': '금 가격 (국제 금선물 환산)',
            'category': '원자재',
            'value': value,
            'prev_value': prev_value,
            'unit': '원/g',
            'signal': 'green',
            'source': 'Yahoo Finance GC=F 환산 (data.go.kr 장애 시 폴백)',
            'reference_date': today_kst(),
            'summary_text': f"금 {value:,.0f}원/g ({flt_rt:+.2f}%, 국제시세 환산)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"금시세 2차(Yahoo) 실패: {type(e).__name__}")
        return None


def main():
    logger.info("=== KRX 금시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    result = fetch_gold_primary(begin_date)
    if not result:
        logger.warning("금시세: 1차 실패 -> Yahoo Finance 폴백 시도")
        result = fetch_gold_fallback()
    if result:
        logger.info(f"✅ 금 {result['value']}원/g ({result['source']})")
        supabase_upsert('market_indicators', [result])
    else:
        logger.error("❌ 금시세 수집 실패 (1차/2차 모두 실패)")
    logger.info("=== KRX 금시세 수집 완료 ===")


if __name__ == '__main__':
    main()
