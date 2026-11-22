"""영어 운세 표시 계층(fortune-en.js) 생성기.

입력: i18n/fortune_src/*.txt(원문, extract_fortune_units.py) + i18n/fortune_en_{A,B,C}.txt(번역, 번호<TAB>영어).
출력: fortune-en.js — window.FZ_EN = {D: {한국어 원문: 영어}, ...용어 표...} 와 window.FZ.T(문구) 변환 함수.
영어 페이지에서만 불러온다. 계산 로직은 한국어 그대로 두고, 화면에 보여 줄 때만 이 사전으로 바꾼다.
사용: python scripts/build_fortune_en.py [--check]  (--check: 파일을 쓰지 않고 누락만 점검)"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_fortune_units as ex  # noqa: E402

ROOT = ex.ROOT
H = re.compile(r'[가-힣]')


def read_tsv(p):
    d = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln and ln.split('\t', 1)[0].isdigit():
            i, t = ln.split('\t', 1)
            d[int(i)] = t
    return d


def load_dict():
    D, missing = {}, []
    for g, tag in (('A_daily_period', 'A'), ('B_saju', 'B'), ('C_tarot', 'C')):
        src = ex.units(ex.GROUPS[g])
        p = os.path.join(ROOT, 'i18n', f'fortune_en_{tag}.txt')
        tr = read_tsv(p) if os.path.exists(p) else {}
        for i, ko in enumerate(src):
            en = tr.get(i)
            if en and en.strip():
                D[ko] = en.strip()
            else:
                missing.append((g, i, ko))
    return D, missing


# 사주 용어: 한자 + 로마자 + 영어. 계산 결과의 키(한글 천간·지지·십신)를 화면용 이름으로 바꾼다.
STEMS = {'갑': ('Gap', 'Wood', 'Yang'), '을': ('Eul', 'Wood', 'Yin'), '병': ('Byeong', 'Fire', 'Yang'), '정': ('Jeong', 'Fire', 'Yin'),
         '무': ('Mu', 'Earth', 'Yang'), '기': ('Gi', 'Earth', 'Yin'), '경': ('Gyeong', 'Metal', 'Yang'), '신': ('Sin', 'Metal', 'Yin'),
         '임': ('Im', 'Water', 'Yang'), '계': ('Gye', 'Water', 'Yin')}
BRANCHES = {'자': ('Ja', 'Rat', 'Water'), '축': ('Chuk', 'Ox', 'Earth'), '인': ('In', 'Tiger', 'Wood'), '묘': ('Myo', 'Rabbit', 'Wood'),
            '진': ('Jin', 'Dragon', 'Earth'), '사': ('Sa', 'Snake', 'Fire'), '오': ('O', 'Horse', 'Fire'), '미': ('Mi', 'Sheep', 'Earth'),
            '신': ('Sin', 'Monkey', 'Metal'), '유': ('Yu', 'Rooster', 'Metal'), '술': ('Sul', 'Dog', 'Earth'), '해': ('Hae', 'Pig', 'Water')}
ELEMENTS = {'목': 'Wood', '화': 'Fire', '토': 'Earth', '금': 'Metal', '수': 'Water'}
TEN_GODS = {'비견': 'Peer', '겁재': 'Rival', '식신': 'Expression', '상관': 'Creativity', '편재': 'Fluid Wealth', '정재': 'Steady Wealth',
            '편관': 'Pressure', '정관': 'Authority', '편인': 'Insight', '정인': 'Support', '일간': 'Self'}
ZODIAC = {'쥐띠': 'Rat', '소띠': 'Ox', '호랑이띠': 'Tiger', '토끼띠': 'Rabbit', '용띠': 'Dragon', '뱀띠': 'Snake', '말띠': 'Horse', '양띠': 'Sheep',
          '원숭이띠': 'Monkey', '닭띠': 'Rooster', '개띠': 'Dog', '돼지띠': 'Pig'}

# 라이브러리 안에서 `${...}` 식 안쪽에 따옴표로 들어 있어 번역 단위로 뽑히지 않는 값들
EXTRA = {'순행': 'forward', '역행': 'backward', '월요일': 'Monday', '화요일': 'Tuesday', '수요일': 'Wednesday', '목요일': 'Thursday', '금요일': 'Friday', '토요일': 'Saturday', '일요일': 'Sunday'}


PH_RE = re.compile(r'\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')


def templates(D):
    """`${...}`가 든 한국어 문구는 정규식으로, 영어 문구는 자리표시자를 캡처 그룹 번역으로 채우는 템플릿으로 만든다.
    공백 하나로만 이어진 자리표시자(`${A} ${B}`)는 경계를 알 수 없어 하나의 그룹으로 묶고, 그룹 번역은 문장 단위로 한다."""
    out = []
    for ko, en in D.items():
        ms = list(PH_RE.finditer(ko))
        if not ms:
            continue
        pat, last, g, ph = '', 0, -1, []
        for k, m in enumerate(ms):
            lit = ko[last:m.start()]
            if k > 0 and lit == ' ':
                ph.append([m.group(0), -1])      # 앞 그룹에 합쳐짐: 영어에서는 빈 문자열
            else:
                pat += re.escape(lit) + '(.+?)'
                g += 1
                ph.append([m.group(0), g])
            last = m.end()
        pat += re.escape(ko[last:])
        out.append({'re': '^' + pat + '$', 'en': en, 'ph': ph})
    return out


def build(D):
    D = dict(D)
    D.update(EXTRA)
    data = {'D': D, 'tpl': templates(D), 'stems': STEMS, 'branches': BRANCHES, 'elements': ELEMENTS, 'tenGods': TEN_GODS, 'zodiac': ZODIAC}
    tpl = open(os.path.join(ROOT, 'scripts', 'fortune_en_runtime.js'), encoding='utf-8').read()
    js = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    open(os.path.join(ROOT, 'fortune-en.js'), 'w', encoding='utf-8', newline='').write(js)
    return len(js)


if __name__ == '__main__':
    D, missing = load_dict()
    print(f'사전 {len(D)}개, 번역 누락 {len(missing)}개')
    for g, i, ko in missing[:10]:
        print(f'  [{g} {i}] {ko[:50]}')
    if '--check' not in sys.argv:
        print('fortune-en.js', build(D), 'bytes')
    sys.exit(1 if missing else 0)
