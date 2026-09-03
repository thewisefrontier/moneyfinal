"""
로컬 PC에서 하루 한 번 실행하는 공공데이터(data.go.kr) 전용 갱신 스크립트.

배경: GitHub Actions 러너 -> apis.data.go.kr 구간이 2026-09-03부터 사실상
전면 차단 상태(제3자 네트워크에서는 정상 응답하는데 러너에서만 ConnectTimeout
100%). 아래 목록은 data.go.kr 외 대체 소스가 없는(있어도 검증 안 된) 데이터라
GitHub Actions 자동화로는 갱신이 안 됨 - 사용자 PC(정상 연결)에서 이 스크립트를
하루 한 번 돌려서 대신 채운다.

사용법:
  1. .env 파일에 DATA_GO_KR_API_KEY / SUPABASE_URL / SUPABASE_KEY가 채워져
     있는지 확인 (D:\\thewise\\moneyfinal\\.env)
  2. python scripts/local_daily_update.py 실행
     (또는 local_daily_update.bat 더블클릭)

한 작업이 실패해도 나머지는 계속 진행한다. 끝나면 성공/실패 요약을 보여준다.
"""
import os
import sys
import time
import traceback
import importlib

# Windows 콘솔 기본 인코딩(cp949)이 이모지(✅❌⚠️)를 못 그려서 print()가 그 자체로
# UnicodeEncodeError로 죽는 걸 방지 (2026-09-04 실측: 백필 성공 직후 이 print 하나
# 때문에 뒤 작업 11개가 전혀 안 돌고 스크립트가 통째로 죽었음).
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def load_env():
    """utils/common.py 등 fetcher들은 python-dotenv를 안 쓰고 순수
    os.environ만 읽으므로, 이 스크립트가 .env를 직접 파싱해서 주입한다."""
    env_path = os.path.join(ROOT, '.env')
    if not os.path.exists(env_path):
        print(f"⚠️ .env 파일이 없습니다: {env_path}")
        return
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value


load_env()

REQUIRED = ['DATA_GO_KR_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    print(f"❌ .env에 다음 값이 비어있습니다: {', '.join(missing)}")
    print(r"   D:\thewise\moneyfinal\.env 파일을 열어서 채워주세요.")
    sys.exit(1)

# (모듈명, 설명) - data.go.kr 전용, 검증된 대체 소스 없는 것들
TASKS = [
    ('fetchers.bank_stats', '국내은행 통계'),
    ('fetchers.corp_finance', '기업 재무/기본정보'),
    ('fetchers.derivatives_info', '파생상품 지수'),
    ('fetchers.disclosure_alerts', '기업 중요공시 알림'),
    ('fetchers.fdi_stats', 'FDI 외국인직접투자'),
    ('fetchers.financial_corp_info', '금융회사 기본정보'),
    ('fetchers.fund_info', '펀드 상품 기본정보'),
    ('fetchers.governance_info', '금융회사 지배구조정보'),
    ('fetchers.insurance_info', '실손보험정보'),
    ('fetchers.isa_info', 'ISA 다모아정보'),
    ('fetchers.kofia_stats', '금융투자협회 종합통계'),
]


def run_module_task(module_name: str, desc: str) -> bool:
    print(f"\n{'=' * 60}\n▶ {desc} ({module_name})\n{'=' * 60}")
    try:
        mod = importlib.import_module(module_name)
        mod.main()
        print(f"✅ {desc} 완료")
        return True
    except Exception as e:
        print(f"❌ {desc} 실패: {type(e).__name__} - {e}")
        traceback.print_exc()
        return False


def run_stock_backfill_task() -> bool:
    """국내주식은 GitHub Actions에서 Yahoo Finance(상위 100종목)로 대체됐지만,
    data.go.kr은 전종목을 주는 유일한 소스라 로컬에서 주기적으로 전종목 갱신."""
    desc = '국내주식 전종목 시세 (data.go.kr, 최근 10일)'
    print(f"\n{'=' * 60}\n▶ {desc}\n{'=' * 60}")
    try:
        from fetchers.stock_prices import run_backfill
        run_backfill(days=10)
        print(f"✅ {desc} 완료")
        return True
    except Exception as e:
        print(f"❌ {desc} 실패: {type(e).__name__} - {e}")
        traceback.print_exc()
        return False


def main():
    print(f"머니파이널 로컬 공공데이터 갱신 시작 ({len(TASKS) + 1}개 작업)")
    print("GitHub Actions에서 막혀있는 apis.data.go.kr 전용 데이터를 이 PC에서 대신 갱신합니다.")

    ok, fail = 0, 0
    if run_stock_backfill_task():
        ok += 1
    else:
        fail += 1
    time.sleep(1)

    for module_name, desc in TASKS:
        if run_module_task(module_name, desc):
            ok += 1
        else:
            fail += 1
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"완료: 성공 {ok}건 / 실패 {fail}건")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
