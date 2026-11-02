"""
미국 하원 의원 주식·ETF 거래 신고서(PTR, Periodic Transaction Report) 수집기 -> data/congress/trades_YYYY.json

출처: 하원 서기국(Clerk of the House) 재산공개 - 연도별 목록 ZIP(YYYYFD.zip)과 PTR PDF
      https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YYYY}FD.zip
      https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YYYY}/{DocID}.pdf
법적 주의: 5 U.S.C. §13107(c)는 이 신고서를 상업적 목적(언론 매체 예외), 금전 모금, 신용평가에 쓰는 것을 금지한다.
  -> 이 데이터를 쓰는 페이지(congress.html)에는 광고·후원 요청을 넣지 않는다. 상원 eFD는 약관 동의가 필요해 제외.
파싱: PDF는 텍스트 PDF라 pypdf로 글자 위치(x,y)와 글꼴 크기를 받아 표를 복원한다.
  본문 행은 12pt, 부가설명(Filing Status/Subholding/Description 등)은 11.4pt라 크기로 구분한다.
  열 위치(x): 소유자 ~65, 자산 ~104, 거래유형 ~262, 거래일 ~327, 통지일 ~381, 금액 ~446.
스캔 이미지 PDF 등 파싱이 안 되는 신고서는 건너뛰고 unparsed에 기록한다.
"""
import io
import json
import logging
import os
import re
import sys
import time
import zipfile
from datetime import date

import requests

logger = logging.getLogger(__name__)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'congress')
UA = {'User-Agent': 'moneyfinal-research overmandol@gmail.com'}
BASE = 'https://disclosures-clerk.house.gov/public_disc'
YEARS_BACK = 2  # 올해 + 직전 2년

TTYPE = {'P': 'buy', 'S': 'sell', 'S (partial)': 'sell_partial', 'E': 'exchange'}
MONEY = re.compile(r'\$([\d,]+)')


ETF_TICKERS = set("SPY VOO IVV VTI QQQ QQQM DIA IWM IWD IWF IJH IJR VEA VWO VUG VTV VIG VYM VXUS VNQ BND AGG LQD HYG TLT IEF SHY GLD SLV USO XLK XLF XLE XLV XLY XLP XLI XLU XLB XLRE XLC SCHD SCHB SCHG SCHX SCHF JEPI JEPQ SMH SOXX ARKK ARKW TQQQ SQQQ SOXL SPXL UPRO SDS SH EFA EEM VB VO VV MDY RSP SPYD SPYG SPYB SPDW SPLG ITOT IXUS IEMG IBIT FBTC GBTC ETHE".split())
ETF_NAME = re.compile(r"(?<![A-Za-z])(ETFs?|ETN|Exchange[- ]Traded|iShares|SPDR|ProShares|Invesco QQQ)(?![A-Za-z])", re.I)


def categorize(name, tk, at):
    """stock / etf / option / bond / fund / crypto / other. 신고자가 ETF를 [ST]나 [OT]로 적는 경우가 많아 이름·티커로도 판별한다."""
    if at == 'ET' or (tk and tk.upper() in ETF_TICKERS) or ETF_NAME.search(name or ''):
        return 'etf'
    return {'ST': 'stock', 'OP': 'option', 'GS': 'bond', 'CS': 'bond', 'MF': 'fund', 'CT': 'crypto'}.get(at, 'other')


def parse_amount(txt):
    t = txt.replace('\n', ' ').strip()
    nums = [int(x.replace(',', '')) for x in MONEY.findall(t)]
    if t.lower().startswith('over') and nums:
        return nums[0], None
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None, None


def parse_pdf(data):
    """PTR PDF 바이트 -> 거래 행 리스트. 실패하면 빈 리스트."""
    from pypdf import PdfReader
    rows = []
    reader = PdfReader(io.BytesIO(data))
    for page in reader.pages:
        chunks = []

        def visit(text, cm, tm, font, size):
            t = (text or '').replace('\x00', '').strip()
            if t and 11.8 <= (size or 0) <= 12.3:  # 본문 행만(헤더 12.6, 부가설명 11.4 제외)
                chunks.append((tm[5] * cm[3] + cm[5], tm[4] * cm[0] + cm[4], t))

        try:
            page.extract_text(visitor_text=visit)
        except Exception:  # noqa: BLE001
            continue
        # 거래 유형 칸(x 255~320)에 P/S/E가 있는 y를 행 기준선으로 삼는다
        anchors = sorted({round(y, 1) for y, x, t in chunks if 255 <= x < 320 and re.fullmatch(r'(P|S|E|S \(partial\))', t)}, reverse=True)
        if not anchors:
            continue
        recs = {a: {'asset': [], 'owner': '', 'tt': '', 'td': '', 'nd': '', 'amt': []} for a in anchors}
        for y, x, t in sorted(chunks, key=lambda c: (-c[0], c[1])):
            # 이 칸이 속한 행: 자기 y 이상(위쪽)에 있는 가장 가까운 기준선
            above = [a for a in anchors if a >= y - 1.5]
            if not above:
                continue
            a = min(above, key=lambda v: v - y)
            r = recs[a]
            if 95 <= x < 255:
                r['asset'].append(t)
            elif 55 <= x < 95 and t in ('SP', 'JT', 'DC'):
                r['owner'] = t
            elif 255 <= x < 320 and not r['tt']:
                r['tt'] = t
            elif 320 <= x < 375 and re.fullmatch(r'\d{2}/\d{2}/\d{4}', t):
                r['td'] = t
            elif 375 <= x < 440 and re.fullmatch(r'\d{2}/\d{2}/\d{4}', t):
                r['nd'] = t
            elif 440 <= x < 525:
                r['amt'].append(t)
        for a in anchors:
            r = recs[a]
            asset = ' '.join(r['asset']).strip()
            mt = re.search(r'\[[A-Z]{2}\]', asset)
            if mt:  # 쪽 하단 문구("Hon. 이름 , 날짜", Filing ID 등)가 뒤에 붙는 경우 잘라낸다
                asset = asset[:mt.end()]
            asset = re.sub(r'\s*Filing ID #\d+.*$', '', asset)
            m_t = re.findall(r'\(([A-Za-z0-9][A-Za-z0-9.\-/ ]{0,9})\)', asset)
            m_c = re.findall(r'\[([A-Z]{2})\]', asset)
            if not (asset and r['td'] and r['tt'] in TTYPE):
                continue
            lo, hi = parse_amount(' '.join(r['amt']))
            name = re.sub(r'\s*\([A-Za-z0-9][A-Za-z0-9.\-/ ]{0,9}\)\s*\[[A-Z]{2}\]\s*$', '', asset)
            name = re.sub(r'\s*\[[A-Z]{2}\]\s*$', '', name).strip()
            tk_ = m_t[-1].strip() if m_t else ''
            at_ = m_c[-1] if m_c else ''
            rows.append({
                'own': r['owner'], 'asset': name, 'tk': tk_, 'at': at_, 'cat': categorize(name, tk_, at_),
                'tt': TTYPE[r['tt']], 'td': r['td'], 'nd': r['nd'], 'lo': lo, 'hi': hi,
            })
    return rows


def iso(d):
    m, dd, y = d.split('/')
    return f'{y}-{int(m):02d}-{int(dd):02d}'


def load_year_index(year):
    r = requests.get(f'{BASE}/financial-pdfs/{year}FD.zip', headers=UA, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml = z.read(f'{year}FD.xml').decode('utf-8', 'ignore')
    out = []
    for m in re.findall(r'<Member>(.*?)</Member>', xml, re.S):
        def g(tag):
            mm = re.search(rf'<{tag}>(.*?)</{tag}>', m, re.S)
            return (mm.group(1).strip() if mm else '')
        if g('FilingType') != 'P':
            continue
        name = ' '.join(x for x in (g('First'), g('Last'), g('Suffix')) if x)
        out.append({'doc': g('DocID'), 'name': name, 'sd': g('StateDst'), 'filed': iso(g('FilingDate')) if g('FilingDate') else ''})
    return out


def main(years=None, limit=None):
    os.makedirs(OUT, exist_ok=True)
    this = date.today().year
    years = years or list(range(this - YEARS_BACK, this + 1))
    summary = {}
    for y in years:
        path = os.path.join(OUT, f'trades_{y}.json')
        cur = {'year': y, 'docs': {}, 'trades': [], 'unparsed': []}
        if os.path.exists(path):
            cur = json.load(open(path, encoding='utf-8'))
        known = set(cur['docs']) | set(cur['unparsed'])
        try:
            idx = load_year_index(y)
        except Exception as e:  # noqa: BLE001
            logger.warning(f'{y} 목록 실패: {e}')
            continue
        todo = [d for d in idx if d['doc'] not in known]
        if limit:
            todo = todo[:limit]
        logger.info(f'{y}: 신고서 {len(idx)}건 중 새로 {len(todo)}건')
        for n, d in enumerate(todo, 1):
            try:
                r = requests.get(f"{BASE}/ptr-pdfs/{y}/{d['doc']}.pdf", headers=UA, timeout=60)
                rows = parse_pdf(r.content) if r.status_code == 200 else []
            except Exception as e:  # noqa: BLE001
                logger.warning(f"{d['doc']} 실패: {type(e).__name__}")
                rows = []
            if rows:
                cur['docs'][d['doc']] = {'m': d['name'], 'sd': d['sd'], 'f': d['filed']}
                for t in rows:
                    t.update({'doc': d['doc'], 'm': d['name'], 'sd': d['sd'], 'f': d['filed'], 'td': iso(t['td']), 'nd': iso(t['nd']) if t['nd'] else ''})
                    if t['td'] > (t['nd'] or t['f'] or '9999'):  # 거래일이 통지일·신고일보다 늦음 = 원문 오기 가능. 값은 그대로 두고 표시만 한다
                        t['fx'] = 1
                    cur['trades'].append(t)
            else:
                cur['unparsed'].append(d['doc'])
                cur.setdefault('scans', {})[d['doc']] = {'m': d['name'], 'sd': d['sd'], 'f': d['filed']}  # 스캔 이미지라 못 읽은 신고서: 목록·원문 링크로만 제공
            if n % 50 == 0:
                logger.info(f'  {n}/{len(todo)}')
            time.sleep(0.25)
        cur['trades'].sort(key=lambda t: (t['td'], t['doc']), reverse=True)
        cur['updated_at'] = date.today().isoformat()
        if not limit:
            json.dump(cur, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        summary[y] = (len(cur['docs']), len(cur['trades']), len(cur['unparsed']))
        logger.info(f'{y}: 파싱 {len(cur["docs"])}건, 거래 {len(cur["trades"])}행, 미파싱 {len(cur["unparsed"])}건')
    if not limit:
        meta = {'updated_at': date.today().isoformat(), 'years': years,
                'counts': {str(k): {'filings': v[0], 'trades': v[1], 'unparsed': v[2]} for k, v in summary.items()}}
        json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return cur


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    main()
