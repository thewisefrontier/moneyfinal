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
    logger.info(f"저장 완료: {filename} ({len(data) if isinstance(data, list) else 1}건)")


def export_rates():
    """금리 데이터 export"""
    rates = supabase_select('rates', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'max_rate.desc'
    })

    # 카테고리별 분류
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
        'order': 'fetched_at.desc'
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
    """기업 공시 알림 export"""
    alerts = supabase_select('corporate_alerts', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'fetched_at.desc',
        'limit': '50'
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


def main():
    logger.info("=== JSON Export 시작 ===")
    export_rates()
    export_market()
    export_briefing()
    export_corporate_alerts()
    export_ipo()
    logger.info("=== JSON Export 완료 ===")


if __name__ == '__main__':
    main()
