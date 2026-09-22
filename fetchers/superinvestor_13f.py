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
    {"cik": "0000949509", "investor_name": "Howard Marks", "fund_name": "Oaktree Capital Management"},
    {"cik": "0001167483", "investor_name": "Chase Coleman", "fund_name": "Tiger Global Management"},
    {"cik": "0001345471", "investor_name": "Nelson Peltz", "fund_name": "Trian Fund Management"},
    {"cik": "0000915191", "investor_name": "Prem Watsa", "fund_name": "Fairfax Financial Holdings"},
    {"cik": "0001056831", "investor_name": "Bruce Berkowitz", "fund_name": "Fairholme Capital Management"},
    {"cik": "0001553733", "investor_name": "Glenn Greenberg", "fund_name": "Brave Warrior Advisors"},
    {"cik": "0001096343", "investor_name": "Tom Gayner", "fund_name": "Markel Group"},
    {"cik": "0001135778", "investor_name": "Bill Miller", "fund_name": "Miller Value Partners"},
    {"cik": "0001040273", "investor_name": "Daniel Loeb", "fund_name": "Third Point"},
    {"cik": "0001103804", "investor_name": "Andreas Halvorsen", "fund_name": "Viking Global Investors"},
    {"cik": "0001061165", "investor_name": "Stephen Mandel", "fund_name": "Lone Pine Capital"},

    # 초분산 멀티전략/퀀트/기관 운용사 - 종목 수가 수백~수천 개라 위 집중투자형
    # 목록과 같이 컨센서스(겹치는 투자자 수)에 넣으면 신호가 희석되고, Citadel은
    # 실제로 보유종목이 너무 많아 삭제 쿼리가 URL 길이 초과로 실패하기도 했음
    # (supabase_delete_not_in을 청크 삭제 방식으로 고쳐서 지금은 문제없음).
    # 컨센서스 집계에선 빼고, 개별 투자자 조회에서만 보여줌 (investor_type 구분).
    {"cik": "0001350694", "investor_name": "Bridgewater Associates", "fund_name": "Bridgewater Associates", "investor_type": "institutional"},
    {"cik": "0001423053", "investor_name": "Citadel Advisors", "fund_name": "Citadel Advisors", "investor_type": "institutional"},
    {"cik": "0001608046", "investor_name": "국민연금공단", "fund_name": "National Pension Service", "investor_type": "institutional"},
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
                "investor_type": inv.get("investor_type", "concentrated"),
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
