"""
공통 유틸리티 - Supabase REST API 헬퍼
"""
import atexit
import os
import logging
import requests
import sys
import time
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

KST = pytz.timezone('Asia/Seoul')

SUPABASE_URL = os.environ['SUPABASE_URL'].rstrip('/')
SUPABASE_KEY = os.environ['SUPABASE_KEY']

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
}

# 테이블별 upsert conflict 컬럼
CONFLICT_COLUMNS = {
    'rates': 'institution,product_name,category,period',
    'market_indicators': 'indicator_code,reference_date',
    'corporate_alerts': 'company_name,alert_type,disclosure_date',
    'ipo_status': 'company_name,status,request_date',
    'financial_health': 'institution,reference_date',
    'daily_briefing': 'briefing_date',
    'stock_prices': 'stock_code,base_date,market_type',
    'stock_short': 'stock_code,base_date',
    'stock_dividends': 'stock_code,base_date,dividend_type',
    'stock_issuance': 'stock_code,issuance_date,issuance_type',
    'stocks': 'stock_code',
    'corp_info': 'stock_code',
    'corp_finance': 'stock_code,fiscal_year',
    'fss_news': 'category,title,post_date',
    'fss_jobs': 'company_name,title,post_date',
    'mortgage_loans': 'fin_co_no,fin_prdt_cd,mrtg_type,rpay_type,lend_rate_type',
    'rent_loans': 'fin_co_no,fin_prdt_cd,rpay_type,lend_rate_type',
    'credit_loans': 'fin_co_no,fin_prdt_cd,crdt_prdt_type,crdt_lend_rate_type',
    'business_loans': 'fin_co_no,fin_prdt_cd',
    'annuity_savings': 'fin_co_no,fin_prdt_cd',
    'etf_dividends': 'ticker,ex_dividend_date',
    'etf_profiles': 'ticker',
}


# upsert 실패 시 워크플로우가 성공(exit 0)으로 표시되지 않도록 프로세스 종료 코드 관리.
# 여러 upsert 중 일부만 실패해도 모두 처리한 뒤 non-zero exit.
_UPSERT_FAILURES = 0


def _mark_upsert_failure(table: str, reason: str) -> None:
    global _UPSERT_FAILURES
    _UPSERT_FAILURES += 1
    logging.error(f"[{table}] upsert 실패 누적 {_UPSERT_FAILURES}건 (사유: {reason})")


def _exit_if_upsert_failures() -> None:
    if _UPSERT_FAILURES > 0:
        logging.error(f"⚠️ upsert 실패 총 {_UPSERT_FAILURES}건 → 프로세스 종료 코드 1")
        # atexit hook 내부에서는 sys.exit이 무시되므로 os._exit 사용
        os._exit(1)


atexit.register(_exit_if_upsert_failures)


def _dedupe_by_conflict(table: str, data: list, conflict: str) -> list:
    """배치 내 conflict key 조합 중복 제거.

    PostgreSQL은 ON CONFLICT DO UPDATE 시 같은 배치 안에 conflict 키 조합이
    중복되면 오류(21000)를 반환한다. 여기서 미리 제거하여 fetcher 개별 대응 부담을 없앰.
    같은 키 조합이면 마지막 행이 최종 반영 (개별 fetcher의 기존 dedupe 관례와 일치).
    """
    if not conflict or len(data) <= 1:
        return data
    keys = [k.strip() for k in conflict.split(',')]
    seen = {}
    for row in data:
        seen[tuple(row.get(k) for k in keys)] = row
    removed = len(data) - len(seen)
    if removed > 0:
        logging.warning(f"[{table}] 배치 내 conflict key 중복 {removed}건 자동 제거 (원본 {len(data)} → {len(seen)})")
    return list(seen.values())


def data_go_kr_get(url: str, service_key: str, params: dict, timeout: int = 15,
                    max_retries: int = 3) -> requests.Response:
    """
    공공데이터포털 API 전용 GET 요청.
    serviceKey를 params에 포함해 requests가 한 번만 인코딩하도록 한다.

    GitHub Actions 러너 -> apis.data.go.kr 구간에서 ConnectTimeout이 간헐적으로
    발생함(로컬에서는 같은 요청이 1초 내 응답 - 페이로드 크기가 아니라 네트워크
    경로 문제, stock_prices.py에서 실측 확인됨). 긴 타임아웃 1회보다 짧은
    타임아웃으로 여러 번 재시도하는 편이 안정적이라 모든 data.go.kr 호출에
    공통 적용한다 (개별 fetcher마다 따로 구현하지 않도록 여기서 일괄 처리).
    """
    all_params = {'serviceKey': service_key, **params}
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, params=all_params, timeout=timeout)
            if res.status_code >= 400:
                logging.error(
                    f"[API 오류] HTTP {res.status_code} "
                    f"| URL: {url} "
                    f"| params: {list(params.items())} "
                    f"| 응답: {res.text[:300]}"
                )
            return res
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_err = e
            logging.warning(f"[data.go.kr] {url} 시도 {attempt}/{max_retries} 실패: {type(e).__name__}")
            if attempt < max_retries:
                time.sleep(3)
    logging.error(f"[data.go.kr] {url} {max_retries}회 재시도 모두 실패: {type(last_err).__name__}")
    raise last_err


def fss_open_api_get(jsp_name: str, auth_key: str, days_back: int = 7, timeout: int = 15) -> requests.Response:
    """
    금융감독원 오픈API 전용 GET 요청 (www.fss.or.kr/fss/kr/openApi/api/*.jsp)
    파라미터: authKey, apiType=json, startDate/endDate (YYYY-MM-DD, 최대 1개월)
    일 30회 호출 제한 있으므로 호출량 주의.
    """
    now = datetime.now(KST)
    end_date = now.strftime('%Y-%m-%d')
    start_date = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = f"https://www.fss.or.kr/fss/kr/openApi/api/{jsp_name}.jsp"
    params = {
        'apiType': 'json',
        'startDate': start_date,
        'endDate': end_date,
        'authKey': auth_key,
    }
    res = requests.get(url, params=params, timeout=timeout)
    if res.status_code >= 400:
        logging.error(f"[FSS오픈API 오류] HTTP {res.status_code} | {jsp_name} | 응답: {res.text[:300]}")
    elif not res.text.strip()[:1] in ('{', '['):
        logging.error(f"[FSS오픈API 응답이상] {jsp_name} | HTTP {res.status_code} | 요청URL: {res.url} | 응답원문(500자): {res.text[:500]}")
    return res


def supabase_upsert(table: str, data: list) -> bool:
    if not data:
        return True

    conflict = CONFLICT_COLUMNS.get(table, '')
    # 배치 내 conflict key 중복 제거 (모든 fetcher에 공통 적용, ON CONFLICT 오류 방지)
    data = _dedupe_by_conflict(table, data, conflict)

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if conflict:
        url += f"?on_conflict={conflict}"

    try:
        res = requests.post(
            url,
            headers={**HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
            json=data,
            timeout=30
        )
        if res.status_code >= 400:
            logging.error(f"[{table}] upsert 실패 ({res.status_code}): {res.text[:200]}")
            res.raise_for_status()
        logging.info(f"[{table}] {len(data)}건 upsert 완료")
        return True
    except requests.exceptions.HTTPError as e:
        _mark_upsert_failure(table, f"HTTP {e.response.status_code if e.response is not None else '?'}")
        return False
    except Exception as e:
        _mark_upsert_failure(table, type(e).__name__)
        return False


def supabase_select(table: str, params: dict = None) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        res = requests.get(
            url,
            headers=HEADERS,
            params=params or {'select': '*'},
            timeout=30
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.error(f"[{table}] 조회 실패: {type(e).__name__}")
        return []


def supabase_select_all(table: str, params: dict = None, page_size: int = 1000, max_pages: int = 20) -> list:
    """
    PostgREST 기본 응답 상한(1000행)을 넘는 전체 조회.
    offset/limit 페이징으로 반복 조회 후 병합.
    """
    base_params = dict(params or {'select': '*'})
    base_params.pop('limit', None)
    base_params.pop('offset', None)
    all_rows = []
    for page in range(max_pages):
        page_params = {**base_params, 'limit': str(page_size), 'offset': str(page * page_size)}
        batch = supabase_select(table, page_params)
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
    else:
        logging.warning(f"[{table}] select_all 최대 페이지({max_pages}) 도달 - 결과가 잘렸을 수 있음")
    return all_rows


def has_recent_data(table: str, filters: dict, date_field: str, days: int) -> bool:
    """
    월간/분기 등 저빈도 수집기의 재시도 크론용 가드.
    filters 조건에 date_field가 최근 days일 이내인 행이 이미 있으면 True
    (이번 재시도 구간에 이미 성공했다는 뜻이므로 API 호출 없이 스킵).
    """
    cutoff = (datetime.now(KST) - timedelta(days=days)).strftime('%Y-%m-%d')
    params = {**filters, date_field: f'gte.{cutoff}', 'select': 'id', 'limit': '1'}
    rows = supabase_select(table, params)
    return bool(rows)


def now_kst() -> str:
    return datetime.now(KST).isoformat()


def today_kst() -> str:
    return datetime.now(KST).strftime('%Y-%m-%d')
