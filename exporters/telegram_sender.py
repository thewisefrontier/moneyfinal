"""
텔레그램 봇 자동 발송
- 일일 브리핑 텍스트 + 카드뉴스 이미지 전송
"""
import logging
import os
import sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_select, today_kst

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID', '')
DISCLAIMER = "\n\n⚠️ 본 정보는 투자 참고용이며, 투자 판단 및 손실에 대한 책임은 이용자 본인에게 있습니다."
SITE_URL = "https://moneyfinal.pages.dev"


def send_message(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={
            'chat_id': TELEGRAM_CHANNEL_ID,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }, timeout=15)
        res.raise_for_status()
        logger.info("텔레그램 메시지 전송 완료")
        return True
    except Exception as e:
        logger.error(f"텔레그램 전송 실패: {e}")
        return False


def send_photo(image_path: str, caption: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, 'rb') as f:
            res = requests.post(url, data={
                'chat_id': TELEGRAM_CHANNEL_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }, files={'photo': f}, timeout=30)
        res.raise_for_status()
        logger.info("텔레그램 이미지 전송 완료")
        return True
    except Exception as e:
        logger.error(f"텔레그램 이미지 전송 실패: {e}")
        return False


def main():
    logger.info("=== 텔레그램 발송 시작 ===")
    today = today_kst()

    # 오늘 브리핑 조회
    briefings = supabase_select('daily_briefing', {
        'select': '*',
        'briefing_date': f'eq.{today}',
        'is_published': 'eq.true'
    })

    if not briefings:
        logger.warning("오늘 브리핑 없음")
        return

    briefing = briefings[0]
    headline = briefing.get('headline', '오늘의 금융 브리핑')
    rate_summary = briefing.get('rate_summary', '')
    market_summary = briefing.get('market_summary', '')

    # 메시지 구성
    message = f"""📊 <b>{today} 머니파이널 브리핑</b>

🎯 <b>{headline}</b>

💰 <b>금리 현황</b>
{rate_summary}

📈 <b>시장 현황</b>
{market_summary}

🔗 자세히 보기: {SITE_URL}
{DISCLAIMER}"""

    send_message(message)

    # 카드뉴스 이미지 전송 (있으면)
    image_path = f"/tmp/cardnews_{today}.png"
    if os.path.exists(image_path):
        send_photo(image_path, f"📊 {today} 머니파이널 카드뉴스{DISCLAIMER}")

    logger.info("=== 텔레그램 발송 완료 ===")


if __name__ == '__main__':
    main()
