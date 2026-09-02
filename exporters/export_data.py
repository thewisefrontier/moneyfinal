"""
DB → JSON export
Cloudflare Pages에서 정적으로 서빙할 JSON 파일 생성
"""
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
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
    """금리 데이터 export (예금/적금/저축은행/CMA/파킹/펀드/실손보험 포함)

    단종 상품 잔존 방지: fetcher는 upsert만 하므로 API에서 사라진(공시 중단된)
    상품이 rates 테이블에 영구 잔존함. 최근 40일 내 재수집된 row만 export하여
    현재 공시 중인 상품만 노출 (월 1회 수집 주기 + 실패 버퍼, loans와 동일).
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    rates = supabase_select_all('rates', {
        'select': '*',
        'fetched_at': f'gte.{cutoff}',
        'order': 'max_rate.desc'
    })

    by_category = {}
    for r in rates:
        cat = r.get('category', '기타')
        by_category.setdefault(cat, []).append(r)

    # top20: 실손보험은 rate/max_rate 단위가 금리(%)가 아닌 공공데이터포털
    # "기준 보험료"(원 단위)라서 예금/적금 금리와 섞어서 순위를 매기면 안 됨.
    # 한도 100만원 미만 소액상품(카드실적 연계 이벤트성 상품 등)은 최고금리만
    # 높고 실제 비교 의미가 없어 TOP 랭킹에서 제외 (전체보기 목록에는 그대로 노출).
    rate_only = [
        r for r in rates
        if r.get('category') != '실손보험'
        and not (r.get('max_limit') and r['max_limit'] < 1_000_000)
    ]

    save_json('rates.json', {
        'updated_at': today_kst(),
        'total': len(rates),
        'by_category': by_category,
        'top20': rate_only[:20]
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


def export_stock_history():
    """market.html 종목 클릭 시 일/월/연도별 드릴다운을 위한 종목별 시세 히스토리.
    전체 상장종목(수천개)을 다 내보내면 용량이 너무 커지므로, 현재 화면에
    실제 표시되는 시가총액 상위 종목만 대상으로 전체 기간 히스토리를 담는다."""
    history = {}
    for market, top_n in [('KOSPI', 30), ('KOSDAQ', 30), ('US', 15)]:
        latest = supabase_select('stock_prices', {
            'select': 'stock_code',
            'market_type': f'eq.{market}',
            'order': 'base_date.desc,market_cap.desc',
            'limit': '200'
        })
        codes = []
        for r in latest:
            code = r.get('stock_code')
            if code and code not in codes:
                codes.append(code)
            if len(codes) >= top_n:
                break
        if not codes:
            continue
        rows = supabase_select_all('stock_prices', {
            'select': 'stock_code,base_date,close_price,flt_rt,volume,market_cap',
            'market_type': f'eq.{market}',
            'stock_code': f'in.({",".join(codes)})',
            'order': 'base_date.asc'
        })
        for r in rows:
            history.setdefault(r['stock_code'], []).append(r)
    save_json('stock_history.json', {
        'updated_at': today_kst(),
        'history': history
    })


INDICATOR_HISTORY_CODES = [
    'USD_KRW', 'BASE_RATE', 'FED_RATE', 'M2_TOTAL', 'HOUSEHOLD_CREDIT',
    'KOSPI', 'KOSDAQ', 'KOSPI200', 'USD_INDEX', 'US_SP500', 'US_DJIA', 'US_NASDAQ',
    'US_CPI', 'US_YIELD_CURVE', 'VIX', 'WTI', 'GOLD',
]


def export_indicator_history():
    """index.html/market.html KPI 클릭 시 일/월/연도별 드릴다운을 위한 지표별 히스토리.
    market_indicators 테이블은 macro.html 은행통계 등까지 포함해 1700여개 코드를
    담고 있어 전체를 내보내면 너무 크므로, 실제 홈/시장 화면에 노출되는
    코드만 화이트리스트로 골라 전체 기간 히스토리를 담는다."""
    history = {}
    for code in INDICATOR_HISTORY_CODES:
        rows = supabase_select_all('market_indicators', {
            'select': 'indicator_code,indicator_name,reference_date,value,unit',
            'indicator_code': f'eq.{code}',
            'order': 'reference_date.asc'
        })
        if rows:
            history[code] = rows
    save_json('indicator_history.json', {
        'updated_at': today_kst(),
        'history': history
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


def export_loans():
    """대출상품 export (주담대/전세/신용/사업자)

    월 1회(매월 21일) 수집이므로 40일 cutoff (월간 주기 + 실패 버퍼).
    단종 상품 잔존 방지 목적은 export_rates()와 동일.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    common = {'select': '*', 'fetched_at': f'gte.{cutoff}'}

    mortgage = supabase_select_all('mortgage_loans', {**common, 'order': 'lend_rate_min.asc'})
    rent = supabase_select_all('rent_loans', {**common, 'order': 'lend_rate_min.asc'})
    credit = supabase_select_all('credit_loans', {**common, 'order': 'crdt_grad_avg.asc'})
    business = supabase_select_all('business_loans', {**common, 'order': 'lend_rate_min.asc'})

    save_json('loans.json', {
        'updated_at': today_kst(),
        'total': len(mortgage) + len(rent) + len(credit) + len(business),
        'mortgage': mortgage,
        'rent': rent,
        'credit': credit,
        'business': business
    })


def export_annuity():
    """연금저축 export"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    annuity = supabase_select_all('annuity_savings', {
        'select': '*',
        'fetched_at': f'gte.{cutoff}',
        'order': 'avg_prft_rate.desc'
    })
    save_json('annuity.json', {
        'updated_at': today_kst(),
        'total': len(annuity),
        'annuity': annuity
    })


def export_dividends():
    """ETF/종목 배당금 이력 + 실시간 시세 + 프로필 export (배당금 계산기 페이지용)

    셋 다 로테이션/일일 수집이라 fetched_at cutoff를 두지 않고 보유분을
    그대로 내보낸다 (오래된 티커도 다음 순번에 갱신됨).
    """
    rows = supabase_select_all('etf_dividends', {
        'select': 'ticker,ex_dividend_date,declaration_date,record_date,payment_date,amount,fetched_at',
        'order': 'ex_dividend_date.desc'
    })
    by_ticker = {}
    for r in rows:
        by_ticker.setdefault(r['ticker'], []).append(r)

    price_rows = supabase_select_all('stock_prices', {
        'select': 'stock_code,close_price,vs,flt_rt,base_date,fetched_at',
        'market_type': 'eq.ETF',
        'order': 'fetched_at.desc'
    })
    prices = {}
    for r in price_rows:
        code = r['stock_code']
        if code not in prices:
            prices[code] = {
                'price': r['close_price'], 'change': r['vs'], 'change_pct': r['flt_rt'],
                'base_date': r['base_date']
            }

    profile_rows = supabase_select_all('etf_profiles', {
        'select': 'ticker,net_assets,expense_ratio,dividend_yield,inception_date,sectors,top_holdings,fetched_at'
    })
    profiles = {r['ticker']: r for r in profile_rows}

    save_json('dividends.json', {
        'updated_at': today_kst(),
        'by_ticker': by_ticker,
        'prices': prices,
        'profiles': profiles
    })


def export_kr_dividends():
    """국내 상장 배당 ETF 분배금 이력 + 시세 export (국내 배당ETF 계산기 페이지용)"""
    rows = supabase_select_all('kr_etf_dividends', {
        'select': 'ticker,ex_dividend_date,amount,fetched_at',
        'order': 'ex_dividend_date.desc'
    })
    by_ticker = {}
    for r in rows:
        by_ticker.setdefault(r['ticker'], []).append(r)

    price_rows = supabase_select_all('kr_etf_prices', {'select': '*'})
    prices = {r['ticker']: r for r in price_rows}

    save_json('kr_dividends.json', {
        'updated_at': today_kst(),
        'by_ticker': by_ticker,
        'prices': prices
    })


def export_us_company_info():
    """미국 기업정보(프로필/재무제표/실적/배당/액면분할) export

    대형주 10종은 FMP로 5종 데이터 전부, 리츠·BDC 16종은 프로필만 FMP,
    나머지는 yfinance로 보완 수집됨(fetchers/us_company_info.py 참고).
    공개 데이터라 별도 인증 없이 다른 프로젝트에서도 그대로 fetch 가능.
    """
    profiles = {r['ticker']: r for r in supabase_select_all('us_company_profile', {'select': '*'})}

    financials_by_ticker = {}
    for r in supabase_select_all('us_company_financials', {'select': '*', 'order': 'fiscal_year.desc'}):
        financials_by_ticker.setdefault(r['ticker'], []).append(r)

    earnings_by_ticker = {}
    for r in supabase_select_all('us_company_earnings', {'select': '*', 'order': 'report_date.desc'}):
        earnings_by_ticker.setdefault(r['ticker'], []).append(r)

    dividends_by_ticker = {}
    for r in supabase_select_all('us_company_dividends', {'select': '*', 'order': 'ex_date.desc'}):
        dividends_by_ticker.setdefault(r['ticker'], []).append(r)

    splits_by_ticker = {}
    for r in supabase_select_all('us_company_splits', {'select': '*', 'order': 'split_date.desc'}):
        splits_by_ticker.setdefault(r['ticker'], []).append(r)

    save_json('us_company_info.json', {
        'updated_at': today_kst(),
        'profiles': profiles,
        'financials': financials_by_ticker,
        'earnings': earnings_by_ticker,
        'dividends': dividends_by_ticker,
        'splits': splits_by_ticker
    })


def main():
    logger.info("=== JSON Export 시작 ===")
    export_rates()
    export_market()
    export_briefing()
    export_corporate_alerts()
    export_stocks()
    export_stock_history()
    export_indicator_history()
    export_corp_finance()
    export_loans()
    export_annuity()
    export_dividends()
    export_kr_dividends()
    export_us_company_info()
    logger.info("=== JSON Export 완료 ===")


if __name__ == '__main__':
    main()
