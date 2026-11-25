"""데이터 신선도 점검 — data/*.json 안의 '내용 기준 최신 날짜'가 기한을 넘겼는지 본다.

배경: daily.yml 등은 단계마다 continue-on-error라 수집이 조용히 죽어도 워크플로는 초록색이다(실제로 의원 거래 스캔이
옵션 파싱 버그로 4일 연속 실패한 것도 코인·보험 같은 다른 단계에 가려 늦게 발견됨). 이 스크립트가 마지막에 한 번 더
'결과 파일의 날짜'를 보고 낡았으면 종료코드 1로 끝나 GitHub이 실패 알림을 보내게 한다.

  python scripts/check_data_health.py          # Actions가 갱신하는 데이터만 검사(기본). 낡은 게 있으면 종료코드 1
  python scripts/check_data_health.py --local  # 이 PC에서만 갱신되는 데이터(한국 재무 분기·기업 재무)도 함께 검사하고 할 일을 안내
"""
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()
DT = re.compile(r'^(20\d\d)-(\d\d)-(\d\d)')


def load(rel):
    p = os.path.join(ROOT, rel)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def latest_date(o, cap=None):
    """JSON 안 문자열 중 오늘 이전의 가장 늦은 날짜(YYYY-MM-DD로 시작하는 값)."""
    best = ['']

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x[:20000]:
                walk(v)
        elif isinstance(x, str) and DT.match(x):
            d = x[:10]
            if d <= TODAY.isoformat() and d > best[0]:
                best[0] = d
    walk(o)
    return best[0] or None


def field(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k):
            return str(d[k])[:10]
    return None


# (표시 이름, 파일, 날짜를 구하는 방법, 허용 일수)  — 방법: 'content'(내용 속 최신 날짜) | 필드 이름
CHECKS = [
    ('시장 지표', 'data/market.json', 'content', 7),
    ('국내·미국 시세', 'data/stocks.json', 'content', 7),
    ('채권', 'data/bonds.json', 'content', 8),
    ('일일 브리핑', 'data/briefing.json', 'content', 4),
    ('배당 ETF', 'data/dividends.json', 'content', 7),
    ('국내 배당 ETF', 'data/kr_dividends.json', 'content', 7),
    ('지표 히스토리', 'data/indicator_history.json', 'content', 7),
    ('종목 히스토리', 'data/stock_history.json', 'content', 7),
    ('행운의 아이템 핫딜', 'data/lucky_deals.json', 'updated_at', 3),
    ('IPO(한국)', 'data/ipo/kr.json', 'updated_at', 4),
    ('IPO(미국)', 'data/ipo/us.json', 'updated_at', 4),
    ('일본 종목 시세', 'data/jp/quotes.json', 'asof', 6),
    ('미국 기업 재무', 'data/us_fin/index.json', 'updated_at', 14),
    ('의원 거래(하원)', 'data/congress/trades_%d.json' % TODAY.year, 'updated_at', 14),
    # 월 1회(21~25일) 갱신 — 한 달 + 여유
    ('예금·적금 금리', 'data/rates.json', 'content', 45),
    ('대출 상품', 'data/loans.json', 'content', 45),
    ('연금저축', 'data/annuity.json', 'content', 50),
    # 분기 1회
    ('종목 AI 요약', 'data/stock_reports.json', 'content', 130),
    ('슈퍼인베스터 13F', 'data/superinvestors.json', 'content', 150),
]


def check_actions():
    rows, bad = [], 0
    for name, rel, how, limit in CHECKS:
        d = load(rel)
        if d is None:
            rows.append((name, '파일 없음', None, limit, False))
            bad += 1
            continue
        ds = latest_date(d) if how == 'content' else field(d, how)
        if not ds:
            rows.append((name, '날짜 없음', None, limit, False))
            bad += 1
            continue
        age = (TODAY - date.fromisoformat(ds)).days
        ok = age <= limit
        bad += 0 if ok else 1
        rows.append((name, ds, age, limit, ok))
    return rows, bad


def expected_quarter():
    """공시 기한(분기 말 + 50일, 사업보고서는 +95일)이 지난 가장 최근 분기 말."""
    cands = []
    for y in (TODAY.year - 1, TODAY.year):
        for m, dd in ((3, 31), (6, 30), (9, 30), (12, 31)):
            qe = date(y, m, dd)
            cands.append((qe, qe + timedelta(days=95 if m == 12 else 50)))
    return max(qe for qe, dl in cands if dl <= TODAY)


def check_local():
    """이 PC에서만 갱신되는 데이터. (이름, 상태, 할 일) 목록."""
    out = []
    eq = expected_quarter()
    kf = load('data/kr_fin/00.json')
    if kf and '005930' in kf:
        q = (kf['005930'].get('q') or {}).get('e') or []
        got = date.fromisoformat(q[-1]) if q else None
        if not got or got < eq:
            out.append(('한국 재무 분기(kr-fin)', f'최신 {got} < 공시된 {eq}', 'python scripts/build_sim_data.py finkr q  (이어서 finkr2)'))
    exp_fy = TODAY.year - 2 if TODAY.month < 4 else TODAY.year - 1
    cf = load('data/corp_finance.json')
    if cf:
        fy = max((c.get('fiscal_year') or 0 for c in cf.get('companies', [])), default=0)
        if fy < exp_fy:
            out.append(('기업 재무(corp_finance)', f'{fy}년 < {exp_fy}년', 'python scripts/local_daily_update.py'))
    return out


def main():
    rows, bad = check_actions()
    print(f'데이터 신선도 점검 (기준일 {TODAY})')
    for name, ds, age, limit, ok in rows:
        print(f"  {'OK ' if ok else '낡음'} {name:16s} {ds}" + (f'  ({age}일 전, 허용 {limit}일)' if age is not None else f'  (허용 {limit}일)'))
    if '--local' in sys.argv:
        loc = check_local()
        print('\n로컬 전용 데이터' + ('' if loc else ': 모두 최신'))
        for name, status, todo in loc:
            print(f'  갱신 필요 {name}: {status}\n    -> {todo}')
    if bad:
        print(f'\n낡은 데이터 {bad}건 — 해당 수집 워크플로 로그를 확인하세요.')
        sys.exit(1)
    print('\n모두 기한 안입니다.')


if __name__ == '__main__':
    main()
