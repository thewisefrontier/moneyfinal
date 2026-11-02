"""
하원 PTR 중 '스캔 이미지로만 공개된 신고서'를 비전 모델(Gemini)로 읽어 data/congress/scan_YYYY.json 에 저장 (로컬 전용).

  python scripts/ptr_scan_ocr.py [연도 ...] [--limit N]

- 대상: data/congress/trades_YYYY.json 의 unparsed 문서. 페이지가 통짜 이미지(TIFF)라 pypdf로 이미지를 꺼내 PNG로 바꿔 보낸다.
- 문서마다 종류(kind)를 판정한다: original(새 신고서) / amendment(정정 서한) / other. original의 행만 거래로 저장하고,
  정정 서한은 기존 신고서와 중복이 되므로 trades에 넣지 않고 docs에 종류만 남긴다.
- 모델이 만든 값은 그대로 믿지 않고 기계 검사를 거친다: 날짜 형식·유효 범위, 거래 유형 집합, 금액은 공식 금액 구간에 맞춰 보정.
  통과한 행에는 ocr=1 표시 -> 화면에 'AI 판독' 배지와 경고를 보여준다.
- 이어서 실행 가능: 이미 처리한 문서(docs)는 건너뜀.
"""
import io
import json
import os
import re
import sys
import time
from datetime import date

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if os.path.exists(os.path.join(ROOT, '.env')):  # Actions에서는 .env 없이 시크릿 환경변수를 씀
    for _l in open(os.path.join(ROOT, '.env'), encoding='utf-8'):
        _l = _l.strip()
        if '=' in _l and not _l.startswith('#'):
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k, _v)
from fetchers.house_ptr import BASE, UA, categorize  # noqa: E402

OUT = os.path.join(ROOT, 'data', 'congress')
MODEL_A = 'gemini-3.8-flash'   # 1차 판독(검증 페이지에서 8/8)
MODEL_B = 'gemini-3.7-flash'   # 2차 판독: A와 일치한 행만 채택
MODEL = MODEL_A
PAGES_PER_CALL = 3
SLEEP = 4
# 하원 PTR 공식 금액 구간 (하한, 상한)
LETTER = {'A': (1001, 15000), 'B': (15001, 50000), 'C': (50001, 100000), 'D': (100001, 250000), 'E': (250001, 500000), 'F': (500001, 1000000),
          'G': (1000001, 5000000), 'H': (5000001, 25000000), 'I': (25000001, 50000000), 'J': (50000001, None), 'K': (1000001, None)}
BRACKETS = [(1001, 15000), (15001, 50000), (50001, 100000), (100001, 250000), (250001, 500000), (500001, 1000000),
            (1000001, 5000000), (5000001, 25000000), (25000001, 50000000), (50000001, None)]
TT = {'purchase': 'buy', 'buy': 'buy', 'p': 'buy', 'sale': 'sell', 'sell': 'sell', 's': 'sell', 'partial_sale': 'sell_partial',
      'sale (partial)': 'sell_partial', 's (partial)': 'sell_partial', 'partial sale': 'sell_partial', 'exchange': 'exchange', 'e': 'exchange'}
OWN = {'self': '', '': '', 'spouse': 'SP', 'sp': 'SP', 'joint': 'JT', 'jt': 'JT', 'child': 'DC', 'dependent child': 'DC', 'dc': 'DC'}
PROMPT = """These are pages of a scanned US House of Representatives Periodic Transaction Report (STOCK Act) or a cover letter with a table of securities transactions.
Return ONLY JSON: {"kind": "original" | "amendment" | "other", "rows": [ ... ]}.
- kind "amendment" if the document amends or corrects a previously filed report (e.g. a letter saying it amends a prior PTR); "original" for a new report; "other" if it contains no transaction table.
- rows: one object per transaction row visible: {"asset": string (security name exactly as written), "ticker": string or null (symbol in parentheses if shown), "asset_type_code": string or null (e.g. ST, ET, OP if shown),
  "owner": "self" | "spouse" | "joint" | "child", "type": "purchase" | "sale" | "partial_sale" | "exchange", "date": "MM/DD/YYYY" (transaction date; years may be 2 digits like 10/19/23 - convert to 4 digits), "notification_date": "MM/DD/YYYY" or null, "amount": string exactly as written (e.g. "$1,001 - $15,000") or null, "amount_box": checked letter A-K or null}.
- Pages may be rotated 90 degrees; read them in the correct orientation.
- Some forms are CHECKBOX grids instead of text: the transaction type is given by which of the Purchase / Sale / Partial Sale / Exchange boxes has an X, and the amount by which lettered row (A-K) has an X. For such forms put the checked letter in "amount_box" (A,B,C,D,E,F,G,H,I,J or K) and leave "amount" null.
  Amount letters: A=$1,001-$15,000, B=$15,001-$50,000, C=$50,001-$100,000, D=$100,001-$250,000, E=$250,001-$500,000, F=$500,001-$1,000,000, G=$1,000,001-$5,000,000, H=$5,000,001-$25,000,000, I=$25,000,001-$50,000,000, J=Over $50,000,000, K=spouse/dependent child asset over $1,000,000.
  Owner column: SP = spouse, DC = dependent child, JT = joint, blank = self.
- Do NOT guess. If a value is illegible use null. Do not invent rows. Include rows only from the tables in these pages."""


def snap_amount(txt):
    """OCR/원문 오타를 공식 구간에 맞춘다. 맞출 수 없으면 (None, None)."""
    if not txt:
        return None, None
    nums = [int(x.replace(',', '')) for x in re.findall(r'\$\s*([\d,]+)', txt)]
    if 'over' in txt.lower() and nums:
        return (nums[0] if nums[0] >= 1000001 else 50000001), None
    if not nums:
        return None, None
    best, bd = None, 1e18
    for lo, hi in BRACKETS:
        for n in nums:
            d = min(abs(n - lo), abs(n - (hi if hi else lo)))
            if d < bd:
                best, bd = (lo, hi), d
    # 원문 숫자와 구간 경계가 너무 멀면(= 완전히 다른 값) 신뢰하지 않는다
    return best if bd <= max(2000, 0.15 * best[0]) else (None, None)


def valid_date(s):
    m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})', (s or '').strip())
    if not m:
        return None
    mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    try:
        dt = date(y, mo, d)
    except ValueError:
        return None
    if not (2012 <= y <= date.today().year + 1):
        return None
    return dt.isoformat()


def page_pngs(pdf_bytes):
    from PIL import Image
    from pypdf import PdfReader
    out = []
    for p in PdfReader(io.BytesIO(pdf_bytes)).pages:
        for im in p.images[:1]:
            try:
                img = Image.open(io.BytesIO(im.data)).convert('L')
            except Exception:  # noqa: BLE001
                continue
            if img.width > 1700:
                img = img.resize((1700, int(img.height * 1700 / img.width)))
            b = io.BytesIO()
            img.save(b, 'PNG', optimize=True)
            out.append(b.getvalue())
    return out


ORIENT_PROMPT = """Each image is one page of a scanned document. For EACH image in order, decide how many degrees it must be rotated COUNTER-CLOCKWISE (0, 90, 180 or 270) so that its text reads upright left-to-right.
Return ONLY JSON: {"pages": [0, 90, ...]} with exactly one number per image, in the same order."""


def upright(client, types, pngs):
    """페이지별 방향을 모델로 판정해 똑바로 돌린 PNG 리스트를 돌려준다(썸네일로 판정해 호출량을 줄임)."""
    from PIL import Image
    thumbs = []
    for b in pngs:
        im = Image.open(io.BytesIO(b))
        im = im.resize((420, int(im.height * 420 / im.width)))
        t = io.BytesIO()
        im.save(t, 'PNG')
        thumbs.append(t.getvalue())
    degs = []
    for i in range(0, len(thumbs), 12):
        res = ask(client, types, thumbs[i:i + 12], model=MODEL_A, prompt=ORIENT_PROMPT) or {}
        part = res.get('pages') or []
        part = [d if d in (0, 90, 180, 270) else 0 for d in part][:len(thumbs[i:i + 12])]
        degs += part + [0] * (len(thumbs[i:i + 12]) - len(part))
    out = []
    for b, d in zip(pngs, degs):
        if d:
            im = Image.open(io.BytesIO(b)).rotate(d, expand=True)
            t = io.BytesIO()
            im.save(t, 'PNG')
            b = t.getvalue()
        out.append(b)
    return out, degs


def ask(client, types, pngs, model=None, prompt=None):
    for attempt in range(2):
        if used_today() >= DAILY_CAP:
            raise StopRun(f'오늘 호출 상한 {DAILY_CAP}회에 도달했습니다. 내일 이어서 실행하세요.')
        try:
            count_call()
            r = client.models.generate_content(
                model=model or MODEL,
                contents=[types.Part.from_bytes(data=b, mime_type='image/png') for b in pngs] + [prompt or PROMPT],
                config=types.GenerateContentConfig(temperature=0, response_mime_type='application/json', max_output_tokens=8192))
            time.sleep(SLEEP)
            out = json.loads(r.text)
            ERR['n'] = 0
            return out
        except StopRun:
            raise
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            print(f'    호출 오류({attempt + 1}/2): {type(e).__name__} {msg[:110]}', flush=True)
            ERR['n'] += 1
            if ERR['n'] >= 8:  # 503·JSON 오류가 이어지면 오늘은 접는다(호출 낭비 방지)
                raise StopRun('오류가 연속으로 이어져 오늘은 중단합니다.')
            if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
                raise StopRun('Gemini 한도(429)에 걸렸습니다. 반복 호출하지 않고 중단합니다.')
            time.sleep(5)
    return None


class StopRun(Exception):
    pass


ERR = {'n': 0}  # 연속 호출 오류 수


USAGE = os.path.join(ROOT, 'data', 'kr_fin_cache', 'gemini_usage.json')  # git 제외 폴더
DAILY_CAP = 40  # 이 스크립트가 하루에 쓰는 Gemini 호출 상한(같은 키를 쓰는 일일 브리핑·AI 요약 몫을 남겨 둠)


def used_today():
    try:
        d = json.load(open(USAGE, encoding='utf-8'))
    except Exception:  # noqa: BLE001
        d = {}
    return d.get(date.today().isoformat(), 0)


def count_call():
    d = {}
    try:
        d = json.load(open(USAGE, encoding='utf-8'))
    except Exception:  # noqa: BLE001
        pass
    k = date.today().isoformat()
    d = {k: d.get(k, 0) + 1}  # 오늘 것만 유지
    os.makedirs(os.path.dirname(USAGE), exist_ok=True)
    json.dump(d, open(USAGE, 'w', encoding='utf-8'))
    return d[k]


def norm_rows(res, info, doc):
    """모델 응답 -> 기계 검사를 통과한 행 리스트, 거절 수"""
    rows, bad = [], 0
    for r in (res or {}).get('rows') or []:
        td = valid_date(r.get('date'))
        tt = TT.get(str(r.get('type') or '').strip().lower())
        box = str(r.get('amount_box') or '').strip().upper()[:1]
        lo, hi = LETTER[box] if box in LETTER else snap_amount(r.get('amount') or '')
        asset = (r.get('asset') or '').strip()
        if not (td and tt and asset and lo):
            bad += 1
            continue
        tk = (r.get('ticker') or '').strip().upper()
        at = (r.get('asset_type_code') or '').strip().upper()[:2]
        rows.append({'own': OWN.get(str(r.get('owner') or '').strip().lower(), ''), 'asset': asset, 'tk': tk, 'at': at, 'cat': categorize(asset, tk, at),
                     'tt': tt, 'td': td, 'nd': valid_date(r.get('notification_date')) or '', 'lo': lo, 'hi': hi,
                     'doc': doc, 'm': info['name'], 'sd': info['sd'], 'f': info['filed'], 'ocr': 1})
    return rows, bad


def key(t):
    """두 모델이 같은 행을 읽었는지 비교하는 키: 종목(영숫자만)·소유자·유형·거래일·금액 구간"""
    return (re.sub(r'[^a-z0-9]', '', (t['tk'] or t['asset']).lower())[:14], t['own'], t['tt'], t['td'], t['lo'])


def agree(a_rows, b_rows):
    """A의 행 중 B에도 같은 키가 있는 것만 남긴다(중복 행은 개수까지 맞춤)."""
    pool = {}
    for t in b_rows:
        pool[key(t)] = pool.get(key(t), 0) + 1
    keep, drop = [], 0
    for t in a_rows:
        k = key(t)
        if pool.get(k, 0) > 0:
            pool[k] -= 1
            keep.append(t)
        else:
            drop += 1
    return keep, drop


def main(years, limit=None, docs_only=None, max_pages=12):
    from fetchers.house_ptr import load_year_index
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    for y in years:
        src = json.load(open(os.path.join(OUT, f'trades_{y}.json'), encoding='utf-8'))
        idx = {d['doc']: d for d in load_year_index(y)}
        path = os.path.join(OUT, f'scan_{y}.json')
        cur = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {'year': y, 'docs': {}, 'trades': []}
        todo = [d for d in src['unparsed'] if d not in cur['docs'] and d in idx and (not docs_only or d in docs_only)]
        todo.sort(key=lambda d: idx[d]['filed'], reverse=True)  # 최신 신고서부터
        if limit:
            todo = todo[:limit]
        print(f'{y}: 스캔 {len(src["unparsed"])}건 중 새로 {len(todo)}건', flush=True)
        for n, doc in enumerate(todo, 1):
            info = idx[doc]
            try:
                pdf = requests.get(f'{BASE}/ptr-pdfs/{y}/{doc}.pdf', headers=UA, timeout=60).content
                pngs = page_pngs(pdf)
                if len(pngs) > max_pages:  # 쪽수가 많은 문서는 호출량이 커서 기본적으로 건너뜀(--max-pages로 조정)
                    cur['docs'][doc] = {'kind': 'skipped_big', 'pages': len(pngs), 'rows': 0}
                    print(f'  [{n}/{len(todo)}] {doc} {info["name"]} p{len(pngs)} -> 쪽수 초과로 건너뜀', flush=True)
                    continue
                pngs, degs = upright(client, types, pngs)
            except StopRun as e:
                print(f'  중단: {e}', flush=True)
                return cur
            except Exception as e:  # noqa: BLE001
                print(f'  {doc} 다운로드/이미지 실패: {type(e).__name__}', flush=True)
                continue
            kind, rows, rej_fmt, rej_agree, failed = None, [], 0, 0, False
            try:
              for i in range(0, len(pngs), PAGES_PER_CALL):
                chunk = pngs[i:i + PAGES_PER_CALL]
                ra = ask(client, types, chunk, model=MODEL_A)
                rb = ask(client, types, chunk, model=MODEL_B)
                if not ra:  # 판독 실패(오류)는 '읽었는데 거래 없음'과 다르므로 완료로 저장하지 않고 다음에 재시도
                    failed = True
                    continue
                ka, kb = ra.get('kind'), (rb or {}).get('kind')
                kind = 'amendment' if 'amendment' in (ka, kb, kind) else (kind or ka)
                a_rows, bad = norm_rows(ra, info, doc)
                b_rows, _ = norm_rows(rb, info, doc)
                keep, drop = agree(a_rows, b_rows) if rb else ([], len(a_rows))
                rows += keep
                rej_fmt += bad
                rej_agree += drop
            except StopRun as e:
                print(f'  중단: {e} (문서 {doc}는 미완료라 저장하지 않음)', flush=True)
                return cur
            if failed:
                tries = cur.setdefault('tries', {})
                tries[doc] = tries.get(doc, 0) + 1
                if tries[doc] < 3:  # 3번 실패하면 포기(원문 링크로만 남김)
                    print(f'  [{n}/{len(todo)}] {doc} {info["name"]} 판독 실패 {tries[doc]}회 -> 다음에 재시도', flush=True)
                    if not limit:
                        json.dump(cur, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
                    continue
                kind = 'failed'
            cur['docs'][doc] = {'kind': kind or 'other', 'pages': len(pngs), 'rot': degs, 'rows': len(rows), 'rejected_format': rej_fmt, 'rejected_disagree': rej_agree}
            if kind == 'original':
                cur['trades'].extend(rows)
            print(f'  [{n}/{len(todo)}] {doc} {info["name"]} p{len(pngs)} rot={degs[:6]} kind={kind} 채택={len(rows)} 형식거절={rej_fmt} 불일치거절={rej_agree}', flush=True)
            if not limit:
                cur['trades'].sort(key=lambda t: (t['td'], t['doc']), reverse=True)
                cur['updated_at'] = date.today().isoformat()
                json.dump(cur, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        if limit or docs_only:
            return cur


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    lim = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    if lim is not None and str(lim) in args:
        args.remove(str(lim))
    yrs = [int(a) for a in args] or [2026, 2025, 2024]
    mp = int(sys.argv[sys.argv.index('--max-pages') + 1]) if '--max-pages' in sys.argv else 12
    if '--max-pages' in sys.argv and str(mp) in args:
        args.remove(str(mp))
    DAILY_CAP = int(sys.argv[sys.argv.index('--max-calls') + 1]) if '--max-calls' in sys.argv else DAILY_CAP
    if '--max-calls' in sys.argv and str(DAILY_CAP) in args:
        args.remove(str(DAILY_CAP))
    r = main(yrs, lim, max_pages=mp)
    if r:
        for t in r['trades'][:12]:
            print(t)
        print(r['docs'])
