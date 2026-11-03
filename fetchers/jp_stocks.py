"""일본 상장 종목 1단계 수집기 (API 키 불필요).

- 종목 마스터: EDINET 제출자 코드표(금융청, 공공데이터 이용규약 PDL1.0) — 상장사의 일본어명·영문명·증권코드·업종·결산월.
- 시세: Yahoo Finance(yfinance) 일괄 다운로드. 시가총액은 fast_info로 종목당 한 번 받아 두고(data/jp/mcap.json) 매일 종가 비율로 갱신하며,
  한 번에 MCAP_PER_RUN(250)개씩만 새로 받아 며칠에 걸쳐 전 종목을 채운다(Yahoo 호출량 제한).
출력: data/jp/index.json(마스터), data/jp/quotes.json(전 종목 종가·전일·거래량·시가총액 + 지수), data/jp/mcap.json(캐시).
출처 표기: EDINET 제출자 코드표(금융청)를 가공, 시세는 Yahoo Finance.
"""
import csv
import io
import json
import os
import re
import time
import unicodedata
import zipfile
from datetime import date

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'jp')
CODE_URL = 'https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip'
UA = {'User-Agent': 'Mozilla/5.0 moneyfinal'}
MCAP_PER_RUN = 250
MCAP_ONLY = '--mcap-only' in __import__('sys').argv  # 시세 다운로드를 건너뛰고 시가총액 캐시만 채움
INDICES = {'N225': '^N225', 'TOPIX_ETF': '1306.T', 'USDJPY': 'JPY=X'}

IND_EN = {
    '水産・農林業': 'Fishery, Agriculture & Forestry', '鉱業': 'Mining', '建設業': 'Construction', '食料品': 'Foods', '繊維製品': 'Textiles & Apparel',
    'パルプ・紙': 'Pulp & Paper', '化学': 'Chemicals', '医薬品': 'Pharmaceuticals', '石油・石炭製品': 'Oil & Coal Products', 'ゴム製品': 'Rubber Products',
    'ガラス・土石製品': 'Glass & Ceramics', '鉄鋼': 'Iron & Steel', '非鉄金属': 'Nonferrous Metals', '金属製品': 'Metal Products', '機械': 'Machinery',
    '電気機器': 'Electric Appliances', '輸送用機器': 'Transportation Equipment', '精密機器': 'Precision Instruments', 'その他製品': 'Other Products',
    '電気・ガス業': 'Electric Power & Gas', '陸運業': 'Land Transportation', '海運業': 'Marine Transportation', '空運業': 'Air Transportation',
    '倉庫・運輸関連業': 'Warehousing & Transport Services', '情報・通信業': 'Information & Communication', '卸売業': 'Wholesale Trade', '小売業': 'Retail Trade',
    '銀行業': 'Banks', '証券、商品先物取引業': 'Securities & Commodity Futures', '保険業': 'Insurance', 'その他金融業': 'Other Financing Business',
    '不動産業': 'Real Estate', 'サービス業': 'Services',
}
IND_KO = {
    '水産・農林業': '수산·농림업', '鉱業': '광업', '建設業': '건설업', '食料品': '식료품', '繊維製品': '섬유제품', 'パルプ・紙': '펄프·종이', '化学': '화학',
    '医薬品': '의약품', '石油・石炭製品': '석유·석탄제품', 'ゴム製品': '고무제품', 'ガラス・土石製品': '유리·토석제품', '鉄鋼': '철강', '非鉄金属': '비철금속',
    '金属製品': '금속제품', '機械': '기계', '電気機器': '전기기기', '輸送用機器': '수송용 기기', '精密機器': '정밀기기', 'その他製品': '기타 제품',
    '電気・ガス業': '전기·가스업', '陸運業': '육운업', '海運業': '해운업', '空運業': '항공운수업', '倉庫・運輸関連業': '창고·운수관련업', '情報・通信業': '정보·통신업',
    '卸売業': '도매업', '小売業': '소매업', '銀行業': '은행업', '証券、商品先物取引業': '증권·상품선물업', '保険業': '보험업', 'その他金融業': '기타 금융업',
    '不動産業': '부동산업', 'サービス業': '서비스업',
}
SUF = re.compile(r'[,\s]*(co[.,]*\s*ltd[.,]*|co[.,]*|inc[.,]*|corp(oration)?[.,]*|company|limited|ltd[.,]*|holdings?)\s*$', re.I)


def clean_en(s):
    s = re.sub(r'\s+', ' ', s).strip(' ,')
    for _ in range(3):
        n = SUF.sub('', s).strip(' ,')
        if n == s or not n:
            break
        s = n
    if s.isupper() and len(s) > 4:  # 전부 대문자인 영문명만 보기 좋게(NTT·KDDI 같은 약어는 어쩔 수 없이 바뀜)
        s = ' '.join(w if len(w) <= 3 else w.title() for w in s.split(' '))
    return s


def clean_ja(s):
    s = unicodedata.normalize('NFKC', s).replace('株式会社', '')  # 전각 영문·숫자를 반각으로
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'(?<=[^\x00-\x7f]) | (?=[^\x00-\x7f])', '', s)  # 일본어 글자 옆 공백만 제거(영문 단어 사이는 유지)


def master():
    r = requests.get(CODE_URL, headers=UA, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    rows = list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode('cp932'))))
    h = rows[1]
    ix = {k: h.index(k) for k in ['提出者名', '提出者名（英字）', '上場区分', '提出者業種', '証券コード', '決算日']}
    out = []
    for x in rows[2:]:
        if len(x) <= ix['証券コード'] or x[ix['上場区分']] != '上場' or not x[ix['証券コード']].strip():
            continue
        code = x[ix['証券コード']].strip()
        m = re.match(r'(\d+)月', x[ix['決算日']])
        out.append([code[:4], clean_ja(x[ix['提出者名']]), clean_en(x[ix['提出者名（英字）']]) or '', x[ix['提出者業種']], int(m.group(1)) if m else 0])
    uniq = {}
    for r_ in out:
        uniq.setdefault(r_[0], r_)  # 보통주 기준 4자리 코드 중복 제거
    return sorted(uniq.values())


def load(p, default):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def main():
    import yfinance as yf
    import pandas as pd
    os.makedirs(OUT, exist_ok=True)
    today = date.today().isoformat()
    stocks = master()
    json.dump({'updated_at': today, 'count': len(stocks), 'source': 'EDINET 제출자 코드표(금융청)', 'ind_en': IND_EN, 'ind_ko': IND_KO, 'stocks': stocks},
              open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('마스터', len(stocks), flush=True)
    syms = {s[0]: s[0] + '.T' for s in stocks}

    # 종가·전일·거래량(일괄). Yahoo가 429를 주기 쉬워 묶음을 작게 하고 쉬어 가며, 연속으로 막히면 그날은 접는다.
    old = load(os.path.join(OUT, 'quotes.json'), {}).get('q', {})
    quotes, miss, fails = {}, [], 0
    tks = list(syms)
    for i in range(0, 0 if MCAP_ONLY else len(tks), 100):
        chunk = [syms[t] for t in tks[i:i + 100]]
        got = 0
        for attempt in range(2):
            try:
                d = yf.download(chunk, period='10d', progress=False, group_by='ticker', threads=False, auto_adjust=False)
            except Exception as e:  # noqa: BLE001
                print('  묶음 실패', i, type(e).__name__, flush=True)
                d = None
            if d is not None:
                for s_ in chunk:
                    try:
                        c = d[s_]['Close'].dropna()
                        v = d[s_]['Volume'].dropna()
                        if len(c) >= 2:
                            quotes[s_[:-2]] = [round(float(c.iloc[-1]), 2), round(float(c.iloc[-2]), 2), int(v.iloc[-1]) if len(v) else 0, c.index[-1].strftime('%Y-%m-%d')]
                            got += 1
                    except Exception:  # noqa: BLE001
                        pass
            if got >= 20:
                break
            time.sleep(45)  # 429면 잠시 쉬었다가 한 번만 재시도
        fails = fails + 1 if got < 20 else 0
        print(f'  시세 {min(i + 100, len(tks))}/{len(tks)} (+{got})', flush=True)
        if fails >= 3:
            print('  연속으로 막혀 오늘은 여기까지(이전 시세는 유지)', flush=True)
            break
        time.sleep(3)
    for t, v in old.items():  # 오늘 못 받은 종목은 이전 값을 유지
        if t not in quotes and t in syms:
            quotes[t] = [v[0], v[1], v[2], '' if len(v) < 4 else '']
    print('시세', len(quotes), flush=True)

    # 시가총액 캐시: 없거나 오래된 종목부터 MCAP_PER_RUN개(429면 중단)
    mp = os.path.join(OUT, 'mcap.json')
    mc = load(mp, {})
    # 아직 없는 종목부터, 그중 거래대금(종가×거래량)이 큰 종목 우선 — 대형주의 시가총액이 먼저 채워져 순위가 빨리 맞아진다
    todo = sorted([t for t in quotes if t not in mc or mc[t][1] < today[:7]],
                  key=lambda t: (t in mc, mc.get(t, ['', ''])[1], -(quotes[t][0] * quotes[t][2])))[:MCAP_PER_RUN]
    for n, t in enumerate(todo, 1):
        try:
            v = yf.Ticker(syms[t]).fast_info.get('marketCap')
            if v:
                mc[t] = [int(v), today, quotes[t][0]]  # [시총, 받은 날, 그때 종가]
        except Exception as e:  # noqa: BLE001
            if 'RateLimit' in type(e).__name__:
                print('  시가총액 수집 중 429 - 중단', flush=True)
                break
        if n % 50 == 0:
            print(f'  시가총액 {n}/{len(todo)}', flush=True)
        time.sleep(0.4)
    json.dump(mc, open(mp, 'w', encoding='utf-8'), separators=(',', ':'))

    q = {}
    for t, (p, prev, vol, d_) in quotes.items():
        cap = None
        if t in mc and mc[t][2]:
            cap = int(mc[t][0] * p / mc[t][2])  # 종가 비율로 오늘 시총 근사
        q[t] = [p, prev, vol, cap]
    idx = {}
    for k, s in INDICES.items():
        try:
            h = yf.Ticker(s).history(period='7d')['Close'].dropna()
            idx[k] = [round(float(h.iloc[-1]), 2), round(float(h.iloc[-2]), 2)]
        except Exception:  # noqa: BLE001
            pass
    asof = max((v[3] for v in quotes.values()), default=today)
    if MCAP_ONLY:
        asof = load(os.path.join(OUT, 'quotes.json'), {}).get('asof') or asof
    json.dump({'updated_at': today, 'asof': asof, 'source': 'Yahoo Finance', 'idx': idx, 'q': q},
              open(os.path.join(OUT, 'quotes.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    have = sum(1 for v in q.values() if v[3])
    print(f'저장: 시세 {len(q)}종목, 시가총액 있는 종목 {have}, 지수 {list(idx)}')


if __name__ == '__main__':
    main()
