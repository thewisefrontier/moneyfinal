// 암호화폐 시세 게이트웨이. 2026-09-04: CoinMarketCap/FMP 계열 ToS가 원본 데이터를
// 별도 API/데이터 서비스로 재배포하는 걸 금지하고 있어(자사 제품에 통합해 보여주는
// 건 허용) crypto_prices 테이블을 public SELECT 없이 잠그고 이 Function으로만 서빙한다.
//
// 두 가지 접근을 허용한다:
//   1) moneyfinal.pages.dev 자신의 페이지(crypto.html)에서 오는 same-origin 요청
//      - 이건 "자사 제품에 통합해서 보여주는" 정상 허용 범위
//   2) X-Api-Key 헤더가 FEED_API_KEY와 일치하는 요청 (뉴스파이널 등 승인된 프로젝트용)
// 그 외(제3자의 임의 스크래핑)는 401로 거부한다.
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

  if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) {
    return new Response(JSON.stringify({ error: 'server not configured' }), {
      status: 500,
      headers: { 'content-type': 'application/json' }
    });
  }

  const upstream = await fetch(
    `${env.SUPABASE_URL}/rest/v1/crypto_prices?select=*&order=market_cap_rank.asc`,
    {
      headers: {
        apikey: env.SUPABASE_SERVICE_ROLE_KEY,
        Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`
      }
    }
  );

  if (!upstream.ok) {
    return new Response(JSON.stringify({ error: 'upstream fetch failed', status: upstream.status }), {
      status: 502,
      headers: { 'content-type': 'application/json' }
    });
  }

  const coins = await upstream.json();
  return new Response(JSON.stringify({ updated_at: new Date().toISOString().slice(0, 10), coins }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
