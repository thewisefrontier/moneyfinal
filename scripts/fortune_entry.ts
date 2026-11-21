// 운세 계산 번들 진입점 — 핫딜월드 순수 TS 계산 코드를 window.Fortune 하나로 노출한다.
// 빌드: node scripts/build_fortune_bundle.mjs  (esbuild는 핫딜월드 node_modules 사용)
import { ZODIAC_SIGNS, getDailyFortune } from '@/lib/dailyFortune';
import { getPeriodFortune } from '@/lib/periodFortune';
import { calculateSaju, interpretSaju, getSajuMonthlyFlow, getSinsal, DAY_MASTER_NICKNAME, stemHanja, branchHanja, stemElement, branchElement } from '@/lib/saju';
import { TAROT_CARDS, drawTarotCard, getCategoryPoint } from '@/lib/tarot';
import { LUCKY_ITEM_THEMES } from '@/lib/luckyItem';

(globalThis as unknown as { Fortune: unknown }).Fortune = {
  ZODIAC_SIGNS,
  getDailyFortune,
  getPeriodFortune,
  calculateSaju,
  interpretSaju,
  getSajuMonthlyFlow,
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
