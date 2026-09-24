"""
공통 유틸리티 - Cloudflare D1 HTTP API 헬퍼
(2026-09: Supabase REST API에서 D1로 이전. 함수 시그니처는 기존과 동일하게 유지해서
 fetchers/processors/exporters 쪽 호출부는 손대지 않음 - 이름은 supabase_* 그대로지만
 내부 구현만 D1로 교체됨. 이름 정리는 별도 후속 작업으로 남겨둠.)
"""
import atexit
import json
import os
import logging
import requests
import sys
import time
from datetime import datetime, timedelta
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

KST = pytz.timezone('Asia/Seoul')

CF_ACCOUNT_ID = os.environ['CF_ACCOUNT_ID']
CF_API_TOKEN = os.environ['CF_API_TOKEN']
CF_D1_DATABASE_ID = os.environ['CF_D1_DATABASE_ID']

D1_QUERY_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"
D1_HEADERS = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json',
}

# SQLite/D1 바인드 파라미터 상한(SQLITE_MAX_VARIABLE_NUMBER 기본값 999).
# 배치 upsert 시 컴럼 수 대비 안전하게 청크 크기를 계산하는 데 사용.
D1_MAX_BOUND_PARAMS = 900

# 테이블별 upsert conflict 컴럼 (Supabase 시절과 동일 - D1 UNIQUE 인덱스와 1:1 대응,
# migrations/0001_init.sql 참고. stock_dividends/stock_issuance는 원본 Postgres 제약과
# 실제로 달랐던 케이스이니 그 파일 상단 주석 참고)
CONFLICT_COLUMNS = {
    'rates': 'institution,product_name,category,period',
    'market_indicators': 'indicator_code,reference_date',
    'corporate_alerts': 'company_name,alert_type,disclosure_date',
    'ipo_status': 'company_name,status,request_date',
    'financial_health': 'institution,reference_date',
    'daily_briefing': 'briefing_date',
    'stock_prices': 'stock_code,base_date,market_type',
    'stock_short': 'stock_code,base_date',
    'stock_dividends': 'stock_code,base_date',
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
    'kr_etf_dividends': 'ticker,ex_dividend_date',
    'kr_etf_prices': 'ticker',
    'market_news': 'url',
    'us_company_profile': 'ticker',
    'us_company_financials': 'ticker,fiscal_year,period',
    'us_company_earnings': 'ticker,report_date',
    'us_company_dividends': 'ticker,ex_date',
    'us_company_splits': 'ticker,split_date',
    'crypto_prices': 'id',
    'superinvestor_holdings': 'investor_name,cusip',
    'stock_ai_reports': 'code',
}


_UPSERT_FAILURES = 0


def _mark_upsert_failure(table: str, reason: str) -> None:
    global _UPSERT_FAILURES
    _UPSERT_FAILURES += 1
    logging.error(f"[{table}] upsert 실패 누적 {_UPSERT_FAILURES}건 (사유: {reason})")


def _exit_if_upsert_failures() -> None:
    if _UPSERT_FAILURES > 0:
        logging.error(f"⚠️ upsert 실패 총 {_UPSERT_FAILURES}건 → 프로세스 종료 코드 1")
        os._exit(1)


atexit.register(_exit_if_upsert_failures)


def _dedupe_by_conflict(table: str, data: list, conflict: str) -> list:
    """배치 내 conflict key 조합 중복 제거.
    SQLite도 ON CONFLICT DO UPDATE 시 같은 statement 안에 conflict 키 조합이
    중복되면 오류를 반환한다(Postgres와 동일). 같은 키 조합이면 마지막 행이 최종 반영."""
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


def _coerce_value(v):
    """D1(SQLite) 바인드 파라미터로 보낼 수 있는 타입으로 변환.
    Supabase REST는 boolean을 JSON true/false로, jsonb를 dict/list로 돌려주는데
    D1은 boolean 타입이 없어 INTEGER(0/1)로, jsonb는 TEXT(JSON 문자열)로 저장해야 함."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v


def _d1_query(sql: str, params: list = None, timeout: int = 30) -> list:
    """D1 HTTP API로 SQL 1개 실행. 성공 시 결과 행(list of dict) 반환."""
    res = requests.post(
        D1_QUERY_URL,
        headers=D1_HEADERS,
        json={'sql': sql, 'params': params or []},
        timeout=timeout
    )
    if res.status_code >= 400:
        raise requests.exceptions.HTTPError(f"D1 HTTP {res.status_code}: {res.text[:300]}", response=res)
    body = res.json()
    if not body.get('success'):
        raise RuntimeError(f"D1 query 실패: {str(body.get('errors'))[:300]}")
    results = body.get('result') or []
    if not results or not results[0].get('success', True):
        raise RuntimeError(f"D1 query 실패(result): {str(results)[:300]}")
    return results[0].get('results') or []


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
    """D1 upsert. INSERT ... ON CONFLICT(conflict_cols) DO UPDATE SET ... 를
    여러 행을 한 statement에 묶어(VALUES (...),(...),...) 보낸다.
    SQLite 바인드 파라미터 상한(999)을 넘지 않도록 컬럼 수 기준으로 청크 분할."""
    if not data:
        return True

    conflict = CONFLICT_COLUMNS.get(table, '')
    data = _dedupe_by_conflict(table, data, conflict)

    # 배치 내 행마다 존재하는 컬럼 집합이 다를 수 있으므로 합집합을 취하고 없는 값은 NULL로 채움
    all_cols = []
    seen_cols = set()
    for row in data:
        for k in row.keys():
            if k not in seen_cols:
                seen_cols.add(k)
                all_cols.append(k)

    conflict_cols = [c.strip() for c in conflict.split(',')] if conflict else []
    update_cols = [c for c in all_cols if c not in conflict_cols]

    chunk_size = max(1, D1_MAX_BOUND_PARAMS // max(1, len(all_cols)))

    col_list_sql = ', '.join(f'"{c}"' for c in all_cols)
    conflict_sql = ', '.join(f'"{c}"' for c in conflict_cols)
    if update_cols:
        update_sql = ', '.join(f'"{c}"=excluded."{c}"' for c in update_cols)
        upsert_clause = f'ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}' if conflict_cols else ''
    else:
        upsert_clause = f'ON CONFLICT({conflict_sql}) DO NOTHING' if conflict_cols else ''

    ok = True
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        values_sql = ', '.join('(' + ', '.join(['?'] * len(all_cols)) + ')' for _ in chunk)
        params = []
        for row in chunk:
            for c in all_cols:
                params.append(_coerce_value(row.get(c)))
        sql = f'INSERT INTO "{table}" ({col_list_sql}) VALUES {values_sql} {upsert_clause}'
        try:
            _d1_query(sql, params)
        except Exception as e:
            logging.error(f"[{table}] upsert 실패 ({len(chunk)}건): {type(e).__name__}: {str(e)[:200]}")
            _mark_upsert_failure(table, type(e).__name__)
            ok = False
            continue
    if ok:
        logging.info(f"[{table}] {len(data)}건 upsert 완료")
    return ok


def _params_to_sql(table: str, params: dict) -> tuple:
    """기존 PostgREST 스타일 params(dict)를 D1용 SELECT SQL로 변환.
    지원 형식: select=col1,col2|*, order=col.asc/desc(,col2...), limit, offset,
              eq.X / gte.X / lte.X / in.(a,b,c) 필터.
    코드베이스에서 실제로 쓰인 필터 형태만 지원(그 외 형태가 들어오면 예외 발생)."""
    params = dict(params or {'select': '*'})
    select = params.pop('select', '*')
    order = params.pop('order', None)
    limit = params.pop('limit', None)
    offset = params.pop('offset', None)

    select_sql = '*' if select == '*' else ', '.join(f'"{c.strip()}"' for c in select.split(','))

    where_clauses = []
    bind_params = []
    for key, value in params.items():
        if value.startswith('eq.'):
            where_clauses.append(f'"{key}" = ?')
            bind_params.append(value[3:])
        elif value.startswith('gte.'):
            where_clauses.append(f'"{key}" >= ?')
            bind_params.append(value[4:])
        elif value.startswith('lte.'):
            where_clauses.append(f'"{key}" <= ?')
            bind_params.append(value[4:])
        elif value.startswith('gt.'):
            where_clauses.append(f'"{key}" > ?')
            bind_params.append(value[3:])
        elif value.startswith('lt.'):
            where_clauses.append(f'"{key}" < ?')
            bind_params.append(value[3:])
        elif value.startswith('in.('):
            items = value[4:-1].split(',') if value[4:-1] else []
            placeholders = ','.join(['?'] * len(items))
            where_clauses.append(f'"{key}" IN ({placeholders})')
            bind_params.extend(items)
        else:
            raise ValueError(f"지원하지 않는 필터 형식: {key}={value}")

    sql = f'SELECT {select_sql} FROM "{table}"'
    if where_clauses:
        sql += ' WHERE ' + ' AND '.join(where_clauses)
    if order:
        order_parts = []
        for part in order.split(','):
            part = part.strip()
            if '.' in part:
                col, direction = part.rsplit('.', 1)
                direction = 'ASC' if direction.startswith('asc') else 'DESC'
            else:
                col, direction = part, 'ASC'
            order_parts.append(f'"{col}" {direction}')
        sql += ' ORDER BY ' + ', '.join(order_parts)
    if limit is not None:
        sql += f' LIMIT {int(limit)}'
    if offset is not None:
        sql += f' OFFSET {int(offset)}'
    return sql, bind_params


def supabase_select(table: str, params: dict = None) -> list:
    try:
        sql, bind_params = _params_to_sql(table, params)
        return _d1_query(sql, bind_params)
    except Exception as e:
        logging.error(f"[{table}] 조회 실패: {type(e).__name__}: {str(e)[:200]}")
        return []


def supabase_select_all(table: str, params: dict = None, page_size: int = 1000, max_pages: int = 20) -> list:
    """D1은 PostgREST식 1000행 응답 상한이 없어 사실상 한 번에 다 가져올 수 있지만,
    호출부 호환을 위해 기존과 동일한 페이징 시그니처를 유지한다."""
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


def supabase_delete_not_in(table: str, column: str, keep_values: list, extra_eq: dict = None) -> bool:
    """keep_values에 없는 행을 삭제. 매일/매분기 top-N만 다시 upsert하는 스냅샷성
    테이블에서 순위·보유 밖으로 밀려난 옛 행이 영구히 남는 걸 방지하기 위함.
    extra_eq: 같은 테이블을 여러 그룹(예: 투자자별)으로 나눠 쓸 때, 그 그룹의
    행만 대상으로 삼기 위한 추가 등호 필터.

    D1은 SQL IN 절 파라미터 개수에 사실상 999 바인드 제한이 있으므로
    (Supabase 시절 URL 길이 414 문제와 동일한 이유로) 청크로 나눠 삭제한다."""
    if not keep_values:
        return True
    select_params = {'select': column}
    if extra_eq:
        select_params.update({k: f'eq.{v}' for k, v in extra_eq.items()})
    existing = supabase_select(table, select_params)
    stale = {str(row[column]) for row in existing} - {str(v) for v in keep_values}
    if not stale:
        return True
    stale_list = list(stale)
    ok = True
    for i in range(0, len(stale_list), 200):
        chunk = stale_list[i:i + 200]
        where_clauses = [f'"{column}" IN ({",".join(["?"] * len(chunk))})']
        bind_params = list(chunk)
        if extra_eq:
            for k, v in extra_eq.items():
                where_clauses.append(f'"{k}" = ?')
                bind_params.append(v)
        sql = f'DELETE FROM "{table}" WHERE ' + ' AND '.join(where_clauses)
        try:
            _d1_query(sql, bind_params)
        except Exception as e:
            logging.error(f"[{table}] 잔여 행 삭제 실패: {type(e).__name__}: {str(e)[:200]}")
            ok = False
    return ok


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
