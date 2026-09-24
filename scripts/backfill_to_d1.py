"""
1회성 데이터 백필: Supabase(Postgres) -> Cloudflare D1

사용법 (로컬 또는 GitHub Actions workflow_dispatch에서):
  SUPABASE_URL=... SUPABASE_KEY=...(service role) \
  CF_ACCOUNT_ID=... CF_API_TOKEN=... CF_D1_DATABASE_ID=... \
  python scripts/backfill_to_d1.py [table1 table2 ...]

인자 없이 실행하면 TABLES 전체를 순서대로 백필한다.
D1 스키마(migrations/0001_init.sql)가 이미 적용되어 있어야 한다
(`wrangler d1 execute moneyfinal-db --remote --file=migrations/0001_init.sql`).

멱등성: utils.common.supabase_upsert()의 ON CONFLICT DO UPDATE를 그대로 쓰므로
여러 번 실행해도 안전하다(재실행 시 최신 Supabase 값으로 덮어씀).
"""
import concurrent.futures
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from utils.common import supabase_upsert, CONFLICT_COLUMNS  # noqa: E402  (D1로 교체된 구현)

logger = logging.getLogger(__name__)

SB_URL = os.environ['SUPABASE_URL'].rstrip('/')
SB_KEY = os.environ['SUPABASE_KEY']
SB_HEADERS = {'apikey': SB_KEY, 'Authorization': f'Bearer {SB_KEY}'}

# migrations/0001_init.sql에 정의된 34개 테이블 전체 (card_news는 CONFLICT_COLUMNS에
# 없어 upsert 대상이 아니므로 별도 append-only 백필 필요 - 아래 TABLES에서 제외하고
# 필요 시 수동으로 따로 처리할 것)
TABLES = list(CONFLICT_COLUMNS.keys())

PAGE_SIZE = 1000

# D1 REST API가 statement당 파라미터 100개로 제한돼 있어(utils.common.D1_MAX_BOUND_PARAMS)
# supabase_upsert 내부에서 청크를 잘게(테이블당 몇 행씩) 나눠 순차 HTTP 요청을 보낸다.
# stock_prices처럼 행이 많은 테이블은 순차 실행 시 수만 건의 요청이 필요해 시간이
# 너무 오래 걸리므로(실측: corp_info 1013건/15컬럼 -> 169 요청에 94초), 데이터를
# 샤드로 나눠 여러 스레드에서 동시에 upsert 요청을 보낸다(네트워크 I/O 대기 구간이라
# GIL에 영향받지 않고 실측상 순차 대비 약 7배 빨라짐).
SHARD_SIZE = 3000
MAX_WORKERS = 10


def fetch_all_from_supabase(table: str) -> list:
    rows = []
    offset = 0
    while True:
        res = requests.get(
            f"{SB_URL}/rest/v1/{table}",
            headers=SB_HEADERS,
            params={'select': '*', 'limit': str(PAGE_SIZE), 'offset': str(offset)},
            timeout=30
        )
        res.raise_for_status()
        batch = res.json()
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def backfill_table(table: str) -> None:
    logger.info(f"[{table}] Supabase에서 조회 중...")
    rows = fetch_all_from_supabase(table)
    logger.info(f"[{table}] {len(rows)}건 조회됨 -> D1 upsert 시작")
    if not rows:
        return
    shards = [rows[i:i + SHARD_SIZE] for i in range(0, len(rows), SHARD_SIZE)]
    ok = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(shards))) as ex:
        futures = [ex.submit(supabase_upsert, table, shard) for shard in shards]
        for f in concurrent.futures.as_completed(futures):
            if not f.result():
                ok = False
    if not ok:
        logger.error(f"[{table}] 일부 실패 - 위 에러 로그 확인")
    else:
        logger.info(f"[{table}] 완료 ({len(rows)}건)")


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else TABLES
    logger.info(f"=== D1 백필 시작: {len(targets)}개 테이블 ===")
    for table in targets:
        if table not in TABLES:
            logger.error(f"알 수 없는 테이블: {table} (건너뜀)")
            continue
        try:
            backfill_table(table)
        except Exception as e:
            logger.error(f"[{table}] 백필 중 예외: {type(e).__name__}: {e}")
    logger.info("=== D1 백필 종료 ===")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    main()
