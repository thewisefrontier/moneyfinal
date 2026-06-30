"""
펀드 상품 기본정보 수집기
출처: 공공데이터포털 금융위원회_펀드상품기본정보 (GetFundProductInfoService/getStandardCodeInfo)
주의: 이 API는 펀드명/코드/설정일 등 기본정보만 제공하며 수익률 필드는 없음.
이전 코드의 erngRt1/erngRt3(수익률)는 존재하지 않는 추측 필드였음 → 제거
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetFundProductInfoService/getStandardCodeInfo"

def main():
    logger.info("=== 펀드 기본정보 수집 시작 ===")
    params = {'resultType':'json','numOfRows':100,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("펀드: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        # 수익률 필드가 없으므로 market_indicators에 기본정보만 저장 (rates 테이블에는 부적합)
        results = []
        for item in items:
            results.append({
                'indicator_code': f"FUND_{item.get('srtnCd','')}",
                'indicator_name': item.get('fndNm','')[:100],
                'category': '펀드',
                'value': 0,
                'unit': '',
                'signal': 'green',
                'source': '금융위원회 펀드상품기본정보 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('ctg','')} / {item.get('fndTp','')} 설정일 {item.get('setpDt','')}",
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('market_indicators', results)
            logger.info(f"✅ 펀드 기본정보 {len(results)}건 저장 (수익률 데이터 없음, 기본정보만 제공)")
    except Exception as e:
        logger.error(f"펀드 수집 오류: {type(e).__name__}")
    logger.info("=== 펀드 기본정보 수집 완료 ===")

if __name__ == '__main__': main()
