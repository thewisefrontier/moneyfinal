"""
종목별 AI 요약 리포트 생성기
- 이미 수집된 실제 재무 데이터(국내 corp_finance, 미국 us_company_financials)만
  근거로 Gemini가 짧은 요약을 씀. 투자 추천/매수매도 의견/목표주가는 금지.
- 전 종목이 아니라 재무데이터가 실제로 있는 종목만 생성함 (2026-09-23 기준
  국내 9 + 미국 26개, corp_finance/us_company_financials 갱신 주기인 분기
  1회 실행) - 전종목 생성은 근거 데이터도 없고 API 비용만 낭비.
"""
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select_all, supabase_upsert, now_kst
from processors.gemini_analyzer import call_gemini

logger = logging.getLogger(__name__)


def _eok(won) -> str:
    """원 단위 숫자를 프롬프트에 조/억원 단위로 넣어준다. AI가 답할 때도 이
    단위를 그대로 써서 '333605938000000원'이나 '3,336,059억원'처럼 안
    읽히는 숫자를 안 쓰게 됨 (won.js의 조/억 표기 관례와 동일하게 맞춤).
    PostgREST가 numeric/bigint를 문자열로 내려줄 수 있어 float()로 캐스팅."""
    n = round(float(won or 0) / 1e8)  # 억 단위
    jo, eok = divmod(n, 10000)
    if jo and eok:
        return f"{jo}조{eok}억원"
    if jo:
        return f"{jo}조원"
    return f"{eok}억원"


def _man_usd(v) -> str:
    return f"{round(float(v or 0) / 1e6):,}백만 USD"


def generate_kr_reports() -> int:
    rows = supabase_select_all('corp_finance', {
        'select': 'stock_code,corp_name,fiscal_year,revenue,operating_profit,net_profit,per,pbr,roe,eps',
        'order': 'fetched_at.desc'
    })
    latest = {}
    for r in rows:
        latest.setdefault(r['stock_code'], r)

    results = []
    for code, r in latest.items():
        prompt = f"""아래는 {r['corp_name']}({code})의 {r['fiscal_year']}년 실제 재무 데이터입니다.
이 데이터만 근거로 실적 현황을 3문장 이내로 담백하게 요약하세요.
투자 추천, 매수/매도 의견, 목표주가는 절대 언급하지 마세요.
데이터에 없는 내용은 추가하지 마세요.

매출액: {_eok(r['revenue'])}
영업이익: {_eok(r['operating_profit'])}
순이익: {_eok(r['net_profit'])}
PER: {r['per']}
PBR: {r['pbr']}
ROE: {r['roe']}%
EPS: {r['eps']}원"""
        text = call_gemini(prompt, 300)
        if not text:
            logger.warning(f"{r['corp_name']}: 요약 생성 실패")
            continue
        results.append({
            'code': code,
            'market': 'KR',
            'corp_name': r['corp_name'],
            'report_text': text,
            'based_on': f"{r['fiscal_year']}년 사업보고서",
            'generated_at': now_kst()
        })
        logger.info(f"✅ {r['corp_name']} 요약 생성 완료")

    if results:
        supabase_upsert('stock_ai_reports', results)
    return len(results)


def generate_us_reports() -> int:
    profiles = supabase_select_all('us_company_profile', {'select': 'ticker,name'})
    financials = supabase_select_all('us_company_financials', {
        'select': 'ticker,fiscal_year,period,revenue,net_income,eps',
        'order': 'fiscal_year.desc'
    })
    latest_fin = {}
    for f in financials:
        if f['period'] != 'FY':
            continue
        latest_fin.setdefault(f['ticker'], f)

    results = []
    for p in profiles:
        ticker = p['ticker']
        f = latest_fin.get(ticker)
        if not f:
            continue
        prompt = f"""아래는 {p['name']}({ticker})의 {f['fiscal_year']}년(회계연도) 실제 재무 데이터입니다.
이 데이터만 근거로 실적 현황을 영어가 아닌 한국어로 3문장 이내로 담백하게 요약하세요.
투자 추천, 매수/매도 의견, 목표주가는 절대 언급하지 마세요.
데이터에 없는 내용은 추가하지 마세요.

매출액: {_man_usd(f['revenue'])}
순이익: {_man_usd(f['net_income'])}
EPS: {f['eps']} USD"""
        text = call_gemini(prompt, 300)
        if not text:
            logger.warning(f"{p['name']}: 요약 생성 실패")
            continue
        results.append({
            'code': ticker,
            'market': 'US',
            'corp_name': p['name'],
            'report_text': text,
            'based_on': f"FY{f['fiscal_year']}",
            'generated_at': now_kst()
        })
        logger.info(f"✅ {p['name']} 요약 생성 완료")

    if results:
        supabase_upsert('stock_ai_reports', results)
    return len(results)


def main():
    logger.info("=== 종목별 AI 요약 리포트 생성 시작 ===")
    kr_count = generate_kr_reports()
    us_count = generate_us_reports()
    logger.info(f"=== 종목별 AI 요약 리포트 생성 완료: 국내 {kr_count}건, 미국 {us_count}건 ===")


if __name__ == '__main__':
    main()
