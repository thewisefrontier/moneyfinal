"""
FDI 외국인직접투자 수집기
출처: 대한무역투자진흥공사(KOTRA) 한국 산업별 외국인직접투자통계 (DS00000127)
정확한 URL/필드: 활용가이드_대한무역투자진흥공사_한국_산업별_외국인직접투자통계.docx 기준
이전 코드의 B553718/FdiService/getFdiList는 존재하지 않는 가짜 URL이었음 → 교체
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/B410001/DS00000127/getDS00000127"

def main():
    logger.info("=== FDI 외국인직접투자 수집 시작 ===")
    if has_recent_data('market_indicators', {'category': 'eq.외국인직접투자'}, 'reference_date', 6):
        logger.info("이미 이번 분기 수집 완료 - 스킵 (재시도 크론 중복 방지)")
        return
    params = {'pageNo':1,'numOfRows':30}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        if data.get('resultCode') != 0:
            logger.warning(f"FDI: 응답 오류 - {data.get('resultMsg')}")
            return
        records = data.get('records', [])
        if not records:
            logger.warning("FDI: 데이터 없음")
            return
        results = []
        for item in records:
            if item.get('LEVEL_CD') == '0':  # '전체' 합계행 제외 (중복집계 방지)
                continue
            amt = float(item.get('INVT_AMT', 0) or 0)
            if amt <= 0: continue
            results.append({
                'indicator_code': f"FDI_{item.get('KSIC_NAME','')[:20]}",
                'indicator_name': f"FDI {item.get('KSIC_NAME','')}",
                'category': '외국인직접투자',
                'value': amt,
                'unit': '달러',
                'signal': 'green',
                'source': 'KOTRA (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('BASE_YR','')}년 신고수 {item.get('STTMN_CNT','')}건, 업체수 {item.get('COMP_CNT','')}개",
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('market_indicators', results)
            logger.info(f"✅ FDI {len(results)}건 저장")
    except Exception as e:
        logger.error(f"FDI 수집 오류: {type(e).__name__}")
    logger.info("=== FDI 외국인직접투자 수집 완료 ===")

if __name__ == '__main__': main()
