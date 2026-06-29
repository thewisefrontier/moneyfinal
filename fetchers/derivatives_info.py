"""
파생상품 지수 시세 수집기
- 금융위원회_지수시세정보 파생상품 (공공데이터포털)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getDerivationProductMarketIndex"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_derivatives(base_date: str) -> list:
    params = {
        'resultType': 'json',
        'numOfRows': 20,
        'pageNo': 1,
        'basDt': base_date,
    }
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"파생상품 {base_date}: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            clpr = float(item.get('clpr', 0) or 0)
            flt_rt = float(item.get('fltRt', 0) or 0)
            idx_nm = item.get('idxNm', '')
            results.append({
                'indicator_code': f"DERIV_{idx_nm[:15]}",
                'indicator_name': idx_nm,
                'category': '파생상품',
                'value': clpr,
                'unit': 'pt',
                'signal': 'red' if flt_rt <= -3 else 'yellow' if flt_rt <= -1 else 'green',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{idx_nm} {clpr:.2f}pt ({flt_rt:+.2f}%)",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"파생상품 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 파생상품 시세 수집 시작 ===")
    base_date = get_base_date()
    results = fetch_derivatives(base_date)
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 파생상품 {len(results)}건 저장")
    logger.info("=== 파생상품 시세 수집 완료 ===")


if __name__ == '__main__':
    main()
