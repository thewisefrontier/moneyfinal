"""
DB → JSON export
Cloudflare Pages에서 정적으로 서빙할 JSON 파일 생성
"""
import json
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, supabase_select_all, today_kst

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def save_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    count = len(data) if isinstance(data, list) else 1
    logger.info(f"저장 완료: {filename} ({count}건)")


def export_rates():
    """금리 데이터 export (예금/적금/저축은행/CMA/파킹/펀드/실손보험 포함)"""
    rates = supabase_select_all('rates', {
        'select': '*',
        'order': 'max_rate.desc'
    })

    by_category = {}
    for r in rates:
        cat = r.get('category', '기타')
        by_category.setdefault(cat, []).append(r)

    save_json('rates.json', {
        'updated_at': today_kst(),
        'total': len(rates),
        'by_category': by_category,
        'top20': rates[:20]
    })


def export_market():
    """거시지표 export (채권/ISA/KOFIA/ECOS/FRED/KRX 포함)"""
    # 전체 히스토리 조회 후 코드별 최신값 dedupe
    # (limit 500 방식은 저빈도 지표(BASE_RATE 등)가 최근 N행 밖으로 밀려 누락되는 문제 있음)
    indicators = supabase_select_all('market_indicators', {
        'select': '*',
        'order': 'fetched_at.desc'
    })

    # 지표 코드별 최신값만 유지 (fetched_at.desc 정렬이므로 첫 등장이 최신)
    latest = {}
    for i in indicators:
        code = i.get('indicator_code')
        if code and code not in latest:
            latest[code] = i

    by_category = {}
    for i in latest.values():
        cat = i.get('category', '기타')
        by_category.setdefault(cat, []).append(i)

    save_json('market.json', {
        'updated_at': today_kst(),
        'indicators': list(latest.values()),
        'by_category': by_category
    })


def export_briefing():
    """일일 브리핑 export"""
    briefing = supabase_select('daily_briefing', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'briefing_date.desc',
        'limit': '7'
    })
    save_json('briefing.json', {
        'updated_at': today_kst(),
        'briefings': briefing
    })


def export_corporate_alerts():
    """기업 공시 알림 export"""
    alerts = supabase_select('corporate_alerts', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'fetched_at.desc',
        'limit': '100'
    })
    save_json('alerts.json', {
        'updated_at': today_kst(),
        'alerts': alerts
    })


def export_ipo():
    """IPO 현황 export"""
    ipo = supabase_select('ipo_status', {
        'select': '*',
        'order': 'fetched_at.desc',
        'limit': '50'
    })
    save_json('ipo.json', {
        'updated_at': today_kst(),
        'ipo_list': ipo
    })


def export_stocks():
    """주식 시세 export - 시가총액 상위 (KOSPI/KOSDAQ/US)"""
    # base_date.desc 우선: 히스토리가 쌓여도 최신일 행이 항상 limit 안에 포함됨
    # (종목별 최신일 dedupe + 상위 N개 slice는 프론트에서 처리)
    kospi = supabase_select('stock_prices', {
        'select': '*',
        'market_type': 'eq.KOSPI',
        'order': 'base_date.desc,market_cap.desc',
        'limit': '100'
    })
    kosdaq = supabase_select('stock_prices', {
        'select': '*',
        'market_type': 'eq.KOSDAQ',
        'order': 'base_date.desc,market_cap.desc',
        'limit': '100'
    })
    us = supabase_select('stock_prices', {
        'select': '*',
        'market_type': 'eq.US',
        'order': 'base_date.desc,market_cap.desc',
        'limit': '50'
    })
    save_json('stocks.json', {
        'updated_at': today_kst(),
        'kospi': kospi,
        'kosdaq': kosdaq,
        'us': us,
        'total': len(kospi) + len(kosdaq) + len(us)
    })


def export_corp_finance():
    """기업 재무정보 export"""
    finance = supabase_select('corp_finance', {
        'select': 'stock_code,corp_name,fiscal_year,revenue,operating_profit,net_profit,per,pbr,roe,eps',
        'order': 'fetched_at.desc',
        'limit': '50'
    })
    save_json('corp_finance.json', {
        'updated_at': today_kst(),
        'companies': finance
    })


def export_dividends():
    """주식 배당 정보 export"""
    dividends = supabase_select('stock_dividends', {
        'select': '*',
        'order': 'dps.desc',
        'limit': '100'
    })
    save_json('dividends.json', {
        'updated_at': today_kst(),
        'total': len(dividends),
        'dividends': dividends
    })


def export_short_selling():
    """공매도(대차) 정보 export - 잔고 상위"""
    short_data = supabase_select('stock_short', {
        'select': '*',
        'order': 'short_amount.desc',
        'limit': '100'
    })
    save_json('short_selling.json', {
        'updated_at': today_kst(),
        'total': len(short_data),
        'short_list': short_data
    })


def main():
    logger.info("=== JSON Export 시작 ===")
    export_rates()
    export_market()
    export_briefing()
    export_corporate_alerts()
    export_ipo()
    export_stocks()
    export_corp_finance()
    export_dividends()
    export_short_selling()
    logger.info("=== JSON Export 완료 ===")


if __name__ == '__main__':
    main()
