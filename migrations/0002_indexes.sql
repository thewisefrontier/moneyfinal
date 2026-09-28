-- 2026-09-28: 조회 패턴 점검 결과 추가한 인덱스 (전체 스캔 제거 목적)
-- market_news: functions/api/market-news.js가 ORDER BY published_at DESC LIMIT ?를 요청마다 실행
-- (market_indicators(indicator_code, fetched_at)는 실측에서 플래너가 안 써서 뺐음.
--  export를 "지표코드별 최신 1건" 쿼리로 바꿀 때 다시 검토)
CREATE INDEX IF NOT EXISTS idx_market_news_published ON market_news(published_at);
