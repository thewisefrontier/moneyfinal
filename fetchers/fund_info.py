"""
펀드 상품 기본정보 수집기
- 금융위원회_펀드상품기본정보 (공공데이터포털)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetFundProductInfoService/getFundProductInfo"


def fetch_fund_products() -> list:
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("펀드: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            results.append({
                'institution':  item.get('asetMgCmpNm',''),
                'product_name': item.get('prdtNm',''),
                'category':     '펀드',
                'rate':         float(item.get('erngRt1',0) or 0),
                'max_rate':     float(item.get('erngRt3',0) or 0),
                'period':       '3개월',
                'join_method':  item.get('prdtClsNm',''),
                'source':       '금융위원회 (공공데이터포털)',
                'source_url':   'https://data.go.kr',
                'fetched_at':   now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"펀드 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 펀드 정보 수집 시작 ===")
    results = fetch_fund_products()
    if results:
        supabase_upsert('rates', results)
        logger.info(f"✅ 펀드 {len(results)}건 저장")
    logger.info("=== 펀드 정보 수집 완료 ===")

if __name__ == '__main__': main()
