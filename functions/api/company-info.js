// 미국 기업정보(프로필/재무제표/실적/배당/액면분할) 게이트웨이.
// 2026-09-04: FMP ToS가 원본 데이터를 별도 API/데이터 서비스로 재배포하는 걸
// 금지하고 있어(자사 제품 통합 표시는 허용) us_company_* 테이블을 public
// SELECT 없이 잠그고 이 Function으로만 서빙한다. X-Api-Key 필수(뉴스파이널
// 등 승인된 프로젝트용) - moneyfinal 자체에는 아직 이 데이터를 쓰는 화면이
// 없어서 crypto.js와 달리 same-origin 예외를 두지 않았다.
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

  const headers = {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`
  };
  const base = `${env.SUPABASE_URL}/rest/v1`;

  const [profilesRes, financialsRes, earningsRes, dividendsRes, splitsRes] = await Promise.all([
    fetch(`${base}/us_company_profile?select=*`, { headers }),
    fetch(`${base}/us_company_financials?select=*&order=fiscal_year.desc`, { headers }),
    fetch(`${base}/us_company_earnings?select=*&order=report_date.desc`, { headers }),
    fetch(`${base}/us_company_dividends?select=*&order=ex_date.desc`, { headers }),
    fetch(`${base}/us_company_splits?select=*&order=split_date.desc`, { headers })
  ]);

  if (!profilesRes.ok || !financialsRes.ok || !earningsRes.ok || !dividendsRes.ok || !splitsRes.ok) {
    return new Response(JSON.stringify({ error: 'upstream fetch failed' }), {
      status: 502,
      headers: { 'content-type': 'application/json' }
    });
  }

  const [profilesArr, financialsArr, earningsArr, dividendsArr, splitsArr] = await Promise.all([
    profilesRes.json(), financialsRes.json(), earningsRes.json(), dividendsRes.json(), splitsRes.json()
  ]);

  const groupBy = (arr) => {
    const out = {};
    for (const r of arr) {
      (out[r.ticker] = out[r.ticker] || []).push(r);
    }
    return out;
  };

  const profiles = {};
  for (const p of profilesArr) profiles[p.ticker] = p;

  return new Response(JSON.stringify({
    updated_at: new Date().toISOString().slice(0, 10),
    profiles,
    financials: groupBy(financialsArr),
    earnings: groupBy(earningsArr),
    dividends: groupBy(dividendsArr),
    splits: groupBy(splitsArr)
  }), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'private, no-store' }
  });
}
