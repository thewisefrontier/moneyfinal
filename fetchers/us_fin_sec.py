"""
미국 기업 연간 재무제표 수집기 (SEC EDGAR XBRL companyfacts) -> data/us_fin/*.json

출처: SEC data.sec.gov/api/xbrl/companyfacts (공식 API, 키 불필요, 미국 정부 공공데이터).
  - SEC 공정접근 정책: 초당 10건 이하 + User-Agent 선언 필수 (공식 안내 확인: 2026-10-25) -> 초당 ~6건으로 제한.
  - 종목 풀: datasets/s-and-p-500-companies (ODC-PDDL 데이터, 위키백과 S&P 500 목록 기반) + 기존 추적 종목(FMP 대상 26개).
방식: 10-K의 FY 사실(fact)만 모아 결산일별로 정리. 같은 결산일이 여러 번 공시(재작성)되면 가장 늦게 제출된 값을 쓴다.
XBRL은 시기별로 태그가 바뀌므로(예: 애플 매출 SalesRevenueNet -> Revenues -> RevenueFromContract...) 지표마다 후보 태그
목록을 두고, 같은 결산일에는 앞선 태그를 우선한다. 은행·보험 등은 매출총이익/영업이익 태그가 없어 '-'로 남는다.
참고(방법론): dgunning/edgartools(MIT)의 표준 계정 매핑 접근을 참고했으나 코드는 가져오지 않음.
"""
import csv
import io
import json
import logging
import os
import sys
import time
from datetime import date

import requests

logger = logging.getLogger(__name__)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'us_fin')
UA = {'User-Agent': 'moneyfinal-research overmandol@gmail.com'}
SP500_CSV = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv'
EXTRA = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'JPM', 'V',
         'O', 'MAIN', 'STAG', 'AGNC', 'ARR', 'GAIN', 'GOOD', 'LAND', 'PSEC', 'EPR', 'ORC', 'NLY', 'ADC', 'LTC', 'ABR', 'EFC']
KEEP_YEARS = 12
KEEP_Q = 20  # 분기: 최근 5년
FORMS = ('10-K', '10-K/A', '10-KT')
QFORMS = FORMS + ('10-Q', '10-Q/A')
NONADD = {'sh'}  # 가중평균 주식수는 누계 차분으로 분기값을 만들 수 없음

# 지표 -> (종류, 단위, 후보 태그들)  종류: dur(기간) / inst(시점)
METRICS = {
    'rev': ('dur', 'USD', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                           'RevenueFromContractWithCustomerIncludingAssessedTax', 'SalesRevenueNet', 'SalesRevenueGoodsNet',
                           'RevenuesNetOfInterestExpense', 'RegulatedAndUnregulatedOperatingRevenue', 'GrossInvestmentIncomeOperating']),
    'cogs': ('dur', 'USD', ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfGoodsSold']),
    'gp': ('dur', 'USD', ['GrossProfit']),
    'rd': ('dur', 'USD', ['ResearchAndDevelopmentExpense']),
    'sga': ('dur', 'USD', ['SellingGeneralAndAdministrativeExpense']),
    'op': ('dur', 'USD', ['OperatingIncomeLoss']),
    'int': ('dur', 'USD', ['InterestExpense', 'InterestExpenseDebt']),
    'tax': ('dur', 'USD', ['IncomeTaxExpenseBenefit']),
    'ni': ('dur', 'USD', ['NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic']),
    'eps': ('dur', 'USD/shares', ['EarningsPerShareDiluted', 'EarningsPerShareBasicAndDiluted', 'EarningsPerShareBasic']),
    'sh': ('dur', 'shares', ['WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic']),
    'cash': ('inst', 'USD', ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'Cash']),
    'ar': ('inst', 'USD', ['AccountsReceivableNetCurrent', 'ReceivablesNetCurrent']),
    'inv': ('inst', 'USD', ['InventoryNet']),
    'ca': ('inst', 'USD', ['AssetsCurrent']),
    'ta': ('inst', 'USD', ['Assets']),
    'cl': ('inst', 'USD', ['LiabilitiesCurrent']),
    'tl': ('inst', 'USD', ['Liabilities']),
    'eq': ('inst', 'USD', ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest']),
    'debt': ('inst', 'USD', ['LongTermDebt', 'LongTermDebtNoncurrent']),
    'cfo': ('dur', 'USD', ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations']),
    'cfi': ('dur', 'USD', ['NetCashProvidedByUsedInInvestingActivities', 'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations']),
    'cff': ('dur', 'USD', ['NetCashProvidedByUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations']),
    'capex': ('dur', 'USD', ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets']),
    'da': ('dur', 'USD', ['DepreciationDepletionAndAmortization', 'DepreciationAndAmortization', 'DepreciationAmortizationAndAccretionNet']),
    'div': ('dur', 'USD', ['PaymentsOfDividends', 'PaymentsOfDividendsCommonStock']),
    'buyback': ('dur', 'USD', ['PaymentsForRepurchaseOfCommonStock']),
}


def _days(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def series(ug, kind, unit, concepts):
    """결산일(end) -> 값. 앞선 태그가 우선, 같은 태그·결산일이면 늦게 제출된 값."""
    out = {}
    for c in concepts:
        node = ug.get(c)
        if not node:
            continue
        best = {}
        for x in node['units'].get(unit, []):
            if x.get('form') not in FORMS:
                continue
            if kind == 'dur':
                if 'start' not in x or not 340 <= _days(x['start'], x['end']) <= 390:
                    continue
            elif 'start' in x:
                continue
            e, f = x['end'], x.get('filed', '')
            if e not in best or f > best[e][0]:
                best[e] = (f, x['val'])
        for e, (_, v) in best.items():
            out.setdefault(e, v)
    return out


def qseries(ug, kind, unit, concepts, additive=True):
    """분기 값: 결산일 -> 값. 기간 항목은 단독 3개월 값 > 누계(YTD) 차분 > Q4(연간-3분기 누계).
    현금흐름은 10-Q에 누계만 있어 차분이 필요하고, Q4는 어떤 항목이든 10-K 연간에서 뺀 값이다."""
    out = {}
    for c in concepts:
        node = ug.get(c)
        if not node:
            continue
        facts = [x for x in node['units'].get(unit, []) if x.get('form') in QFORMS]
        if kind == 'inst':
            best = {}
            for x in facts:
                if 'start' in x:
                    continue
                e, f = x['end'], x.get('filed', '')
                if e not in best or f > best[e][0]:
                    best[e] = (f, x['val'])
            for e, (_, v) in best.items():
                out.setdefault(e, v)
            continue
        byse = {}
        for x in facts:
            if 'start' not in x:
                continue
            d = _days(x['start'], x['end'])
            if not (80 <= d <= 100 or 170 <= d <= 200 or 260 <= d <= 290 or 340 <= d <= 390):
                continue
            k, f = (x['start'], x['end']), x.get('filed', '')
            if k not in byse or f > byse[k][0]:
                byse[k] = (f, x['val'])
        res = {}
        for (st, en), (_, v) in byse.items():  # 단독 3개월(또는 Q1 누계)
            if 80 <= _days(st, en) <= 100:
                res[en] = v
        if additive:
            groups = {}
            for (st, en), (_, v) in byse.items():
                groups.setdefault(st, []).append((en, v, _days(st, en)))
            for st, lst in groups.items():
                lst.sort()
                prev_v, prev_d = 0, 0
                for en, v, d in lst:
                    if 80 <= d - prev_d <= 125:  # 직전 누계와 한 분기 차이일 때만
                        res.setdefault(en, v - prev_v)
                        prev_v, prev_d = v, d
        for en, v in res.items():
            out.setdefault(en, v)
    return out


def extract(facts):
    ug = facts.get('facts', {}).get('us-gaap', {})
    ser = {k: series(ug, *spec) for k, spec in METRICS.items()}
    # 부족한 항목 보완
    if not ser['tl'] and ser['ta'] and ser['eq']:
        ser['tl'] = {e: ser['ta'][e] - ser['eq'][e] for e in ser['ta'] if e in ser['eq']}
    if not ser['gp'] and ser['rev'] and ser['cogs']:
        ser['gp'] = {e: ser['rev'][e] - ser['cogs'][e] for e in ser['rev'] if e in ser['cogs']}
    ends = sorted(set(ser['rev']) | set(ser['ni']) | set(ser['ta']))
    # 손익 또는 자산이 있는 결산일만, 최근 N개
    ends = [e for e in ends if e in ser['ni'] or e in ser['rev']][-KEEP_YEARS:]
    if not ends:
        return None
    res = {'e': ends, 'd': {k: [s.get(e) for e in ends] for k, s in ser.items() if any(s.get(e) is not None for e in ends)}}
    qs = {k: qseries(ug, spec[0], spec[1], spec[2], additive=k not in NONADD) for k, spec in METRICS.items()}
    if not qs['tl'] and qs['ta'] and qs['eq']:
        qs['tl'] = {e: qs['ta'][e] - qs['eq'][e] for e in qs['ta'] if e in qs['eq']}
    if not qs['gp'] and qs['rev'] and qs['cogs']:
        qs['gp'] = {e: qs['rev'][e] - qs['cogs'][e] for e in qs['rev'] if e in qs['cogs']}
    qends = [e for e in sorted(set(qs['rev']) | set(qs['ni'])) if e in qs['rev'] or e in qs['ni']][-KEEP_Q:]
    if qends:
        qs['eps'] = {e: round(v, 4) for e, v in qs['eps'].items()}  # 차분 부동소수 오차 제거
        res['q'] = {'e': qends, 'd': {k: [s.get(e) for e in qends] for k, s in qs.items() if any(s.get(e) is not None for e in qends)}}
    return res


def universe():
    rows = {}
    try:
        txt = requests.get(SP500_CSV, timeout=30, headers=UA).text
        for r in csv.DictReader(io.StringIO(txt)):
            rows[r['Symbol'].strip()] = {'n': r['Security'].strip(), 's': r['GICS Sector'].strip(), 'cik': int(r['CIK'])}
    except Exception as e:  # noqa: BLE001
        logger.warning(f'S&P500 목록 실패: {e}')
    tk = requests.get('https://www.sec.gov/files/company_tickers.json', timeout=30, headers=UA).json()
    by_t = {v['ticker']: v for v in tk.values()}
    for t in EXTRA:
        if t not in rows and t in by_t:
            rows[t] = {'n': by_t[t]['title'].title(), 's': '', 'cik': int(by_t[t]['cik_str'])}
    return rows


def main(limit=None, only=None):
    os.makedirs(OUT, exist_ok=True)
    uni = universe()
    items = [(t, v) for t, v in sorted(uni.items()) if (not only or t in only)]
    if limit:
        items = items[:limit]
    logger.info(f'대상 {len(items)}개')
    shards, index, fail = {}, [], 0
    for n, (t, v) in enumerate(items, 1):
        try:
            r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{v['cik']:010d}.json", headers=UA, timeout=60)
            if r.status_code != 200:
                raise RuntimeError(f'HTTP {r.status_code}')
            res = extract(r.json())
        except Exception as e:  # noqa: BLE001
            fail += 1
            logger.warning(f'{t} 실패: {type(e).__name__} {e}')
            res = None
        if res:
            res.update({'n': v['n'], 's': v['s'], 'cik': v['cik']})
            shards.setdefault(t[0].upper(), {})[t] = res
            index.append([t, v['n'], v['s'], res['e'][-1]])
        if n % 50 == 0:
            logger.info(f'  {n}/{len(items)}')
        time.sleep(0.17)  # 초당 약 6건 (SEC 한도 10건 이하)
    if only or limit:  # 부분 실행은 파일을 덮어쓰지 않고 미리보기만
        return shards
    if len(index) < len(items) * 0.8:
        raise SystemExit(f'수집 성공률이 낮아 기존 데이터를 유지합니다 ({len(index)}/{len(items)})')
    for f in os.listdir(OUT):
        if f.endswith('.json'):
            os.remove(os.path.join(OUT, f))
    for k, body in shards.items():
        json.dump(body, open(os.path.join(OUT, f'{k}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'updated_at': date.today().isoformat(), 'count': len(index), 'stocks': index},
              open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    logger.info(f'완료: {len(index)}개 종목, 실패 {fail}')
    return shards


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    main()
