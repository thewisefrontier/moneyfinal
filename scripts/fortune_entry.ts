// 운세 계산 번들 진입점 — 핫딜월드 순수 TS 계산 코드를 window.Fortune 하나로 노출한다.
// 빌드: node scripts/build_fortune_bundle.mjs  (esbuild는 핫딜월드 node_modules 사용)
import { ZODIAC_SIGNS, getDailyFortune } from '@/lib/dailyFortune';
import { getPeriodFortune } from '@/lib/periodFortune';
import { calculateSaju, interpretSaju, getSajuFlow, getSajuMonthlyFlow, getSajuWeeklyFlow, getSinsal, DAY_MASTER_NICKNAME, stemHanja, branchHanja, stemElement, branchElement } from '@/lib/saju';
import { TAROT_CARDS, drawTarotCard, getCategoryPoint } from '@/lib/tarot';
import { LUCKY_ITEM_THEMES } from '@/lib/luckyItem';


// 핫딜월드 흐름 함수는 "지금(한국 시간)" 기준이라, 다른 해를 보려면 Date.now()를 그 해 7월 1일로 잠시 바꿔 부른다(핫딜월드 코드는 건드리지 않는다).
function inYear<T>(year: number, fn: () => T): T {
  const real = Date.now;
  Date.now = () => Date.UTC(year, 6, 1, 3);
  try { return fn(); } finally { Date.now = real; }
}
const getSajuYearFlow = (dayStem: string, year: number) => inYear(year, () => getSajuFlow(dayStem)[0]);
const getSajuMonthlyFlowOf = (dayStem: string, year: number) => inYear(year, () => getSajuMonthlyFlow(dayStem));

const nowKst = () => new Date(Date.now() + 9 * 60 * 60 * 1000);
// 다음 달(그달 15일)·내년(7월 1일)의 기간 운세 — Date.now()를 잠시 그 시점으로 바꿔 핫딜월드 getPeriodFortune을 그대로 쓴다.
const getPeriodFortuneNext = (period: "month" | "year", key: string) => {
  const k = nowKst(), real = Date.now;
  const t = period === "month" ? Date.UTC(k.getUTCFullYear(), k.getUTCMonth() + 1, 15, 3) : Date.UTC(k.getUTCFullYear() + 1, 6, 1, 3);
  Date.now = () => t;
  try { return getPeriodFortune(period, key); } finally { Date.now = real; }
};

(globalThis as unknown as { Fortune: unknown }).Fortune = {
  ZODIAC_SIGNS,
  getDailyFortune,
  getPeriodFortune,
  getPeriodFortuneNext,
  calculateSaju,
  interpretSaju,
  getSajuFlow,
  getSajuMonthlyFlow,
  getSajuWeeklyFlow,
  getSajuYearFlow,
  getSajuMonthlyFlowOf,
  getSinsal,
  DAY_MASTER_NICKNAME,
  stemHanja,
  branchHanja,
  stemElement,
  branchElement,
  TAROT_CARDS,
  drawTarotCard,
  getCategoryPoint,
  LUCKY_ITEM_THEMES,
};
