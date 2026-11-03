"""미국 IPO 수집기 — SEC EDGAR 공식 색인만 사용 (공정접근: 초당 10건 이하, User-Agent 선언).

분기별 form.idx 에서 S-1·F-1(신고서)·424B4(최종 설명서)·RW(철회)를 모으고, 기존 상장사(10-K·10-Q·20-F 제출 이력이 신고서보다 앞서 있는 회사)는
후속 공모이므로 제외한다. 공모가·규모는 본문을 읽어야 해서 1차 버전에는 넣지 않고, 단계(신고/확정/철회)와 원문 링크만 제공한다.
"""
import json
import os
import re
import time
from datetime import date, timedelta

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'ipo', 'us.json')
UA = {'User-Agent': 'moneyfinal-research overmandol@gmail.com'}
REG = {'S-1', 'S-1/A', 'F-1', 'F-1/A'}
PERIODIC = {'10-K', '10-Q', '20-F', '40-F', '10-KT', '10-K405', '8-K', '6-K', '424B1', '424B3', '424B5'}  # 신고서 이전에 이런 제출이 있으면 이미 상장된 회사
LOOKBACK = 300  # 일


def quarters(today):
    d, out = today - timedelta(days=LOOKBACK), []
    while d <= today:
        q = (d.year, (d.month - 1) // 3 + 1)
        if q not in out:
            out.append(q)
        d += timedelta(days=28)
    return out


def index_rows(y, q):
    t = requests.get(f'https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx', headers=UA, timeout=120).text
    for ln in t.splitlines():
        ft = ln[:17].strip()
        if ft in REG | {'424B4', 'RW'}:
            yield ft, ln[17:79].strip(), int(ln[79:91]), ln[91:103].strip(), ln[103:].strip()


def has_history(cik, before):
    """신고서 이전에 정기보고서를 낸 적이 있으면 이미 상장된 회사(후속 공모)."""
    r = requests.get(f'https://data.sec.gov/submissions/CIK{cik:010d}.json', headers=UA, timeout=30).json()
    time.sleep(0.15)
    rc = r['filings']['recent']
    hist = any((f in PERIODIC or (f == '424B4' and d < before)) and d < before for f, d in zip(rc['form'], rc['filingDate']))
    return hist, r


def main():
    today = date.today()
    cut = (today - timedelta(days=LOOKBACK)).isoformat()
    by = {}
    for y, q in quarters(today):
        for ft, name, cik, d, path in index_rows(y, q):
            if d < cut:
                continue
            c = by.setdefault(cik, {'name': name, 'cik': cik, 'reg': [], 'p': [], 'rw': []})
            if ft in REG:
                c['reg'].append((d, path))
            elif ft == '424B4':
                c['p'].append((d, path))
            else:
                c['rw'].append(d)
    print(f'후보 {len(by)}개 회사', flush=True)
    items = []
    for cik, c in by.items():
        if not c['reg']:  # 424B4만 있는 회사는 선반등록 후속 공모일 가능성이 커서 제외
            continue
        c['reg'].sort()
        first = c['reg'][0][0]
        try:
            hist, sub = has_history(cik, first)
        except Exception as e:  # noqa: BLE001
            print('  실패', cik, type(e).__name__, flush=True)
            continue
        if hist or re.search(r'ETF|Trust', sub.get('name') or c['name']):  # 상장펀드·신탁은 일반 IPO가 아님
            continue
        lastreg = c['reg'][-1]
        priced = max(c['p'])[0] if c['p'] else None
        rw = max(c['rw']) if c['rw'] else None
        status = 'priced' if priced and priced >= first else 'withdrawn' if rw and rw >= lastreg[0] else 'filed'
        if status == 'filed' and lastreg[0] < (today - timedelta(days=210)).isoformat():
            continue  # 7개월 넘게 움직임 없는 신고서는 사실상 중단
        tk = (sub.get('tickers') or [None])[0]
        ex = (sub.get('exchanges') or [None])[0]
        items.append({
            'name': sub.get('name') or c['name'], 'cik': cik, 'ticker': tk, 'exch': ex, 'sic': sub.get('sicDescription'),
            'spac': sub.get('sic') == '6770' or bool(re.search(r'acquisition|spac', c['name'], re.I)),
            'status': status, 'first': first, 'last': lastreg[0], 'priced': priced if status == 'priced' else None,
            'url': f'https://www.sec.gov/Archives/{(max(c["p"])[1] if status == "priced" else lastreg[1])}',
        })
    items.sort(key=lambda x: (x['priced'] or x['last']), reverse=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({'updated_at': today.isoformat(), 'source': 'SEC EDGAR full-index (S-1/F-1/424B4/RW)', 'items': items},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    from collections import Counter
    print('저장', len(items), Counter(x['status'] for x in items), 'SPAC', sum(x['spac'] for x in items))
    for x in items[:10]:
        print(x['status'], x['priced'] or x['last'], x['name'], x['ticker'], x['exch'], 'SPAC' if x['spac'] else '')


if __name__ == '__main__':
    main()
