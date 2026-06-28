"""
DB → JSON export
Cloudflare Pages에서 정적으로 서빙할 JSON 파일 생성
"""
import json
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, today_kst

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def save_json(filename: str, data: any):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    count = len(data) if isinstance(data, list) else 1
    logger.info(f"저장 완료: {filename} ({count}건)")


def export_rates():
    """금리 데이터 export"""
    # Supabase REST API: order 형식은 'column.desc' 또는 'column.asc'
    rates = supabase_select('rates', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'max_rate.desc',
        'limit': '2000'
    })

    by_category = {}
    for r in rates:
        cat = r.get('category', '기타')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)

    save_json('rates.json', {
        'updated_at': today_kst(),
        'total': len(rates),
        'by_category': by_category,
        'top20': rates[:20]
    })


def export_market():
    """거시지표 export"""
    indicators = supabase_select('market_indicators', {
        'select': '*',
        'order': 'fetched_at.desc',
        'limit': '100'
    })

    # 지표별 최신값만
    latest = {}
    for i in indicators:
        code = i.get('indicator_code')
        if code not in latest:
            latest[code] = i

    save_json('market.json', {
        'updated_at': today_kst(),
        'indicators': list(latest.values())
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
    """기업 공시 알림 export - needs_review=false인 것만"""
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
    """주식 시세 export - 시가총액 상위 50"""
    # KOSPI 상위 25 + KOSDAQ 상위 25
    kospi = supabase_select('stock_prices', {
        'select': '*',
        'market_type': 'eq.KOSPI',
        'order': 'market_cap.desc',
        'limit': '25'
    })
    kosdaq = supabase_select('stock_prices', {
        'select': '*',
        'market_type': 'eq.KOSDAQ',
        'order': 'market_cap.desc',
        'limit': '25'
    })
    # 최신 날짜만
    all_stocks = kospi + kosdaq
    save_json('stocks.json', {
        'updated_at': today_kst(),
        'kospi': kospi,
        'kosdaq': kosdaq,
        'total': len(all_stocks)
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


def main():
    logger.info("=== JSON Export 시작 ===")
    export_rates()
    export_market()
    export_briefing()
    export_corporate_alerts()
    export_ipo()
    export_stocks()
    export_corp_finance()
    logger.info("=== JSON Export 완료 ===")


if __name__ == '__main__':
    main()
