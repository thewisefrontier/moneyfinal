#!/usr/bin/env python3
"""
시크릿/환경변수 감사 도구.

레포를 스캔해서 다음 3가지를 대조한다.
  1. 워크플로우가 주입하는 매핑        : secrets.X -> env var Y
  2. 파이썬 코드가 읽는 환경변수        : os.environ[...] / os.getenv(...)
  3. 불일치 (고아 시크릿 / 누락 주입)

산출물: docs/SECRETS.md  (수기 관리 금지 — 이 스크립트가 유일한 생성자)
사용법:
  python scripts/audit_secrets.py          # docs/SECRETS.md 갱신
  python scripts/audit_secrets.py --check  # 갱신 필요하면 exit 1 (CI용)
"""
import os
import re
import sys
from collections import defaultdict

# Windows 콘솔 기본 인코딩(cp949)이 이모지(⚠️)를 못 그려서 print()가 죽는 것 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF_DIR = os.path.join(ROOT, '.github', 'workflows')
CODE_DIRS = ['fetchers', 'processors', 'exporters', 'utils', 'scripts']
OUT = os.path.join(ROOT, 'docs', 'SECRETS.md')

# env_var: secrets.SECRET_NAME  형태를 잡는다
RE_INJECT = re.compile(
    r'^\s*([A-Z][A-Z0-9_]*)\s*:\s*\$\{\{\s*secrets\.([A-Z][A-Z0-9_]*)\s*\}\}',
    re.MULTILINE,
)
# 워크플로우가 실행하는 스크립트 경로
RE_SCRIPT = re.compile(r'(?:fetchers|processors|exporters|utils|scripts)/[a-z0-9_]+\.py')
# 코드가 읽는 환경변수
RE_IMPORT = re.compile(r'^\s*(?:from\s+([a-z_][a-z0-9_.]*)\s+import|import\s+([a-z_][a-z0-9_.]*))', re.MULTILINE)
RE_READ = re.compile(
    r'os\.environ\.get\(\s*[\'"]([A-Z][A-Z0-9_]*)[\'"]'
    r'|os\.environ\[\s*[\'"]([A-Z][A-Z0-9_]*)[\'"]\s*\]'
    r'|os\.getenv\(\s*[\'"]([A-Z][A-Z0-9_]*)[\'"]'
)


def scan_workflows():
    """{env_var: {secret_names}}, {workflow: {env_vars}}, {workflow: [scripts]}"""
    mapping = defaultdict(set)
    wf_env = defaultdict(set)
    wf_scripts = defaultdict(list)
    if not os.path.isdir(WF_DIR):
        return mapping, wf_env, wf_scripts
    for fn in sorted(os.listdir(WF_DIR)):
        if not fn.endswith(('.yml', '.yaml')):
            continue
        raw = open(os.path.join(WF_DIR, fn), encoding='utf-8').read()
        # 주석 처리(전체 줄이 '#'로 시작)된 스텝은 의도적으로 비활성화된 것이라
        # 스캔 대상에서 제외한다 (안 그러면 run: 줄만 주석 밖에 남았을 때
        # "env 주입 누락" 오탐이 남 - 2026-09-04 data.go.kr 스텝들 주석 처리하며 발견).
        text = '\n'.join(line for line in raw.splitlines() if not line.strip().startswith('#'))
        for env_var, secret in RE_INJECT.findall(text):
            mapping[env_var].add(secret)
            wf_env[fn].add(env_var)
        seen = []
        for s in RE_SCRIPT.findall(text):
            if s not in seen:
                seen.append(s)
        wf_scripts[fn] = seen
    return mapping, wf_env, wf_scripts


def scan_code():
    """({env_var: [paths]}, {path: {env_vars}}, {path: {imported paths}})"""
    reads = defaultdict(list)
    by_file = defaultdict(set)
    imports = defaultdict(set)
    for d in CODE_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for fn in sorted(os.listdir(full)):
            if not fn.endswith('.py'):
                continue
            rel = f'{d}/{fn}'
            text = open(os.path.join(full, fn), encoding='utf-8').read()
            for a, b in RE_IMPORT.findall(text):
                mod = (a or b).replace('.', '/')
                for cand in (f'{mod}.py', f'{mod}/__init__.py'):
                    if os.path.exists(os.path.join(ROOT, cand)):
                        imports[rel].add(f'{mod}.py')
                        break
            for groups in RE_READ.findall(text):
                var = next(g for g in groups if g)
                if var in ('PATH', 'HOME', 'PWD', 'GITHUB_ACTIONS', 'CI'):
                    continue
                if rel not in reads[var]:
                    reads[var].append(rel)
                by_file[rel].add(var)
    return reads, by_file, imports


def required_env(path, by_file, imports, _seen=None):
    """스크립트 하나가 (import 포함) 필요로 하는 환경변수 전체."""
    _seen = _seen or set()
    if path in _seen:
        return set()
    _seen.add(path)
    need = set(by_file.get(path, ()))
    for dep in imports.get(path, ()):
        need |= required_env(dep, by_file, imports, _seen)
    return need


def build():
    mapping, wf_env, wf_scripts = scan_workflows()
    reads, by_file, imports = scan_code()

    injected = set(mapping)
    used = set(reads)

    # 워크플로우가 실제로 실행하는 스크립트 집합
    executed = set()
    for scripts in wf_scripts.values():
        for sc in scripts:
            executed.add(sc)
            executed |= imports.get(sc, set())

    # 어떤 워크플로우도 주입하지 않는데 코드가 읽는 변수
    missing_all = sorted(used - injected)
    # 실행되는 스크립트가 읽는 경우만 실제 장애 (= 치명적)
    missing = [v for v in missing_all if any(f in executed for f in reads[v])]
    # 실행 안 되는 모듈이 읽는 경우는 참고 정보
    dormant = [v for v in missing_all if v not in missing]
    # 주입은 되는데 아무 코드도 안 읽는 변수
    orphan = sorted(injected - used)
    # 한 환경변수에 서로 다른 시크릿이 매핑된 경우 (사고 원인)
    ambiguous = sorted(v for v, s in mapping.items() if len(s) > 1)

    # 워크플로우가 실행하는 스크립트에 필요한 키를 실제로 주입하는지
    gaps = {}
    for wf, scripts in wf_scripts.items():
        need = set()
        for sc in scripts:
            need |= required_env(sc, by_file, imports)
        short = sorted(need - wf_env.get(wf, set()))
        if short:
            gaps[wf] = short

    L = []
    L.append('# 시크릿 / 환경변수 감사 결과')
    L.append('')
    L.append('> ⚠️ **이 파일은 `scripts/audit_secrets.py`가 생성한다. 직접 편집하지 말 것.**')
    L.append('> 워크플로우나 코드를 바꾼 뒤 `python scripts/audit_secrets.py`를 실행해 갱신한다.')
    L.append('')

    # --- 이상 징후 먼저 ---
    L.append('## 🚨 점검 결과')
    L.append('')
    if not (missing or orphan or ambiguous or gaps or dormant):
        L.append('이상 없음. 주입된 환경변수와 코드가 읽는 환경변수가 모두 일치한다.')
    if gaps:
        L.append('### 워크플로우 주입 부족 (가장 위험)')
        L.append('해당 워크플로우가 실행하는 스크립트가 필요로 하는 키인데 `env:`에 없다.')
        L.append('')
        L.append('| 워크플로우 | 빠진 환경변수 |')
        L.append('|---|---|')
        for wf in sorted(gaps):
            L.append(f'| `{wf}` | {", ".join(f"`{v}`" for v in gaps[wf])} |')
        L.append('')
    if missing:
        L.append('### 주입 누락 (코드는 읽는데 워크플로우가 안 넘김)')
        L.append('런타임에 `None`이 되어 조용히 실패할 수 있다.')
        L.append('')
        L.append('| 환경변수 | 읽는 파일 |')
        L.append('|---|---|')
        for v in missing:
            L.append(f'| `{v}` | {", ".join(f"`{p}`" for p in reads[v])} |')
        L.append('')
    if dormant:
        L.append('### 미실행 모듈이 읽는 환경변수 (참고)')
        L.append('아직 어떤 워크플로우에서도 실행되지 않는 코드다. 지금은 장애가 아니지만,')
        L.append('스케줄에 편입할 때 반드시 `env:`에 추가해야 한다.')
        L.append('')
        L.append('| 환경변수 | 읽는 파일 |')
        L.append('|---|---|')
        for v in dormant:
            L.append(f'| `{v}` | {", ".join(f"`{p}`" for p in reads[v])} |')
        L.append('')
    if orphan:
        L.append('### 고아 시크릿 (주입은 하는데 아무도 안 읽음)')
        L.append('삭제 대상 후보. 또는 코드에서 이름을 잘못 읽고 있을 수 있다.')
        L.append('')
        L.append('| 환경변수 | 주입 시크릿 | 주입 워크플로우 |')
        L.append('|---|---|---|')
        for v in orphan:
            wfs = sorted(f for f, vs in wf_env.items() if v in vs)
            L.append(f'| `{v}` | {", ".join(f"`{s}`" for s in sorted(mapping[v]))} | {", ".join(f"`{w}`" for w in wfs)} |')
        L.append('')
    if ambiguous:
        L.append('### 모호한 매핑 (같은 환경변수에 서로 다른 시크릿)')
        L.append('워크플로우마다 다른 키가 들어간다. 의도한 것이 아니면 사고다.')
        L.append('')
        L.append('| 환경변수 | 매핑된 시크릿들 |')
        L.append('|---|---|')
        for v in ambiguous:
            L.append(f'| `{v}` | {", ".join(f"`{s}`" for s in sorted(mapping[v]))} |')
        L.append('')

    # --- 정식 매핑표 ---
    L.append('---')
    L.append('')
    L.append('## 매핑표 (GitHub Secret → 환경변수 → 사용 파일)')
    L.append('')
    L.append('| GitHub Secret | 코드가 읽는 이름 | 사용 파일 |')
    L.append('|---|---|---|')
    for var in sorted(injected | used):
        secrets = ', '.join(f'`{s}`' for s in sorted(mapping.get(var, []))) or '— (미주입)'
        files = ', '.join(f'`{p}`' for p in reads.get(var, [])) or '— (미사용)'
        L.append(f'| {secrets} | `{var}` | {files} |')
    L.append('')

    # --- 워크플로우별 ---
    L.append('---')
    L.append('')
    L.append('## 워크플로우별 주입 환경변수')
    L.append('')
    L.append('| 워크플로우 | 실행 스크립트 | 주입 환경변수 |')
    L.append('|---|---|---|')
    for wf in sorted(set(wf_env) | set(wf_scripts)):
        scripts = ', '.join(f'`{s}`' for s in wf_scripts.get(wf, [])) or '—'
        envs = ', '.join(f'`{v}`' for v in sorted(wf_env.get(wf, []))) or '—'
        L.append(f'| `{wf}` | {scripts} | {envs} |')
    L.append('')

    # dormant / orphan 은 CI를 실패시키지 않는다 (정보성)
    return '\n'.join(L) + '\n', bool(missing or ambiguous or gaps)


def main():
    content, has_problem = build()
    check = '--check' in sys.argv

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    old = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''

    if check:
        if old != content:
            print('docs/SECRETS.md 가 최신이 아니다. python scripts/audit_secrets.py 실행 필요.')
            sys.exit(1)
        if has_problem:
            print('시크릿 매핑 문제 발견. docs/SECRETS.md 참조.')
            sys.exit(1)
        print('OK')
        return

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'생성 완료: docs/SECRETS.md')
    if has_problem:
        print('⚠️ 문제 발견 — 파일 상단 점검 결과 확인')


if __name__ == '__main__':
    main()
