"""
Gemini AI 정제 및 일일 브리핑 생성기
- google-genai 새 SDK 사용
- 모델: gemini-3.1-flash-lite
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

DISCLAIMER = "본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다."

SYSTEM_PROMPT = """당신은 대한민국 금융 데이터 분석 AI입니다.
규칙:
1. 팩트만 서술, 투자 추천/매매 권유 절대 금지
2. 모든 수치는 출처 명시
3. 간결하고 객관적인 뉴스 문체
4. 한국어로 작성"""


def call_gemini(prompt: str, max_tokens: int = 300) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=SYSTEM_PROMPT + "\n\n" + prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
            )
        )
        time.sleep(10)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini 호출 오류: {e}")
        time.sleep(15)
        return ""


def generate_rate_summary(rates: list) -> str:
    if not rates:
        return "금리 데이터 수집 중입니다."
    top = sorted(rates, key=lambda x: x.get('max_rate', 0), reverse=True)[:5]
    rate_text = "\n".join([
        f"- {r['institution']} {r['product_name']}: 최고 {r.get('max_rate', r['rate'])}% ({r.get('period','')})"
        for r in top
    ])
    return call_gemini(f"다음 금리 TOP5를 3문장 이내로 요약하세요. 마크다운 기호 사용 금지:\n{rate_text}", 200)


def generate_market_summary(indicators: list) -> str:
    if not indicators:
        return "시장 지표 수집 중입니다."
    text = "\n".join([
        f"- {i['indicator_name']}: {i['value']} {i.get('unit','')} (신호: {i.get('signal','green')})"
        for i in indicators
    ])
    return call_gemini(f"다음 거시지표를 3문장 이내로 객관적으로 요약하세요. 마크다운 기호 사용 금지:\n{text}", 200)


def generate_headline(rate_summary: str, market_summary: str) -> str:
    return call_gemini(
        f"""오늘의 금융 헤드라인을 작성하세요.
규칙:
- 반드시 20자 이내
- 마크다운 기호 절대 금지 (**, [], # 등)
- 투자 권유 없이 팩트만
- 헤드라인 텍스트만 출력 (설명 없이)

금리: {rate_summary[:100]}
시장: {market_summary[:100]}""",
        30
    )


def main():
    logger.info("=== Gemini 분석 시작 ===")
    today = today_kst()

    rates = supabase_select('rates', {
        'select': '*',
        'is_published': 'eq.true',
        'order': 'max_rate.desc',
        'limit': '20'
    })
    indicators = supabase_select('market_indicators', {
        'select': '*',
        'order': 'fetched_at.desc',
        'limit': '10'
    })
    logger.info(f"금리 {len(rates)}건, 지표 {len(indicators)}건 조회")

    rate_summary = generate_rate_summary(rates)
    market_summary = generate_market_summary(indicators)
    headline = generate_headline(rate_summary, market_summary)
    logger.info(f"헤드라인: {headline}")

    briefing = {
        'briefing_date': today,
        'headline': headline,
        'rate_summary': rate_summary,
        'market_summary': market_summary,
        'full_text': f"{rate_summary}\n\n{market_summary}",
        'is_published': True
    }
    supabase_upsert('daily_briefing', [briefing])
    logger.info("=== Gemini 분석 완료 ===")


if __name__ == '__main__':
    main()
