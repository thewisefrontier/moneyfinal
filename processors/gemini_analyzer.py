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

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = 'gemini-3.1-flash-lite'

DISCLAIMER = "본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다. 출처: 공공기관 공시 데이터"

SYSTEM_PROMPT = """당신은 금융 데이터 분석 AI입니다.

엄격한 규칙:
1. 반드시 제공된 데이터 수치만 사용하세요. 데이터에 없는 내용을 추측하거나 생성하지 마세요.
2. 모든 수치는 제공된 데이터에서 그대로 인용하세요.
3. 투자 추천, 매매 권유, 수익 보장 표현 절대 금지.
4. 마크다운 기호(**, ##, [] 등) 사용 금지.
5. 데이터가 부족하면 "데이터 수집 중"이라고만 하세요.
6. 한국어로 간결하게 작성하세요."""


def call_gemini(prompt: str, max_tokens: int = 300) -> str:
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
        150
    )


def analyze_market(indicators: list) -> str:
    if not indicators:
        return "시장 지표 수집 중"
    data_text = "\n".join([
        f"- {i['indicator_name']}: {i['value']} {i.get('unit', '')} (출처: {i.get('source', '')})"
        for i in indicators
    ])
    return call_gemini(
        f"""아래는 오늘 수집된 실제 거시경제 지표 데이터입니다.
이 수치들만을 바탕으로 현황을 2-3문장으로 객관적으로 설명하세요.
데이터에 없는 내용, 전망, 예측은 절대 추가하지 마세요.

[수집된 거시지표 데이터]
{data_text}""",
        150
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


def main():
    logger.info("=== Gemini 데이터 분석 시작 ===")
    today = today_kst()

    rates = supabase_select('rates', {
        'select': '*',
        'order': 'max_rate.desc',
        'limit': '10'
    })
    indicators = supabase_select('market_indicators', {
        'select': '*',
        'order': 'fetched_at.desc',
        'limit': '10'
    })

    logger.info(f"금리 {len(rates)}건, 지표 {len(indicators)}건 조회")

    if not rates and not indicators:
        logger.warning("분석할 데이터 없음. 종료.")
        return

    rate_analysis = analyze_rates(rates)
    logger.info("금리 분석 완료")

    market_analysis = analyze_market(indicators)
    logger.info("시장 분석 완료")

    overall_signal = generate_signal(indicators)

    briefing = {
        'briefing_date': today,
        'headline': f"{today} 금융 데이터 현황",
        'rate_summary': rate_analysis,
        'market_summary': market_analysis,
        'full_text': f"{rate_analysis}\n\n{market_analysis}\n\n{DISCLAIMER}",
        'is_published': True
    }
    supabase_upsert('daily_briefing', [briefing])
    logger.info(f"분석 완료 - 종합 신호: {overall_signal}")
    logger.info("=== Gemini 데이터 분석 완료 ===")


if __name__ == '__main__':
    main()
