"""
실손보험정보 수집기
출처: 공공데이터포털 금융위원회_실손보험정보 (GetMedicalReimbursementInsuranceInfoService/getInsuranceInfo)
정확한 서비스명: 이전 코드는 GetRealLossInsuranceInfoService로 잘못 추측됨
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMedicalReimbursementInsuranceInfoService/getInsuranceInfo"

def main():
    logger.info("=== 실손보험 정보 수집 시작 ===")
    if has_recent_data('rates', {'category': 'eq.실손보험'}, 'fetched_at', 6):
        logger.info("이미 이번 달 수집 완료 - 스킵 (재시도 크론 중복 방지)")
        return
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("실손보험: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            ml = float(item.get('mlInsRt',0) or 0)
            fml = float(item.get('fmlInsRt',0) or 0)
            avg = (ml+fml)/2 if (ml>0 or fml>0) else 0
            if avg <= 0: continue
            results.append({
                'institution': item.get('cmpyNm',''),
                'product_name': item.get('prdNm',''),
                'category': '실손보험',
                'rate': avg,
                'max_rate': max(ml,fml),
                'period': f"{item.get('age','')}세",
                'join_method': item.get('ptrn',''),
                'source': '손해보험협회/생명보험협회 (공공데이터포털)',
                'source_url': 'https://data.go.kr',
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('rates', results)
            logger.info(f"✅ 실손보험 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"실손보험 수집 오류: {type(e).__name__}")
    logger.info("=== 실손보험 정보 수집 완료 ===")

if __name__ == '__main__': main()
