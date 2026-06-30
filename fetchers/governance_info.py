"""
금융회사 지배구조정보 수집기 (대표이사정보 + 임원보수현황)
출처: 공공데이터포털 금융위원회_금융회사지배구조정보 (GetFnCoGoveInfoService)
주의: 이 서비스는 운영명이 GetFnCoGoveInfoService이며 오퍼레이션명에 버전(_V2 등) 접미사가 없음 — 가이드 문서 그대로
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetFnCoGoveInfoService"

MAJOR_CRNOS = [
    {'crno':'1101110028131','name':'KB금융'},
    {'crno':'1101110608146','name':'카카오'},
]


def collect_ceo_info() -> list:
    """금융회사대표이사정보조회 (getFnCoReprDireInfo)"""
    url = f"{BASE_URL}/getFnCoReprDireInfo"
    results = []
    for stock in MAJOR_CRNOS:
        params = {'resultType':'json','numOfRows':5,'pageNo':1,'crno':stock['crno']}
        try:
            res = data_go_kr_get(url, API_KEY, params)
            res.raise_for_status()
            body = res.json().get('response',{}).get('body',{})
            if not body.get('totalCount',0): continue
            items = body.get('items',{}).get('item',[])
            if isinstance(items,dict): items=[items]
            for item in items:
                results.append({
                    'indicator_code': f"GOVE_CEO_{item.get('crno','')}"[:50],
                    'indicator_name': f"{item.get('fncoNm', stock['name'])} 대표이사",
                    'category': '지배구조',
                    'value': 0,
                    'unit': '',
                    'signal': 'green',
                    'source': '금융위원회 지배구조정보 (공공데이터포털)',
                    'reference_date': today_kst(),
                    'summary_text': f"{item.get('ceoFnm','')} ({item.get('ceoJbttNm','')}) 재직기간 {item.get('ceoHdfTermCtt','')}",
                    'fetched_at': now_kst()
                })
        except Exception as e:
            logger.error(f"{stock['name']} 대표이사정보 오류: {type(e).__name__}")
    return results


def collect_exec_remuneration() -> list:
    """금융회사임원보수현황조회 (getFnCoExecRemuStat)"""
    url = f"{BASE_URL}/getFnCoExecRemuStat"
    results = []
    for stock in MAJOR_CRNOS:
        params = {'resultType':'json','numOfRows':5,'pageNo':1,'crno':stock['crno']}
        try:
            res = data_go_kr_get(url, API_KEY, params)
            res.raise_for_status()
            body = res.json().get('response',{}).get('body',{})
            if not body.get('totalCount',0): continue
            items = body.get('items',{}).get('item',[])
            if isinstance(items,dict): items=[items]
            for item in items:
                avg = float(item.get('rgstDrtrAvgRmrAmt',0) or 0)
                if avg <= 0: continue
                results.append({
                    'indicator_code': f"GOVE_REMU_{item.get('crno','')}"[:50],
                    'indicator_name': f"{stock['name']} 등기이사 평균보수",
                    'category': '지배구조',
                    'value': avg,
                    'unit': '백만원',
                    'signal': 'green',
                    'source': '금융위원회 지배구조정보 (공공데이터포털)',
                    'reference_date': today_kst(),
                    'summary_text': f"사외이사평균 {item.get('otdrAvgRmrAmt','')}백만원, 감사인평균 {item.get('audpnAvgRmrAmt','')}백만원",
                    'fetched_at': now_kst()
                })
        except Exception as e:
            logger.error(f"{stock['name']} 임원보수 오류: {type(e).__name__}")
    return results


def main():
    logger.info("=== 금융회사 지배구조정보 수집 시작 ===")
    results = collect_ceo_info() + collect_exec_remuneration()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 지배구조정보 {len(results)}건 저장")
    logger.info("=== 금융회사 지배구조정보 수집 완료 ===")


if __name__ == '__main__': main()
