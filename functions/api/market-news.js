// 다른 프로젝트(뉴스파이널 등)가 미국 시장 뉴스를 가져가는 전용 게이트웨이.
// market_news 테이블은 Supabase에 public SELECT 정책이 없어서(RLS 기본 차단),
// 여기서 service_role 키로만 조회하고, 호출자는 X-Api-Key 헤더로만 인증한다.
// 이 파일은 Cloudflare Pages Functions로 자동 라우팅됨: GET /api/market-news
export async function onRequestGet(context) {
  const { request, env } = context;

  const key = request.headers.get('x-api-key');
  if (!env.FEED_API_KEY || !key || key !== env.FEED_API_KEY) {
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

  const url = new URL(request.url);
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '40', 10) || 40, 100);

  const upstream = await fetch(
    `${env.SUPABASE_URL}/rest/v1/market_news?select=headline,summary,source,url,category,image_url,published_at&order=published_at.desc&limit=${limit}`,
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

  const data = await upstream.json();
  return new Response(JSON.stringify({ items: data, fetched_at: new Date().toISOString() }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
