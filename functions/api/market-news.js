// 다른 프로젝트(뉴스파이널 등)가 미국 시장 뉴스를 가져가는 전용 게이트웨이.
// market_news 테이블은 public SELECT 정책 없이 잠겨있고, 여기서만 조회해
// 호출자는 X-Api-Key 헤더로만 인증한다.
// 이 파일은 Cloudflare Pages Functions로 자동 라우팅됨: GET /api/market-news
// 2026-09: Supabase REST -> Cloudflare D1 네이티브 바인딩으로 이전.
export async function onRequestGet(context) {
  const { request, env } = context;

  const key = request.headers.get('x-api-key');
  if (!env.FEED_API_KEY || !key || key !== env.FEED_API_KEY) {
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

  const url = new URL(request.url);
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '40', 10) || 40, 100);

  const upstream = await env.DB.prepare(
    'SELECT headline, summary, source, url, category, image_url, published_at FROM market_news ORDER BY published_at DESC LIMIT ?'
  ).bind(limit).all();

  if (!upstream.success) {
    return new Response(JSON.stringify({ error: 'upstream query failed' }), {
      status: 502,
      headers: { 'content-type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({ items: upstream.results, fetched_at: new Date().toISOString() }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
