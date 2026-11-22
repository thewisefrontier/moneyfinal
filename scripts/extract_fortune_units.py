"""핫딜월드 운세 계산 코드(TS)에서 한글이 든 문자열 리터럴만 뽑아 번역 대상 목록을 만든다.
출력: i18n/fortune_src/{A_daily_period,B_saju,C_tarot}.txt (번호<TAB>원문). 영어 사전 검사(build_fortune_en.py)도 같은 함수를 쓴다."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'D:/thewise/hotdealworld/apps/web/lib/'
H = re.compile(r'[가-힣]')
LIT = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`', re.S)
GROUPS = {'A_daily_period': ['dailyFortune', 'periodFortune'], 'B_saju': ['saju'], 'C_tarot': ['tarot']}


def strip(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'(?m)(?<![:\'"`\w])//[^\n]*', '', s)


def units(files):
    seen, S = [], set()
    for f in files:
        s = strip(open(BASE + f + '.ts', encoding='utf-8').read())
        for m in LIT.finditer(s):
            u = next(x for x in m.groups() if x is not None)
            if H.search(u) and u not in S:
                S.add(u)
                seen.append(u)
    return seen


if __name__ == '__main__':
    out = os.path.join(ROOT, 'i18n', 'fortune_src')
    os.makedirs(out, exist_ok=True)
    for g, fs in GROUPS.items():
        us = units(fs)
        with open(os.path.join(out, g + '.txt'), 'w', encoding='utf-8', newline='') as o:
            for i, u in enumerate(us):
                o.write(f'{i}\t{u}\n')
        print(g, len(us), sum(len(u) for u in us), 'placeholders', sum('${' in u for u in us))
