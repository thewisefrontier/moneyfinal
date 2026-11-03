"""영어판(/en/) 빌더 — 한국어 원본 HTML을 읽어 번역 사전(i18n/en.json)으로 문구 단위 치환 후 en/ 에 쓴다.

사용:
  python scripts/build_en.py            # 빌드 (번역 안 된 문구가 있으면 목록을 i18n/en_todo.json 에 쓰고 실패)
  python scripts/build_en.py --todo     # 번역할 문구만 뽑아 i18n/en_todo.json 에 쓴다
번역 단위: 따옴표·태그·세미콜론 등으로 끊기는 '한글이 든 문구'. 인라인 태그(<b>, <span> 등)와 ${...}는 문구 안에 그대로 두며,
번역문도 같은 태그·${} 개수를 유지해야 한다(검사함). 번역문에는 직선 따옴표(' " `)를 쓰지 않는다(JS 문자열이 깨지므로 ’ “ ” 사용).
페이지별 코드 수정(통화 표기 등)은 i18n/en_patches.json: {"페이지.html": [["원본","교체"], ...], "*": [...]}.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N = os.path.join(ROOT, 'i18n')
SITE = 'https://moneyfinal.pages.dev'
HANGUL = re.compile(r'[가-힣]')

# 영어판에 싣는 페이지. 한국 예금·대출·연금저축·ISA·보험·AI 브리핑은 제외.
CORE = ['dividend-etf.html', 'us-fin.html', 'kr-fin.html', 'compare.html', 'superinvestor.html', 'congress.html', 'ipo.html',
        'market.html', 'macro.html', 'macro-detail.html', 'indicator-detail.html', 'stock-detail.html', 'company.html', 'bond.html',
        'crypto.html', 'sim.html', 'about.html', 'privacy.html', 'terms.html', '404.html',
        'calc.html', 'calc-age.html', 'calc-date.html', 'calc-dividend.html', 'calc-fire-dividend.html', 'calc-fire.html',
        'calc-freelancer.html', 'calc-fx.html', 'calc-loan.html', 'calc-lotto-sim.html', 'calc-lotto-tax.html', 'calc-pyeong.html',
        'calc-realty.html', 'calc-salary.html']


NAME_PAGES = {'market.html', 'macro.html', 'macro-detail.html', 'indicator-detail.html', 'stock-detail.html', 'company.html', 'kr-fin.html',
              'sim.html', 'compare.html', 'calc-fire-dividend.html', 'ipo.html'}


def en_pages():
    extra = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'dividend-*.html'))
             if os.path.basename(p) != 'dividend-etf.html']
    return CORE + sorted(extra)


INLINE = r'</?(?:b|strong|i|em|small|span|a|br|code|u|sup|sub|mark)(?:\s[^<>]*)?/?>'
TOKEN = re.compile(r'(?P<tag>' + INLINE + r')|(?P<ph>\$\{)|(?P<stop>[\'"`<>;{}=])|(?P<txt>[^\'"`<>;{}=$]+|\$)')


def strip_comments(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'/\*.*?\*/', lambda m: '' if HANGUL.search(m.group(0)) else m.group(0), s, flags=re.S)
    # 한글이 든 // 주석(URL의 :// 제외)
    s = re.sub(r'(?m)(?<![:\'"`\w])//[^\n]*', lambda m: '' if HANGUL.search(m.group(0)) else m.group(0), s)
    return s


def balanced(s, i):
    """s[i:]가 '${' 로 시작할 때 닫는 '}' 다음 위치."""
    d, j = 0, i + 1
    while j < len(s):
        if s[j] == '{':
            d += 1
        elif s[j] == '}':
            d -= 1
            if d == 0:
                return j + 1
        j += 1
    return len(s)


def scan(s):
    """한글이 든 번역 단위의 (start, end) 목록."""
    spans, i, run_start, has_h = [], 0, None, False

    def flush(end):
        nonlocal run_start, has_h
        if run_start is not None and has_h:
            a, b = run_start, end
            while a < b and s[a].isspace():
                a += 1
            while b > a and s[b - 1].isspace():
                b -= 1
            if a < b:
                spans.append((a, b))
        run_start, has_h = None, False

    while i < len(s):
        m = TOKEN.match(s, i)
        if not m:
            flush(i)
            i += 1
            continue
        k = m.lastgroup
        if k == 'ph':
            j = balanced(s, i)
            if HANGUL.search(s[i:j]):  # 식 안에 한글 문자열이 있으면 경계로 보고 안쪽을 따로 스캔
                flush(i)
                i += 2
                continue
            if run_start is None:
                run_start = i
            i = j
            continue
        if k == 'stop':
            flush(i)
            i = m.end()
            continue
        if run_start is None:
            run_start = i
        if k == 'txt' and HANGUL.search(m.group(0)):
            has_h = True
        if k == 'tag' and HANGUL.search(m.group(0)):
            has_h = True
        i = m.end()
    flush(len(s))
    return spans


def by_rule(u, rules):
    for rx, v in rules:
        m = rx.fullmatch(u)
        if m:
            return m.expand(v)
    return None


_PROT = re.compile(r"""(?:===?|!==?)\s*'([^']*[가-힣][^']*)'|'([^']*[가-힣][^']*)'\s*(?:===?|!==?)|\.includes\('([^']*[가-힣][^']*)'\)|\{\s*'([^']*[가-힣][^']*)'\s*:|,\s*'([^']*[가-힣][^']*)'\s*:\s*[\d.e]""")


def protected(s):
    """코드에서 데이터 값과 비교하거나 키로 쓰는 한글 문자열(예: unit==='원')은 번역하면 로직이 깨지므로 원문 유지."""
    out = set()
    for m in _PROT.finditer(s):
        out.add(next(g for g in m.groups() if g))
    for m in re.finditer(r"""\[((?:'[^']*',?\s*)+)\]\.includes""", s):
        out.update(x for x in re.findall(r"'([^']*)'", m.group(1)) if HANGUL.search(x))
    return out


def sig(u):
    return (sorted(re.findall(r'\$\{[^{}]*\}', u)), sorted(re.findall(r'</?(\w+)', ''.join(re.findall(INLINE, u)))))


def load(name, default):
    p = os.path.join(I18N, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def load_dict():
    """i18n/en.json(정규식 규칙) + i18n/en*.txt(문구 번역). txt 형식: 원문 / --->  / 번역 블록을 ==== 줄로 구분."""
    dic = load('en.json', {})
    sep, arrow = '\n====\n', '\n--->\n'
    for p in sorted(glob.glob(os.path.join(I18N, 'en*.txt'))):
        for blk in open(p, encoding='utf-8').read().replace('\r\n', '\n').split(sep):
            if arrow in blk:
                ko, en = blk.strip('\n').split(arrow, 1)
                dic[ko.strip()] = en.strip().replace('⎵', ' ')
    return dic


def load_patches():
    ns = {}
    p = os.path.join(I18N, 'en_patches.py')
    if os.path.exists(p):
        exec(open(p, encoding='utf-8').read(), ns)
    return ns.get('PATCHES', {})


def patches_for(patches, name):
    import fnmatch
    out = []
    for k, v in patches.items():
        if k == '*' or fnmatch.fnmatch(name, k):
            out += [(o, n, k == name) for o, n in v]  # 세 번째 값: 이 페이지 이름으로 직접 지정된 패치인가(미적용 경고 대상)
    return out


def main(todo_only=False):
    dic, patches = load_dict(), load_patches()
    rules = [(re.compile(k[3:], re.S), v) for k, v in dic.items() if k.startswith('re:')]  # ETF 페이지처럼 티커만 다른 문구용 정규식 규칙
    pages = en_pages()
    todo, bad, out = {}, [], {}
    for name in pages:
        s = open(os.path.join(ROOT, name), encoding='utf-8').read()
        for old, new, exact in patches_for(patches, name):
            if old.startswith('re:'):
                s, k = re.subn(old[3:], lambda m, n=new: n, s, flags=re.S)
                if not k and exact:
                    bad.append(f'[패치 미적용] {name}: {old[:50]}')
                continue
            if old not in s and exact:
                bad.append(f'[패치 미적용] {name}: {old[:50]}')
            s = s.replace(old, new)
        s = strip_comments(s)
        spans = scan(s)
        prot = protected(s)
        parts, last = [], 0
        for a, b in spans:
            u = s[a:b]
            parts.append(s[last:a])
            if u in prot:  # 데이터 키: 번역하지 않고 그대로
                parts.append(u)
                last = b
                continue
            t = dic.get(name + '::' + u) or dic.get(u) or by_rule(u, rules)
            if t is None:
                todo.setdefault(u, []).append(name)
                t = u
            else:
                if sig(t) != sig(u):
                    bad.append(f'[태그/${{}} 불일치] {u[:60]} -> {t[:60]}')
                if re.search(r'[\'"`]', re.sub(INLINE, '', t)) and not re.search(r'[\'"`]', re.sub(INLINE, '', u)):
                    bad.append(f'[직선 따옴표] {t[:70]}')
            parts.append(t)
            last = b
        parts.append(s[last:])
        out[name] = ''.join(parts)
    if todo:
        json.dump({k: '' for k in todo}, open(os.path.join(I18N, 'en_todo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'번역 필요 문구 {len(todo)}개 -> i18n/en_todo.json')
    for b in bad:
        print(b)
    if todo_only or todo or bad:
        return 1 if (todo or bad) else 0
    os.makedirs(os.path.join(ROOT, 'en'), exist_ok=True)
    enset = set(pages)
    for name, s in out.items():
        open(os.path.join(ROOT, 'en', name), 'w', encoding='utf-8').write(localize(name, s, enset))
    home = os.path.join(I18N, 'en_index.html')
    if os.path.exists(home):  # 영어 홈은 손으로 쓴 파일을 그대로 복사
        open(os.path.join(ROOT, 'en', 'index.html'), 'w', encoding='utf-8', newline='').write(open(home, encoding='utf-8', newline='').read())
    add_ko_hreflang(pages + ['index.html'])
    print(f'{len(out)}개 페이지 생성 -> en/')
    return 0


def localize(name, s, enset):
    page = name[:-5]
    s = s.replace('<html lang="ko"', '<html lang="en"').replace('ko_KR', 'en_US').replace('"inLanguage":"ko"', '"inLanguage":"en"')
    s = s.replace("'ko-KR'", "'en-US'")
    s = re.sub(r'(rel="canonical" href=")' + re.escape(SITE) + r'/?([^"]*)"', lambda m: f'{m.group(1)}{SITE}/en/{m.group(2)}"', s)
    s = re.sub(r'(property="og:url" content=")' + re.escape(SITE) + r'/?([^"]*)"', lambda m: f'{m.group(1)}{SITE}/en/{m.group(2)}"', s)
    s = re.sub(r'("url":")' + re.escape(SITE) + r'/?([^"]*)"', lambda m: f'{m.group(1)}{SITE}/en/{m.group(2)}"', s)
    # 상대 경로 -> 루트 기준. 영어판에 있는 페이지는 /en/, 없는 페이지와 정적 자원은 루트.

    def page_href(m):
        q, nm, rest = m.group(1), m.group(2), m.group(3)
        pre = '/en/' if nm + '.html' in enset else '/'
        return f'{q}{pre}{nm}{".html" if nm + ".html" in enset else ""}{rest}'
    s = re.sub(r'((?:href|src)=")(?!https?:|//|/|#|mailto:|data:|javascript:|\$\{)([^"#?]+)(")',
               lambda m: m.group(1) + ('/en/' if m.group(2) in enset else '/') + m.group(2) + m.group(3), s)
    s = re.sub(r'((?:href|src)=")(?!https?:|//|/|#|mailto:|data:|javascript:|\$\{)([^"#?]+)([?#][^"]*")',
               lambda m: m.group(1) + ('/en/' if m.group(2) in enset else '/') + m.group(2) + m.group(3), s)
    s = re.sub(r'([\'"`])((?:data|notes)/)', r'\1/\2', s)
    s = re.sub(r'(?<!data-active=)([\'"`])([\w\-]+\.html)(?=[?#\'"`])', lambda m: m.group(1) + ('/en/' if m.group(2) in enset else '/') + m.group(2), s)
    if name in NAME_PAGES:  # 한글 데이터(기업명·지표명)를 영어로 바꿔 주는 런타임 사전
        s = s.replace('</body>', '<script src="/en-names.js"></script>\n</body>', 1)
    s = s.replace('href="/index.html"', 'href="/en/"').replace('href="/en/index.html"', 'href="/en/"')
    # 검색엔진용 언어 대응 링크
    alt = (f'<link rel="alternate" hreflang="en" href="{SITE}/en/{page}">\n<link rel="alternate" hreflang="ko" href="{SITE}/{page}">\n'
           f'<link rel="alternate" hreflang="x-default" href="{SITE}/{page}">\n')
    s = re.sub(r'(<link rel="canonical"[^>]*>\n?)', lambda m: m.group(1) + alt, s, count=1)
    return s


def add_ko_hreflang(names):
    """한국어 원본에 영어판 대응 링크를 한 번만 넣는다(이미 있으면 건너뜀)."""
    for name in names:
        p = os.path.join(ROOT, name)
        s = open(p, encoding='utf-8', newline='').read()
        if 'hreflang="en"' in s:
            continue
        page = '' if name == 'index.html' else name[:-5]
        alt = (f'<link rel="alternate" hreflang="ko" href="{SITE}/{page}">\n<link rel="alternate" hreflang="en" href="{SITE}/en/{page}">\n'
               f'<link rel="alternate" hreflang="x-default" href="{SITE}/{page}">\n')
        n = re.sub(r'(<link rel="canonical"[^>]*>\n?)', lambda m: m.group(1) + alt, s, count=1)
        if n != s:
            open(p, 'w', encoding='utf-8', newline='').write(n)


if __name__ == '__main__':
    sys.exit(main('--todo' in sys.argv))
