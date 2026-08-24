"""
Gemini AI 데이터 분석기
- 수집된 공공데이터만을 기반으로 분석
- 할루시네이션 방지: 입력 데이터 외 내용 생성 금지
- 출처 명시된 수치만 활용
"""
import logging
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, supabase_upsert, now_kst, today_kst
from google import genai
import datetime as _dt
import pytz
import holidays as _hd

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = 'gemini-3.1-flash-lite'

DISCLAIMER = "본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다. 출처: 공공기관 공시 데이터"

# 브리핑에 사용할 핵심 거시지표 (fetched_at.desc limit 방식은 최근 수집 파이프라인에 따라
# 무관한 지표(예: 해외파생 종목)만 들어가는 문제가 있어 코드 지정 방식으로 변경)
KEY_INDICATOR_CODES = [
    'BASE_RATE', 'FED_RATE', 'USD_KRW', 'USD_INDEX', 'M2_TOTAL',
    'KOSPI', 'KOSDAQ', 'KOSPI200', 'VIX', 'WTI', 'GOLD', 'US_YIELD_CURVE', 'US_CPI',
    'US_SP500', 'US_DJIA', 'US_NASDAQ'
]

# 시장 브리핑에 포함할 시가총액 상위 종목 수
TOP_STOCKS = [('KOSPI', 5), ('KOSDAQ', 3), ('US', 5)]
TOP_STOCKS_KR_CLOSED = [('US', 5)]  # 한국 증시 휴장일: 미국 종목만


def is_kr_market_closed() -> bool:
    """한국 증시 휴장 여부 (주말 + 공휴일 + KRX 전용 휴장일)"""
    kst = _dt.datetime.now(pytz.timezone('Asia/Seoul')).date()
    if kst.weekday() >= 5:  # 토/일
        return True
    if kst in _hd.KR(years=kst.year):  # 공휴일 (대체공휴일 포함)
        return True
    if (kst.month, kst.day) in ((5, 1), (12, 31)):  # 근로자의날, 연말 휴장
        return True
    return False

SYSTEM_PROMPT = """당신은 금융 데이터 분석 AI입니다.

엄격한 규칙:
1. 반드시 제공된 데이터 수치만 사용하세요. 데이터에 없는 내용을 추측하거나 생성하지 마세요.
2. 모든 수치는 제공된 데이터에서 그대로 인용하세요.
3. 투자 추천, 매매 권유, 수익 보장 표현 절대 금지.
4. 마크다운 기호(**, ##, [] 등) 사용 금지.
5. 데이터가 부족하면 "데이터 수집 중"이라고만 하세요.
6. 한국어로 간결하게 작성하세요."""


def call_gemini(prompt: str, max_tokens: int = 500) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=SYSTEM_PROMPT + "\n\n" + prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.1,
            )
        )
        time.sleep(10)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini 호출 오류: {type(e).__name__} - {e}")
        time.sleep(15)
        return ""


def analyze_rates(rates: list) -> str:
    if not rates:
        return "금리 데이터 수집 중"
    top5 = sorted(rates, key=lambda x: x.get('max_rate') or x.get('rate', 0), reverse=True)[:5]
    data_text = "\n".join([
        f"- {r['institution']} {r['product_name']}: 기본금리 {r['rate']}%, 최고금리 {r.get('max_rate', r['rate'])}%, 기간 {r.get('period', '')}"
        for r in top5
    ])
    return call_gemini(
        f"""아래는 오늘 수집된 실제 금융상품 금리 데이터입니다.
이 데이터만을 바탕으로 현황을 2-3문장으로 설명하세요.
데이터에 없는 내용은 절대 추가하지 마세요.

[수집된 금리 데이터 TOP5]
{data_text}""",
        400
    )


def analyze_market(indicators: list, stocks_by_market: list, kr_closed: bool = False) -> str:
    if not indicators and not stocks_by_market:
        return "시장 지표 수집 중"
    ind_text = "\n".join([
        f"- {i['indicator_name']}: {i['value']} {i.get('unit', '')} (출처: {i.get('source', '')})"
        for i in indicators
    ])
    stock_lines = []
    for market, stocks in stocks_by_market:
        unit = 'USD' if market == 'US' else '원'
        for s in stocks:
            chg = s.get('flt_rt')
            chg_txt = f", 등락률 {chg}%" if chg is not None else ""
            stock_lines.append(f"- [{market}] {s.get('stock_name')}: 종가 {s.get('close_price')}{unit}{chg_txt}")
    stock_text = "\n".join(stock_lines)
    if kr_closed:
        instruction = """오늘은 주말 또는 공휴일로 한국 증시(코스피/코스닥)가 휴장입니다.
해외 지수(S&P 500, 다우존스, 나스닥, VIX)와 환율, 원자재를 중심으로 설명하고, 이어서 미국 종목의 종가와 등락률을 언급하세요.
코스피/코스닥 수치는 직전 거래일 종가임을 명시하여 한 문장으로만 간단히 언급하세요."""
    else:
        instruction = "지수와 거시지표를 먼저 언급하고, 이어서 시가총액 상위 종목의 종가와 등락률을 언급하세요."
    return call_gemini(
        f"""아래는 오늘 수집된 실제 시장 데이터입니다.
이 수치들만을 바탕으로 현황을 4-5문장으로 객관적으로 설명하세요.
{instruction}
데이터에 없는 내용, 전망, 예측은 절대 추가하지 마세요.

[수집된 거시지표 데이터]
{ind_text}

[시가총액 상위 종목]
{stock_text}""",
        500
    )


def generate_signal(indicators: list) -> str:
    if not indicators:
        return "green"
    red_count = sum(1 for i in indicators if i.get('signal') == 'red')
    yellow_count = sum(1 for i in indicators if i.get('signal') == 'yellow')
    if red_count >= 2:
        return 'red'
    elif red_count >= 1 or yellow_count >= 2:
        return 'yellow'
    return 'green'


def get_key_indicators() -> list:
    """핵심 지표 코드별 최신값 조회"""
    rows = supabase_select('market_indicators', {
        'select': '*',
        'indicator_code': f"in.({','.join(KEY_INDICATOR_CODES)})",
        'order': 'fetched_at.desc',
        'limit': '200'
    })
    latest = {}
    for r in rows:
        code = r.get('indicator_code')
        if code and code not in latest:
            latest[code] = r
    return list(latest.values())


def get_top_stocks(markets: list = None) -> list:
    """시장별 시가총액 상위 종목 조회 (종목별 최신일 dedupe)"""
    out = []
    for market, n in (markets or TOP_STOCKS):
        rows = supabase_select('stock_prices', {
            'select': 'stock_code,stock_name,close_price,flt_rt,market_cap,base_date',
            'market_type': f'eq.{market}',
            'order': 'base_date.desc,market_cap.desc',
            'limit': '60'
        })
        latest = {}
        for r in rows:
            code = r.get('stock_code')
            if code and code not in latest:
                latest[code] = r
        top = sorted(latest.values(), key=lambda x: x.get('market_cap') or 0, reverse=True)[:n]
        out.append((market, top))
    return out


def main():
    logger.info("=== Gemini 데이터 분석 시작 ===")
    today = today_kst()
    time_str = now_kst()[11:16]  # ISO 포맷(YYYY-MM-DDTHH:MM:SS+09:00)에서 HH:MM만 추출

    # 실손보험(category='실손보험')은 rate/max_rate 컬럼에 금리(%)가 아닌
    # 공공데이터포털 "기준 보험료"(원 단위 수치)가 들어있어 예금/적금과 단위가 다르다.
    # 함께 정렬하면 보험료 수치가 금리로 오인되어 "15193.5%" 같은 오류 문구가 생성되므로
    # 실제 금리(%) 상품인 예금/적금만 대상으로 한다.
    rates = supabase_select('rates', {
        'select': '*',
        'category': 'in.(예금,적금)',
        'order': 'max_rate.desc',
        'limit': '10'
    })
    kr_closed = is_kr_market_closed()
    if kr_closed:
        logger.info("한국 증시 휴장일 - 해외 증시 중심 브리핑")

    indicators = get_key_indicators()
    top_stocks = get_top_stocks(TOP_STOCKS_KR_CLOSED if kr_closed else None)

    stock_count = sum(len(s) for _, s in top_stocks)
    logger.info(f"금리 {len(rates)}건, 지표 {len(indicators)}건, 종목 {stock_count}건 조회")

    if not rates and not indicators:
        logger.warning("분석할 데이터 없음. 종료.")
        return

    rate_analysis = analyze_rates(rates)
    logger.info("금리 분석 완료")

    market_analysis = analyze_market(indicators, top_stocks, kr_closed)
    logger.info("시장 분석 완료")

    overall_signal = generate_signal(indicators)

    briefing = {
        'briefing_date': today,
        'headline': f"{today} {time_str} 기준 금융 데이터 현황",
        'rate_summary': rate_analysis,
        'market_summary': market_analysis,
        'full_text': f"{market_analysis}\n\n{rate_analysis}\n\n{DISCLAIMER}",
        'is_published': True
    }
    supabase_upsert('daily_briefing', [briefing])
    logger.info(f"분석 완료 - 종합 신호: {overall_signal}")
    logger.info("=== Gemini 데이터 분석 완료 ===")


if __name__ == '__main__':
    main()
