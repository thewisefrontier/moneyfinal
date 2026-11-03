"""한국 IPO(공모) 수집기 — OpenDART 증권신고서(지분증권) 공식 API만 사용.

list.json(공시 목록)에서 '증권신고서(지분증권)' 중 비상장법인(corp_cls=E)을 고르고,
estkRs.json(지분증권 주요정보)에서 청약기일·납입일·공모가·수량·인수인을 읽어 data/ipo/kr.json 에 쓴다.
상장 법인(Y/K)의 증권신고서는 유상증자라서 제외. 수요예측 일정·희망가격 밴드·상장일·경쟁률은 신고서 본문/KIND에만 있어 포함하지 않는다.
"""
import json
import os
import re
import sys
import time
from datetime import date, timedelta

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'ipo', 'kr.json')
API = 'https://opendart.fss.or.kr/api'
DAYS = 400  # 최초 수집 범위, 이후엔 기존 파일을 유지하고 최근 DAYS_INC일만 다시 본다
DAYS_INC = 45


def key():
    k = os.environ.get('DART_API_KEY')
    if not k and os.path.exists(os.path.join(ROOT, '.env')):
        for ln in open(os.path.join(ROOT, '.env'), encoding='utf-8'):
            if ln.startswith('DART_API_KEY='):
                k = ln.strip().partition('=')[2]
    return k


def num(s):
    s = re.sub(r'[^\d.]', '', s or '')
    return int(float(s)) if s else None


def dates(s):
    """'2026년 12월 01일 ~ 2026년 12월 02일' -> ['2026-12-01', '2026-12-02']"""
    return ['%04d-%02d-%02d' % tuple(map(int, m)) for m in re.findall(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', s or '')]


def get(path, **p):
    for i in range(3):
        try:
            r = requests.get(f'{API}/{path}', params={'crtfc_key': KEY, **p}, timeout=30).json()
            return r
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return {}


def filings(bgn, end):
    out, page = [], 1
    while True:
        r = get('list.json', bgn_de=bgn, end_de=end, pblntf_ty='C', page_no=page, page_count=100)
        if r.get('status') != '000':
            break
        out += [x for x in r['list'] if '증권신고서(지분증권)' in x['report_nm'] and x['corp_cls'] == 'E']
        if page >= int(r['total_page']):
            break
        page += 1
    print(f'  증권신고서(지분증권, 비상장) {len(out)}건 ({bgn}~{end})', flush=True)
    return out


def detail(f):
    # 기재정정·발행조건확정은 최초 접수일 기준으로 묶이므로 넉넉한 기간으로 조회해 가장 최근 접수분을 쓴다
    d = date(int(f['rcept_dt'][:4]), int(f['rcept_dt'][4:6]), int(f['rcept_dt'][6:]))
    r = get('estkRs.json', corp_code=f['corp_code'], bgn_de=(d - timedelta(days=150)).strftime('%Y%m%d'), end_de=f['rcept_dt'])
    if r.get('status') != '000':
        return None
    g = {x['title']: x['list'] for x in r['group']}

    def last(title):
        rows = g.get(title) or [{}]
        top = max(x.get('rcept_no', '') for x in rows)
        return [x for x in rows if x.get('rcept_no', '') == top]
    base, sec = last('일반사항')[0], last('증권의종류')[0]
    uws = last('인수인정보')
    und = [u['actnmn'] for u in uws if u.get('actsen') in ('대표', '공동대표')] or [u['actnmn'] for u in uws if u.get('actnmn')]
    sub = dates(base.get('sbd'))
    return {
        'corp': f['corp_name'], 'code': f['corp_code'], 'rcept': f['rcept_no'], 'filed': f['rcept_dt'],
        'sub': sub[:2], 'pay': (dates(base.get('pymd')) or [None])[0],
        'price': num(sec.get('slprc')), 'shares': num(sec.get('stkcnt')), 'amount': num(sec.get('slta')),
        'method': sec.get('slmthn'), 'stock': sec.get('stksen'), 'uw': und[:3],
        'spac': '스팩' in f['corp_name'] or '기업인수목적' in f['corp_name'],
    }


def main():
    today = date.today()
    old = json.load(open(OUT, encoding='utf-8'))['items'] if os.path.exists(OUT) else []
    known = {x['code']: x for x in old}
    span = DAYS_INC if old else DAYS
    fl, end = [], today
    while end > today - timedelta(days=span):  # corp_code 없이는 조회 기간이 3개월까지라 85일씩 끊어서 조회
        bgn = max(end - timedelta(days=85), today - timedelta(days=span))
        fl += filings(bgn.strftime('%Y%m%d'), end.strftime('%Y%m%d'))
        end = bgn - timedelta(days=1)
    latest = {}
    for f in fl:  # 기재정정이 여러 번 나오므로 회사별 최신 접수만
        if f['corp_code'] not in latest or f['rcept_no'] > latest[f['corp_code']]['rcept_no']:
            latest[f['corp_code']] = f
    for n, f in enumerate(latest.values(), 1):
        if f['corp_code'] in known and known[f['corp_code']]['rcept'] >= f['rcept_no']:
            continue
        d = detail(f)
        if d and d['sub']:
            known[f['corp_code']] = d
        time.sleep(0.2)
    items = sorted(known.values(), key=lambda x: x['sub'][0], reverse=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({'updated_at': today.isoformat(), 'source': 'OpenDART 증권신고서(지분증권) 주요정보', 'items': items},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'저장 {len(items)}건')
    for x in items[:8]:
        print(x['sub'], x['corp'], x['price'], x['shares'], x['uw'], 'SPAC' if x['spac'] else '')


KEY = key()
if __name__ == '__main__':
    if not KEY:
        sys.exit('DART_API_KEY 없음')
    main()
