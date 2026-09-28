-- 2026-09-28: 수집기가 없고 행이 0개인 테이블 6개 삭제.
-- stock_dividends/stock_issuance/stock_short: 6/30 상업 이용 불가로 수집기 삭제, ipo_status: 7/8 데이터 소스 없어 export 제거,
-- financial_health/card_news: 채운 적 없음. (0001_init.sql은 이력이라 그대로 둠)
DROP TABLE IF EXISTS card_news;
DROP TABLE IF EXISTS financial_health;
DROP TABLE IF EXISTS ipo_status;
DROP TABLE IF EXISTS stock_dividends;
DROP TABLE IF EXISTS stock_issuance;
DROP TABLE IF EXISTS stock_short;
