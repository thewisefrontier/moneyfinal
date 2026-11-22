"""번역 TSV 검사. 사용: python scripts/check_fortune_tsv.py <원문 TSV> <번역 TSV>
규칙: 모든 번호가 있고, ${...} 자리표시자가 원문과 같고, 직선 따옴표(' " `)가 없고, 한글이 남지 않았고, 비어 있지 않다."""
import re
import sys

H = re.compile(r'[가-힣]')
PH = re.compile(r'\$\{[^{}]*\}')


def read(p):
    d = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip():
            continue
        if '\t' in ln and ln.split('\t', 1)[0].isdigit():
            i, t = ln.split('\t', 1)
            d[int(i)] = t
        elif d:  # 원문에 줄바꿈이 섞인 경우 앞 항목에 이어 붙임
            k = max(d)
            d[k] += '\n' + ln
    return d


def main(src, out):
    s, o = read(src), read(out)
    bad = []
    for i, ko in s.items():
        en = o.get(i)
        if en is None or not en.strip():
            bad.append((i, '번역 없음'))
            continue
        if sorted(PH.findall(ko)) != sorted(PH.findall(en)):
            bad.append((i, f'자리표시자 불일치 {PH.findall(ko)} -> {PH.findall(en)}'))
        t = PH.sub('', en)
        if re.search(r'[\'"`]', t):
            bad.append((i, '직선 따옴표 사용(’ “ ” 로 바꾸세요)'))
        if H.search(PH.sub('', en)):
            bad.append((i, '한글이 남음'))
    extra = sorted(set(o) - set(s))
    for i, why in bad[:60]:
        print(f'[{i}] {why} | {s[i][:50]}')
    if extra:
        print('원문에 없는 번호:', extra[:20])
    print(f'원문 {len(s)}개, 번역 {len(o)}개, 문제 {len(bad)}건')
    return 1 if bad or extra else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
