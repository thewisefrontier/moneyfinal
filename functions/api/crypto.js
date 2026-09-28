// 암호화폐 시세 게이트웨이. 2026-09-04: CoinMarketCap/FMP 계열 ToS가 원본 데이터를
// 별도 API/데이터 서비스로 재배포하는 걸 금지하고 있어(자사 제품에 통합해 보여주는
// 건 허용) crypto_prices 테이블을 public SELECT 없이 잠그고 이 Function으로만 서빙한다.
//
// 두 가지 접근을 허용한다:
//   1) moneyfinal.pages.dev 자신의 페이지(crypto.html)에서 오는 same-origin 요청
//      - 이건 "자사 제품에 통합해서 보여주는" 정상 허용 범위
//   2) X-Api-Key 헤더가 FEED_API_KEY와 일치하는 요청 (뉴스파이널 등 승인된 프로젝트용)
// 그 외(제3자의 임의 스크래핑)는 401로 거부한다.
// 2026-09: Supabase REST -> Cloudflare D1 네이티브 바인딩으로 이전.
export async function onRequestGet(context) {
  const { request, env } = context;

  const origin = request.headers.get('origin') || '';
  const referer = request.headers.get('referer') || '';
  const isSameOrigin = origin.includes('moneyfinal.pages.dev') || referer.includes('moneyfinal.pages.dev');

  const key = request.headers.get('x-api-key');
  const hasValidKey = env.FEED_API_KEY && key === env.FEED_API_KEY;

  if (!isSameOrigin && !hasValidKey) {
    return new Response(JSON.stringify({ error: 'unauthorized' }), {
      status: 401,
      headers: { 'content-type': 'application/json' }
    });
  }

  if (!env.DB) {
    return new Response(JSON.stringify({ error: 'server not configured' }), {
      status: 500,
      headers: { 'content-type': 'application/json' }
    });
  }

  const upstream = await env.DB.prepare('SELECT * FROM crypto_prices ORDER BY market_cap_rank ASC').all();

  if (!upstream.success) {
    return new Response(JSON.stringify({ error: 'upstream query failed' }), {
      status: 502,
      headers: { 'content-type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({ updated_at: new Date().toISOString().slice(0, 10), coins: upstream.results }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
