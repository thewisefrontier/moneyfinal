"""영어판용 한글 이름 사전 data/en_names.json 생성.

- n: 한국 상장사 {한글 회사명: 영문명} — OpenDART corpCode.xml의 corp_eng_name(공식)을 접미사만 다듬어 사용. 영문명이 없으면 한글 그대로 둔다.
- t: 지표·은행·용어 치환 규칙 [[정규식, 영문], ...] — 경제지표 페이지의 한글 표기용(수동 작성).
브라우저에서는 /en-names.js 가 영어 페이지의 한글 텍스트 노드를 이 사전으로 바꿔 보여준다(검색은 종목코드로).
실행: python scripts/build_en_names.py  (DART_API_KEY 필요, 로컬)
"""
import io
import json
import os
import re
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'en_names.json')

# 정규식 규칙(앞에서부터 적용). 긴 표현을 먼저.
TERMS = [
    (r'국고채\((\d+)년\)', r'Korean Treasury (\1-year)'), (r'회사채\(([^,)]+), (\d+)년\)', r'Corporate bond (\1, \2-year)'),
    (r'국고채 (\d+)년', r'Korean Treasury \1-year'), (r'회사채 ([^ ]+) (\d+)년', r'Corporate \1 \2-year'),
    (r'BIS기준 자기자본비율', 'BIS capital ratio'), (r'기본자본비율', 'Tier 1 capital ratio'), (r'보통주자본비율', 'Common equity Tier 1 ratio'),
    (r'부채비율', 'Debt ratio'), (r'(\d{6}) 기준', r'as of \1'), (r'(\d{4}-\d{2}-\d{2}) 기준', r'as of \1'),
    (r'원달러 환율', 'USD/KRW exchange rate'), (r'시중 유동성\(M2, 평잔\)', 'Money supply M2 (average balance)'),
    (r'한국은행 기준금리', 'Bank of Korea policy rate'), (r'가계신용 잔액', 'Household credit outstanding'),
    (r'코스피 200', 'KOSPI 200'), (r'코스피200', 'KOSPI 200'), (r'코스피 지수', 'KOSPI index'), (r'코스닥 지수', 'KOSDAQ index'),
    (r'나스닥 종합지수', 'Nasdaq Composite'), (r'다우존스', 'Dow Jones'), (r'달러 인덱스\(DXY\)', 'US dollar index (DXY)'),
    (r'미국 실업률', 'US unemployment rate'), (r'미국 10년물 국채금리', 'US 10-year Treasury yield'),
    (r'미국 장단기 금리차\(10Y-2Y\)', 'US yield curve (10Y−2Y)'), (r'미국 기준금리', 'US policy rate (Fed)'),
    (r'VIX 공포지수', 'VIX fear index'), (r'미국 소비자물가지수\(CPI\)', 'US CPI'), (r'등유 가격', 'Kerosene price'), (r'경유 가격', 'Diesel price'),
    (r'휘발유 가격', 'Gasoline price'), (r'금 가격 \(국제 금선물 환산\)', 'Gold price (converted from international gold futures)'),
    (r'이더리움', 'Ethereum'), (r'비트코인', 'Bitcoin'), (r'RSI\(14\)', 'RSI(14)'),
    (r'지방은행', 'Regional banks'), (r'인터넷전문은행', 'Internet-only banks'), (r'시중은행', 'Commercial banks'), (r'일반은행', 'General banks'),
    (r'국내은행', 'Domestic banks'), (r'특수은행', 'Specialized banks'),
    (r'한국씨티은행', 'Citibank Korea'), (r'주식회사 카카오뱅크', 'KakaoBank'), (r'주식회사 케이뱅크', 'K Bank'), (r'농협은행주식회사', 'NH Bank'),
    (r'수협은행', 'Suhyup Bank'), (r'우리은행', 'Woori Bank'), (r'한국스탠다드차타드은행', 'SC Bank Korea'), (r'신한은행', 'Shinhan Bank'),
    (r'아이엠뱅크', 'iM Bank'), (r'주식회사 하나은행', 'Hana Bank'), (r'한국수출입은행', 'Export-Import Bank of Korea'), (r'국민은행', 'Kookmin Bank'),
    (r'전북은행', 'Jeonbuk Bank'), (r'광주은행', 'Gwangju Bank'), (r'부산은행', 'Busan Bank'), (r'중소기업은행', 'Industrial Bank of Korea'),
    (r'제주은행', 'Jeju Bank'), (r'한국산업은행', 'Korea Development Bank'), (r'경남은행', 'Kyongnam Bank'),
    (r'코스피', 'KOSPI'), (r'코스닥', 'KOSDAQ'), (r'원/g', 'KRW/g'), (r'원/L', 'KRW/L'), (r'USD/배럴', 'USD/barrel'), (r'WTI 원유가격', 'WTI crude oil price'),
    (r'해외파생', 'Overseas derivative'), (r'거래대금', 'trading value'), (r'\(미국\)', '(US)'),
    (r'\(주\)', ''), (r'주식회사 ', ''),
]

SUFFIX = re.compile(r'[,\s]*(co[.,]*\s*ltd[.,]*|co[.,]*|inc[.,]*|corp(oration)?\.?|company|limited|ltd\.?|holdings?\s*co\.?,?\s*ltd\.?)\s*$', re.I)


def clean(en):
    en = re.sub(r'\s+', ' ', en).strip(' ,')
    for _ in range(3):
        n = SUFFIX.sub('', en).strip(' ,')
        if n == en or not n:
            break
        en = n
    if en.isupper() and len(en) > 4:
        en = en.title()
    return en


def key():
    k = os.environ.get('DART_API_KEY')
    if not k and os.path.exists(os.path.join(ROOT, '.env')):
        for ln in open(os.path.join(ROOT, '.env'), encoding='utf-8'):
            if ln.startswith('DART_API_KEY='):
                k = ln.strip().partition('=')[2]
    return k


def main():
    r = requests.get('https://opendart.fss.or.kr/api/corpCode.xml', params={'crtfc_key': key()}, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    x = z.read(z.namelist()[0]).decode('utf-8')
    names, by_code = {}, {}
    for ko, en, code in re.findall(r'<corp_name>([^<]*)</corp_name>\s*<corp_eng_name>([^<]*)</corp_eng_name>\s*<stock_code>([^<]*)</stock_code>', x):
        if code.strip() and en.strip():
            c = clean(en)
            if c and re.search('[A-Za-z]', c):
                names[ko.strip()] = c
                by_code[code.strip()] = c
    # 페이지에 실제로 쓰이는 표시 이름(KRX 약칭 등)은 종목코드로 연결: 현대차 -> Hyundai Motor
    disp = {}
    for f, pick in [('kr_fin/index.json', lambda d: d['stocks']), ('sim/index.json', lambda d: d)]:
        for row in pick(json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))):
            disp[row[1]] = row[0]
    st = json.load(open(os.path.join(ROOT, 'data', 'stocks.json'), encoding='utf-8'))
    for mk in ('kospi', 'kosdaq'):
        for row in st.get(mk, []):
            disp[row['stock_name']] = row['stock_code']
    for ko, code in disp.items():
        if code in by_code:
            names[ko] = by_code[code]
    json.dump({'n': names, 't': [[a, b] for a, b in TERMS]}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(len(names), os.path.getsize(OUT))
    for k in ['삼성전자', 'SK하이닉스', '현대차', 'KB금융', '셀트리온']:
        print(k, names.get(k))


if __name__ == '__main__':
    main()
