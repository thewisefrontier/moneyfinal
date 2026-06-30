"""
은행 경영통계 수집기
출처: 금융통계정보시스템 FISIS (fisis.fss.or.kr) - 별도 도맨/키 가맥성 필요
주의: authKey가 아니른 auth 파랄트를 쓰고, financeCd/listNo 동적 파래뫁터 필요
실제 실행 전 응답 스트렉처 확인 필요 - 1단계: 연결 확인만 수행
"""
import logging, os, sys, requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import now_kst

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://fisis.fss.or.kr/openapi/companySearch.json"

def main():
    logger.info("=== 은행경영통계 연결 확인 시작 ===")
    # FISIS는 financeCd/listNo 조합이 필요해 별도 설계 단개 필요.
    # 우선 기본 연결(공식 은행 리스트)만 확인하여 실제 조회 가능 여벀 파악.
    try:
        params = {'auth': AUTH_KEY, 'lang': 'kr', 'financeGb': '1'}
        res = requests.get(BASE_URL, params=params, timeout=15)
        if res.status_code >= 400:
            logger.error(f"FISIS 연결 오류: HTTP {res.status_code} | 응답: {res.text[:300]}")
            return
        logger.info(f"FISIS 응답 확인: {res.text[:300]}")
        logger.warning("은행경영통계는 financeCd/listNo 설계가 필요합니다. 연결 확인만 완료, 실제 수집은 추가 설정 대기.")
    except Exception as e:
        logger.error(f"FISIS 연결 오류: {type(e).__name__} - {e}")
    logger.info("=== 은행경영통계 연결 확인 완료 ===")

if __name__ == '__main__': main()
