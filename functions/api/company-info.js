// 미국 기업정보(프로필/재무제표/실적/배당/액면분할) 게이트웨이.
// 2026-09-04: FMP ToS가 원본 데이터를 별도 API/데이터 서비스로 재배포하는 걸
// 금지하고 있어(자사 제품 통합 표시는 허용) us_company_* 테이블을 public
// SELECT 없이 잠그고 이 Function으로만 서빙한다. X-Api-Key 필수(뉴스파이널
// 등 승인된 프로젝트용) - moneyfinal 자체에는 아직 이 데이터를 쓰는 화면이
// 없어서 crypto.js와 달리 same-origin 예외를 두지 않았다.
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

  const [profilesRes, financialsRes, earningsRes, dividendsRes, splitsRes] = await Promise.all([
    env.DB.prepare('SELECT * FROM us_company_profile').all(),
    env.DB.prepare('SELECT * FROM us_company_financials ORDER BY fiscal_year DESC').all(),
    env.DB.prepare('SELECT * FROM us_company_earnings ORDER BY report_date DESC').all(),
    env.DB.prepare('SELECT * FROM us_company_dividends ORDER BY ex_date DESC').all(),
    env.DB.prepare('SELECT * FROM us_company_splits ORDER BY split_date DESC').all()
  ]);

  if (!profilesRes.success || !financialsRes.success || !earningsRes.success || !dividendsRes.success || !splitsRes.success) {
    return new Response(JSON.stringify({ error: 'upstream query failed' }), {
      status: 502,
      headers: { 'content-type': 'application/json' }
    });
  }

  const groupBy = (arr) => {
    const out = {};
    for (const r of arr) {
      (out[r.ticker] = out[r.ticker] || []).push(r);
    }
    return out;
  };

  const profiles = {};
  for (const p of profilesRes.results) profiles[p.ticker] = p;

  return new Response(JSON.stringify({
    updated_at: new Date().toISOString().slice(0, 10),
    profiles,
    financials: groupBy(financialsRes.results),
    earnings: groupBy(earningsRes.results),
    dividends: groupBy(dividendsRes.results),
    splits: groupBy(splitsRes.results)
  }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
