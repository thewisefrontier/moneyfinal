"""
Gemini AI 정제 및 일일 브리핑 생성기
- 수집된 데이터를 분석하여 브리핑 텍스트 생성
- 투자 권유 표현 자동 필터링
- 면책 문구 자동 삽입
"""
import logging
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, supabase_upsert, now_kst, today_kst
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

DISCLAIMER = "본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다. 출처: 공공기관 공시 데이터"

SYSTEM_PROMPT = """
당신은 대한민국 금융 데이터 분석 AI입니다.
다음 규칙을 반드시 지켜주세요:

1. 팩트만 서술하고 투자 추천/매매 권유 표현 절대 금지
   - 금지: "매수하세요", "투자하세요", "오를 것입니다", "추천합니다"
   - 허용: "~로 나타났습니다", "~를 기록했습니다", "~수준입니다"

2. 모든 수치는 출처 명시

3. 문체: 간결하고 객관적인 뉴스 문체

4. 한국어로 작성

5. 면책 문구는 별도로 처리하므로 본문에 포함 불필요
"""


def call_gemini(prompt: str, max_tokens: int = 500) -> str:
    """Gemini API 호출 (10초 간격 유지)"""
    try:
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\n" + prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
            )
        )
        time.sleep(10)  # RPM 안전 간격
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini 호출 오류: {e}")
        time.sleep(15)
        return ""


def generate_rate_summary(rates: list) -> str:
    """금리 데이터 요약 생성"""
    if not rates:
        return "금리 데이터 수집 중입니다."

    # 상위 5개 최고금리 상품
    top_rates = sorted(rates, key=lambda x: x.get('max_rate', 0), reverse=True)[:5]
    rate_text = "\n".join([
        f"- {r['institution']} {r['product_name']}: 기본 {r['rate']}% / 최고 {r.get('max_rate', r['rate'])}% ({r.get('period', '')})"
        for r in top_rates
    ])

    prompt = f"""
다음은 오늘 수집된 금융권 금리 데이터입니다.
핵심 내용을 3문장 이내로 요약해주세요.

[금리 TOP5]
{rate_text}
"""
    return call_gemini(prompt, max_tokens=200)


def generate_market_summary(indicators: list) -> str:
    """거시지표 요약 생성"""
    if not indicators:
        return "시장 지표 수집 중입니다."

    indicator_text = "\n".join([
        f"- {i['indicator_name']}: {i['value']} {i.get('unit', '')} (신호: {i.get('signal', 'green')})"
        for i in indicators
    ])

    prompt = f"""
다음은 오늘 수집된 거시경제 지표입니다.
주요 변화와 시장 현황을 3문장 이내로 객관적으로 요약해주세요.

[거시지표]
{indicator_text}
"""
    return call_gemini(prompt, max_tokens=200)


def generate_headline(rate_summary: str, market_summary: str) -> str:
    """오늘의 헤드라인 생성"""
    prompt = f"""
다음 금융 요약을 바탕으로 오늘의 헤드라인을 20자 이내로 작성해주세요.
투자 권유 표현 없이 팩트 중심으로.

금리 요약: {rate_summary[:100]}
시장 요약: {market_summary[:100]}
"""
    return call_gemini(prompt, max_tokens=50)


def generate_cardnews_copy(rate_summary: str, market_summary: str) -> dict:
    """카드뉴스용 JSON 카피 생성"""
    prompt = f"""
다음 데이터를 바탕으로 카드뉴스 텍스트를 JSON 형식으로 작성해주세요.
각 카드는 제목(title)과 내용(content)으로 구성됩니다.
총 4장의 카드뉴스입니다.

금리 현황: {rate_summary}
시장 현황: {market_summary}

JSON 형식:
{{
  "cards": [
    {{"title": "카드1 제목", "content": "카드1 내용"}},
    {{"title": "카드2 제목", "content": "카드2 내용"}},
    {{"title": "카드3 제목", "content": "카드3 내용"}},
    {{"title": "카드4 제목 (면책)", "content": "본 정보는 투자 참고용입니다."}}
  ]
}}
"""
    result = call_gemini(prompt, max_tokens=500)

    # JSON 파싱
    import json
    import re
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.error(f"카드뉴스 JSON 파싱 오류: {e}")

    return {"cards": [{"title": "오늘의 금융 브리핑", "content": rate_summary}]}


def main():
    logger.info("=== Gemini 분석 시작 ===")
    today = today_kst()

    # 오늘 데이터 조회
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

    # AI 요약 생성
    rate_summary = generate_rate_summary(rates)
    logger.info(f"금리 요약 생성 완료")

    market_summary = generate_market_summary(indicators)
    logger.info(f"시장 요약 생성 완료")

    headline = generate_headline(rate_summary, market_summary)
    logger.info(f"헤드라인: {headline}")

    cardnews_json = generate_cardnews_copy(rate_summary, market_summary)
    logger.info(f"카드뉴스 카피 생성 완료")

    # daily_briefing 저장
    briefing = {
        'briefing_date': today,
        'headline': headline,
        'rate_summary': rate_summary,
        'market_summary': market_summary,
        'full_text': f"{rate_summary}\n\n{market_summary}",
        'is_published': True
    }
    supabase_upsert('daily_briefing', [briefing])

    # card_news 저장
    import json
    card_news = {
        'title': headline,
        'category': '종합',
        'content_json': cardnews_json,
        'disclaimer': DISCLAIMER,
        'published_at': now_kst()
    }
    supabase_upsert('card_news', [card_news])

    logger.info("=== Gemini 분석 완료 ===")


if __name__ == '__main__':
    main()
