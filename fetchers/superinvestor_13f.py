"""
13F 기반 슈퍼인베스터 컨센서스 - SEC EDGAR 공시 수집기
출처: SEC EDGAR, edgartools(https://github.com/dgunning/edgartools) 라이브러리로 조회.
미국 정부 공공데이터라 재배포 제한 없음.

13F는 분기 공시라 분기 종료 후 최대 45일 지연이 있음 (실시간 보유 현황이
아니라 "최대 4.5개월 전 스냅샷"). "슈퍼인베스터" 명단은 SEC 데이터가 판별해
주는 게 아니라 널리 알려진 트랙레코드를 기준으로 직접 고른 것 (2026-09-22).

2026-09-22: 처음엔 requests+xml.etree로 직접 파싱했는데(보유내역 XML
파일명이 filer마다 제각각이라 "primary_doc.xml이 아닌 .xml 파일"로 추측해야
했음), SEC 공시 포맷이 바뀌면 유지보수가 계속 필요할 거라 판단해 이 용도로
특화된 edgartools로 교체함. Ticker 심볼도 덤으로 받아짐.
"""
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_delete_not_in, now_kst
from edgar import set_identity, Company

logger = logging.getLogger(__name__)

set_identity("moneyfinal-research overmandol@gmail.com")

# CIK는 2026-09-22에 SEC EDGAR 전체 텍스트 검색으로 직접 확인함(하드코딩된
# 이름만으로 CIK를 추측하면 조용히 엉뚱한/빈 데이터를 가져오는 filer가 섞여
# 있어서 - 예: Mohnish Pabrai는 2012년 이후 13F-HR을 안 내서 명단에서 뺌).
SUPERINVESTORS = [
    {"cik": "0001067983", "investor_name": "Warren Buffett", "fund_name": "Berkshire Hathaway"},
    {"cik": "0001336528", "investor_name": "Bill Ackman", "fund_name": "Pershing Square Capital Management"},
    {"cik": "0001649339", "investor_name": "Michael Burry", "fund_name": "Scion Asset Management"},
    {"cik": "0000921669", "investor_name": "Carl Icahn", "fund_name": "Icahn Enterprises"},
    {"cik": "0001061768", "investor_name": "Seth Klarman", "fund_name": "Baupost Group"},
    {"cik": "0001536411", "investor_name": "Stanley Druckenmiller", "fund_name": "Duquesne Family Office"},
    {"cik": "0001079114", "investor_name": "David Einhorn", "fund_name": "Greenlight Capital"},
    {"cik": "0001656456", "investor_name": "David Tepper", "fund_name": "Appaloosa"},
    {"cik": "0001709323", "investor_name": "Li Lu", "fund_name": "Himalaya Capital Management"},
]


def fetch_holdings(cik: str):
    """(DataFrame, report_period) 또는 (None, None). get_filings(form='13F-HR')가
    이미 13F-NT(별도 filer에 위임)는 걸러줌 - latest()는 진짜 최신 보유내역 공시."""
    try:
        filings = Company(cik).get_filings(form="13F-HR")
        latest = filings.latest()
        if latest is None:
            return None, None
        obj = latest.obj()
        return obj.holdings, str(obj.report_period)
    except Exception as e:
        logger.warning(f"조회 실패 (CIK {cik}): {type(e).__name__} - {e}")
        return None, None


def main():
    logger.info("=== 13F 슈퍼인베스터 컨센서스 수집 시작 ===")
    for inv in SUPERINVESTORS:
        df, period = fetch_holdings(inv["cik"])
        if df is None or df.empty:
            logger.warning(f"{inv['investor_name']}: 최근 13F-HR 없음")
            continue

        # 같은 종목이 하위 매니저별로 여러 행에 나뉘어 나올 수 있어 cusip 기준 합산
        agg = {}
        for _, row in df.iterrows():
            cusip = row.get("Cusip")
            if not cusip:
                continue
            value = float(row.get("Value") or 0)
            shares = int(row.get("SharesPrnAmount") or 0)
            if cusip in agg:
                agg[cusip]["value"] += value
                agg[cusip]["shares"] += shares
            else:
                agg[cusip] = {
                    "name_of_issuer": row.get("Issuer") or cusip,
                    "ticker": row.get("Ticker") or None,
                    "value": value,
                    "shares": shares,
                }

        total_value = sum(a["value"] for a in agg.values())
        rows = [
            {
                "investor_name": inv["investor_name"],
                "fund_name": inv["fund_name"],
                "cik": inv["cik"],
                "cusip": cusip,
                "name_of_issuer": a["name_of_issuer"],
                "ticker": a["ticker"],
                "value_usd": a["value"],
                "shares": a["shares"],
                "weight_pct": round(a["value"] / total_value * 100, 4) if total_value else 0,
                "period_of_report": period,
                "source": "SEC EDGAR 13F",
                "fetched_at": now_kst(),
            }
            for cusip, a in agg.items()
        ]
        supabase_upsert("superinvestor_holdings", rows)
        # 이번 분기 팔아치운 종목이 예전 분기 행으로 영구히 남지 않도록 정리
        supabase_delete_not_in(
            "superinvestor_holdings", "cusip",
            [r["cusip"] for r in rows],
            extra_eq={"investor_name": inv["investor_name"]},
        )
        logger.info(f"✅ {inv['investor_name']} ({period}): {len(rows)}종목")

    logger.info("=== 13F 슈퍼인베스터 컨센서스 수집 완료 ===")


if __name__ == "__main__":
    main()
